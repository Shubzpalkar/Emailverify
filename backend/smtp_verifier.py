import asyncio
import aiosmtplib
from typing import Tuple, Dict

async def connect_and_check(mx_server: str, email: str, sender_email: str = "test@verifier.local") -> Tuple[int, str]:
    """
    Connect to the SMTP server and perform the handshake.
    Returns (status_code, response_message)
    """
    try:
        smtp = aiosmtplib.SMTP(hostname=mx_server, port=25, timeout=10)
        await smtp.connect()
        # Some servers require EHLO/HELO
        await smtp.ehlo()
        
        # Test mail from
        mail_from_response = await smtp.mail(sender_email)
        if mail_from_response.code >= 400:
            msg = mail_from_response.message.lower()
            code = mail_from_response.code
            await smtp.quit()
            return code, f"error on MAIL FROM: {msg}"
            
        # Test rcpt to
        rcpt_to_response = await smtp.rcpt(email)
        await smtp.quit()
        
        return rcpt_to_response.code, rcpt_to_response.message.lower()
    except aiosmtplib.SMTPException as e:
        return 0, f"smtp exception: {str(e)}"
    except Exception as e:
        # Connection timeouts, DNS errors, etc.
        return 0, f"connection failed: {str(e)}"

async def verify_smtp_with_retries(mx_server: str, email: str, sender_email: str = "test@verifier.local") -> Dict[str, str]:
    """
    Verify email via SMTP with retry logic for temporary errors.
    Returns a dictionary with status and reason.
    """
    delays = [5, 30, 120]
    
    for attempt in range(len(delays) + 1): # Max 4 attempts (1 initial + 3 retries)
        code, msg = await connect_and_check(mx_server, email, sender_email)
        
        # Interpret response
        if code == 250:
            return {"status": "valid", "reason": "smtp_valid"}
        
        if code == 550:
            # 550 can sometimes be a block, but per requirements we mostly treat it as invalid unless explicitly noted.
            if "spamhaus" in msg or "blocked" in msg:
                return {"status": "unknown", "reason": "blocked_by_provider"}
            return {"status": "invalid", "reason": "user_not_found"}
        
        # 421 Service not available, closing transmission channel
        # 450 Requested mail action not taken: mailbox unavailable (e.g., mail queue full, greylisting)
        if code in (421, 450) or "greylist" in msg or "too many connections" in msg:
            if attempt < len(delays):
                delay = delays[attempt]
                print(f"[SMTP Retry] {email} got {code} ({msg}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            else:
                return {"status": "unknown", "reason": "temporary_error_timeout"}
        
        # Connection errors (code 0) or timeouts - might be worth retrying if it's transient, 
        # but let's just attempt retries on actual SMTP codes that imply greylisting/rate limits.
        # However, connection refused/timeouts could mean they block connections.
        if code == 0:
            if attempt < len(delays):
                delay = delays[attempt]
                await asyncio.sleep(delay)
                continue
            else:
                return {"status": "unknown", "reason": f"connection_failed: {msg}"}
        
        # Any other code
        return {"status": "unknown", "reason": f"unhandled_smtp_response_{code}"}
        
    return {"status": "unknown", "reason": "max_retries_exceeded"}

async def check_catch_all(mx_server: str, domain: str) -> bool:
    """
    Checks if the domain is a catch-all by sending an email to a random address.
    """
    import uuid
    random_local = f"bounce-{uuid.uuid4().hex[:10]}"
    random_email = f"{random_local}@{domain}"
    
    code, _ = await connect_and_check(mx_server, random_email)
    return code == 250
