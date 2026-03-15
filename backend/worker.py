import asyncio
import uuid
from typing import List
from database import get_db
from engine import verify_single_email
from config import settings
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

async def _process_batch(job_id: str, emails_chunk: List[str]):
    # Process a chunk of emails concurrently using asyncio.gather
    tasks = []
    for email in emails_chunk:
        tasks.append(verify_single_email(email))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Write back to DB
    db = get_db()
    
    # To efficiently write back, we use executemany
    records = []
    for email, result in zip(emails_chunk, results):
        result_id = str(uuid.uuid4())
        if isinstance(result, Exception):
            logger.error(f"Error checking email {email}: {result}")
            records.append((
                result_id, job_id, email, email.split('@')[1] if '@' in email else None,
                'invalid', False, False, str(result)
            ))
        else:
            records.append((
                result_id, job_id, email, result.get('domain'),
                result.get('status'), result.get('is_role'),
                result.get('is_disposable'), result.get('smtp_result')
            ))
            
    # Write results
    db.executemany("""
    INSERT INTO verification_results 
    (id, job_id, email, domain, status, is_role, is_disposable, smtp_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    # Update job progress
    db.execute("""
    UPDATE verification_jobs 
    SET processed_emails = processed_emails + ? 
    WHERE id = ?
    """, [len(records), job_id])


class RateLimiter:
    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.updated_at
            self.tokens = min(self.rate, self.tokens + time_passed * (self.rate / self.per))
            self.updated_at = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / (self.rate / self.per)
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.updated_at = time.monotonic()
            else:
                self.tokens -= 1

global_limiter = RateLimiter(100, 60)
domain_semaphores = defaultdict(lambda: asyncio.Semaphore(5))

async def background_worker(job_id: str, email_list: List[str]):
    try:
        db = get_db()
        # Update status to processing
        db.execute("UPDATE verification_jobs SET status = 'processing' WHERE id = ?", [job_id])
        
        total = len(email_list)
        logger.info(f"[Job {job_id}] 🚀 Started — {total:,} emails to verify")
        
        # Group emails by domain for logging
        domain_counts = defaultdict(int)
        for email in email_list:
            if '@' in email:
                domain_counts[email.split('@')[1].lower()] += 1
        unique_domains = len(domain_counts)
        logger.info(f"[Job {job_id}] 📊 Found {unique_domains:,} unique domains")
        
        processed_count = 0
        stats = defaultdict(int)
        
        async def bounded_process(email):
            nonlocal processed_count
            if '@' in email:
                domain = email.split('@')[1].lower()
            else:
                domain = "invalid"
                
            # Global rate limit: 100/minute
            await global_limiter.acquire()
            
            # Domain limit: 5 concurrent connections
            async with domain_semaphores[domain]:
                res = await verify_single_email(email)
                
                processed_count += 1
                status = res.get('status', 'unknown')
                stats[status] += 1
                
                # Log individual results
                icon_map = {
                    'valid': '✅',
                    'invalid': '❌',
                    'disposable': '🗑️',
                    'catch_all': '📬',
                    'role_based': '👥',
                    'unknown': '❓',
                }
                icon = icon_map.get(status, '•')
                
                smtp_info = res.get('smtp_result', '')
                logger.info(f"[Job {job_id}] {icon} {email} → {status.upper()} ({smtp_info})")
                
                # Log progress milestones
                if processed_count % 50 == 0 or processed_count == total:
                    pct = round(processed_count / total * 100, 1)
                    logger.info(f"[Job {job_id}] 📈 Progress: {processed_count:,}/{total:,} ({pct}%)")
                
                return email, res

        # Create all tasks
        tasks = [bounded_process(email) for email in email_list]
        
        # We can chunk them so we don't hold thousands of items in memory for DB insert
        chunk_size = 500
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (len(tasks) + chunk_size - 1) // chunk_size
            
            logger.info(f"[Job {job_id}] ⚡ Processing DB batch {chunk_num}/{total_chunks}...")
            results = await asyncio.gather(*chunk, return_exceptions=True)
            
            records = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"[Job {job_id}] 💥 Error: {str(result)}")
                    continue
                email, res = result
                
                result_id = str(uuid.uuid4())
                records.append((
                    result_id, job_id, email, res.get('domain'),
                    res.get('status'), res.get('is_role'),
                    res.get('is_disposable'), res.get('smtp_result')
                ))
            
            if records:
                db.executemany("""
                INSERT INTO verification_results 
                (id, job_id, email, domain, status, is_role, is_disposable, smtp_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
                
                db.execute("""
                UPDATE verification_jobs 
                SET processed_emails = processed_emails + ? 
                WHERE id = ?
                """, [len(records), job_id])

        # Job complete - log summary
        db.execute("UPDATE verification_jobs SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?", [job_id])
        
        summary_parts = [f"{status}: {count}" for status, count in sorted(stats.items())]
        logger.info(f"[Job {job_id}] 🎉 Job completed! Results: {', '.join(summary_parts)}")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] failed: {e}")
        db = get_db()
        db.execute("UPDATE verification_jobs SET status = 'failed' WHERE id = ?", [job_id])
