import asyncio
import uuid
from typing import List
from database import get_db, get_db_write_lock
from engine import verify_single_email
from config import settings
import logging
import time
from collections import defaultdict, deque
from dns_checks import prefetch_domain_types

logger = logging.getLogger(__name__)

_result_buffer: deque = deque()

async def _buffer_result(result: dict, db):
    _result_buffer.append(result)
    if len(_result_buffer) >= 10:
        await _flush_result_buffer(db)

async def _flush_result_buffer(db):
    if not _result_buffer:
        return
    async with get_db_write_lock():
        batch = []
        while _result_buffer:
            batch.append(_result_buffer.popleft())
        if batch:
            try:
                records = [
                    (
                        r.get("id", str(uuid.uuid4())),
                        r.get("job_id"),
                        r.get("email"),
                        r.get("domain"),
                        r.get("status", "unknown"),
                        bool(r.get("is_role", False)),
                        bool(r.get("is_disposable", False)),
                        str(r.get("smtp_result", ""))
                    )
                    for r in batch
                ]
                db.executemany(
                    "INSERT OR REPLACE INTO verification_results "
                    "(id, job_id, email, domain, status, is_role, is_disposable, smtp_result) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    records
                )
            except Exception as e:
                logger.error(f"Failed to flush verification results buffer: {e}")

async def bulk_cache_lookup(emails: list[str], db) -> dict[str, dict]:
    placeholders = ", ".join(["?" for _ in emails])
    rows = db.execute(
        f"SELECT email, status, confidence FROM email_cache "
        f"WHERE email IN ({placeholders}) "
        f"AND (epoch(CURRENT_TIMESTAMP) - epoch(verified_at)) < {settings.EMAIL_CACHE_TTL}",
        emails
    ).fetchall()
    return {row[0]: {"status": row[1], "score": row[2], "from_cache": True} for row in rows}

async def _staggered_gather(email_list: list, verify_fn, delay_secs: float) -> list:
    tasks = []
    for email in email_list:
        if delay_secs > 0:
            await asyncio.sleep(delay_secs)
        tasks.append(asyncio.create_task(verify_fn(email)))
    return await asyncio.gather(*tasks, return_exceptions=True)

_global_semaphore = asyncio.Semaphore(settings.GLOBAL_MAX_CONCURRENT)
_active_job_tasks: dict[str, asyncio.Task] = {}
_cancelled_job_ids: set[str] = set()

def cancel_running_job(job_id: str) -> bool:
    """Mark job as cancelled and terminate running asyncio task if active."""
    _cancelled_job_ids.add(job_id)
    if job_id in _active_job_tasks:
        task = _active_job_tasks[job_id]
        if not task.done():
            task.cancel()
        return True
    return False

async def background_worker(job_id: str, email_list: List[str]):
    current_task = asyncio.current_task()
    if current_task:
        _active_job_tasks[job_id] = current_task

    try:
        db = get_db()
        # Update status to processing
        db.execute("UPDATE verification_jobs SET status = 'processing' WHERE id = ?", [job_id])
        
        total = len(email_list)
        logger.info(f"[Job {job_id}] 🚀 Started — {total:,} emails to verify")
        
        user_row = db.execute(
            "SELECT tier FROM users WHERE id = (SELECT user_id FROM verification_jobs WHERE id = ?)", [job_id]
        ).fetchone()
        user_tier = user_row[0] if user_row else "standard"

        TIER_RATE_MAP = {
            "free":       settings.RATE_TIER_FREE,
            "standard":   settings.RATE_TIER_STANDARD,
            "power":      settings.RATE_TIER_POWER,
            "enterprise": settings.RATE_TIER_ENTERPRISE,
        }
        job_rate = TIER_RATE_MAP.get(user_tier, settings.RATE_TIER_STANDARD)
        job_delay = 60.0 / job_rate
        job_semaphore = asyncio.Semaphore(max(1, job_rate // 10))

        logger.info(f"[Job {job_id}] 🎯 Job rate: {job_rate}/min (tier: {user_tier})")
        
        # Bulk cache lookup
        cache_lookup_results = await bulk_cache_lookup(email_list, db)
        cache_hits = []
        emails_to_verify = []
        for em in email_list:
            if em in cache_lookup_results:
                cache_hits.append((em, cache_lookup_results[em]))
            else:
                emails_to_verify.append(em)

        logger.info(f"[Job {job_id}] 📦 Cache: {len(cache_hits)} hits, {len(emails_to_verify)} need verification")
        
        unique_domains = list({email.split('@')[1].lower() for email in emails_to_verify if '@' in email})
        domain_type_map = await prefetch_domain_types(unique_domains)
        logger.info(f"[Job {job_id}] 🔍 Domain pre-scan: {len(unique_domains)} unique domains classified")

        CONCURRENT_MAP = {
            "exchange_online":  settings.CONCURRENT_EXCHANGE_ONLINE,
            "exchange_onprem":  settings.CONCURRENT_EXCHANGE_ONPREM,
            "gateway":          settings.CONCURRENT_GATEWAY,
            "google_workspace": settings.CONCURRENT_GOOGLE_WORKSPACE,
            "postfix_other":    settings.CONCURRENT_POSTFIX_OTHER,
            "unknown":          settings.PER_DOMAIN_CONCURRENT,
        }
        
        domain_semaphores: dict[str, asyncio.Semaphore] = {
            domain: asyncio.Semaphore(CONCURRENT_MAP.get(domain_type_map.get(domain, "unknown"), settings.PER_DOMAIN_CONCURRENT))
            for domain in unique_domains
        }
        
        processed_count = 0
        stats = defaultdict(int)
        
        # Process cache hits directly
        for email, res in cache_hits:
            await _buffer_result({
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "email": email,
                "domain": email.split('@')[1] if '@' in email else None,
                "status": res.get("status", "unknown"),
                "is_role": False,
                "is_disposable": False,
                "smtp_result": "cached"
            }, db)
            stats[res.get("status", "unknown")] += 1
            processed_count += 1
            
            icon_map = {
                'valid': '✅', 'invalid': '❌', 'disposable': '🗑️',
                'catch_all': '📬', 'role_based': '👥', 'unknown': '❓',
            }
            logger.info(f"[Job {job_id}] {icon_map.get(res.get('status', 'unknown'), '•')} {email} → {res.get('status', 'unknown').upper()} (cached)")
            
        if len(cache_hits) > 0:
            db.execute("""
            UPDATE verification_jobs 
            SET processed_emails = processed_emails + ? 
            WHERE id = ?
            """, [len(cache_hits), job_id])

        async def bounded_process(email):
            nonlocal processed_count
            if '@' in email:
                domain = email.split('@')[1].lower()
            else:
                domain = "invalid"

            domain_sem = domain_semaphores.get(domain, asyncio.Semaphore(settings.PER_DOMAIN_CONCURRENT))
            
            async with _global_semaphore:
                async with job_semaphore:
                    async with domain_sem:
                        res = await verify_single_email(email)
                        
            processed_count += 1
            status = res.get('status', 'unknown')
            stats[status] += 1
            
            icon_map = {
                'valid': '✅', 'invalid': '❌', 'disposable': '🗑️',
                'catch_all': '📬', 'role_based': '👥', 'unknown': '❓',
            }
            icon = icon_map.get(status, '•')
            smtp_info = res.get('smtp_result', '')
            logger.info(f"[Job {job_id}] {icon} {email} → {status.upper()} ({smtp_info})")
            
            if processed_count % 10 == 0 or processed_count == total:
                pct = round(processed_count / total * 100, 1)
                logger.info(f"[Job {job_id}] 📈 Progress: {processed_count:,}/{total:,} ({pct}%)")
                try:
                    db.execute("UPDATE verification_jobs SET processed_emails = ? WHERE id = ?", [processed_count, job_id])
                except Exception:
                    pass

            await _buffer_result({
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "email": email,
                "domain": res.get('domain'),
                "status": res.get('status'),
                "is_role": res.get('is_role'),
                "is_disposable": res.get('is_disposable'),
                "smtp_result": res.get('smtp_result')
            }, db)
            
            return res

        # Staggered launch loop instead of gathering all instantly
        results = await _staggered_gather(emails_to_verify, bounded_process, job_delay)
        
        # Flush DB output buffer unconditionally at job conclusion
        await _flush_result_buffer(db)

        # Set final accurate processed emails count from actual results table
        cnt_row = db.execute("SELECT COUNT(*) FROM verification_results WHERE job_id = ?", [job_id]).fetchone()
        final_processed = cnt_row[0] if cnt_row else processed_count

        db.execute("UPDATE verification_jobs SET processed_emails = ? WHERE id = ?", [final_processed, job_id])

        # Set job status completed and recorded credits used
        db.execute("""
            UPDATE verification_jobs 
            SET status = 'completed', 
                credits_used = ?,
                completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, [total, job_id])

        # Deduct credits from workspace and user upon completion
        j_row = db.execute("SELECT user_id, workspace_id FROM verification_jobs WHERE id = ?", [job_id]).fetchone()
        if j_row:
            u_id, w_id = j_row[0], j_row[1]
            db.execute("""
                UPDATE users
                SET credit_pool = GREATEST(0, COALESCE(credit_pool, 0) - ?),
                    credits = GREATEST(0, COALESCE(credits, 0) - ?)
                WHERE id = ?
            """, [total, total, u_id])

            if w_id:
                db.execute("""
                    UPDATE workspaces
                    SET credits_remaining = GREATEST(0, COALESCE(credits_remaining, 0) - ?),
                        credits_used = COALESCE(credits_used, 0) + ?
                    WHERE id = ?
                """, [total, total, w_id])
        
        try:
            user_row = db.execute(
                "SELECT u.email FROM users u JOIN verification_jobs j ON j.user_id = u.id WHERE j.id = ?",
                [job_id]
            ).fetchone()
            if user_row:
                user_email = user_row[0]
                from email_service import EmailService
                await EmailService.sendVerificationCompletedEmail(
                    to_email=user_email,
                    job_id=job_id,
                    total_emails=total,
                    valid_emails=stats.get('valid', 0)
                )
        except Exception as email_err:
            logger.error(f"[Job {job_id}] Failed to send job completion email: {email_err}")
        
        summary_parts = [f"{status}: {count}" for status, count in sorted(stats.items())]
        logger.info(f"[Job {job_id}] 🎉 Job completed! Results: {', '.join(summary_parts)}")
        
    except asyncio.CancelledError:
        logger.info(f"[Job {job_id}] 🛑 Job cancelled")
        db = get_db()
        await _flush_result_buffer(db)
        cnt_row = db.execute("SELECT COUNT(*) FROM verification_results WHERE job_id = ?", [job_id]).fetchone()
        actual_cnt = cnt_row[0] if cnt_row else 0
        db.execute("UPDATE verification_jobs SET status = 'cancelled', processed_emails = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", [actual_cnt, job_id])
    except Exception as e:
        logger.error(f"[Job {job_id}] failed: {e}")
        db = get_db()
        cnt_row = db.execute("SELECT COUNT(*) FROM verification_results WHERE job_id = ?", [job_id]).fetchone()
        actual_cnt = cnt_row[0] if cnt_row else 0
        db.execute("UPDATE verification_jobs SET status = 'failed', processed_emails = ? WHERE id = ?", [actual_cnt, job_id])
    finally:
        _active_job_tasks.pop(job_id, None)
        _cancelled_job_ids.discard(job_id)
