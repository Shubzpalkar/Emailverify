import asyncio
import uuid
import time
import logging
from typing import Tuple, Dict, Any, Optional, List
import aiosmtplib

from config import settings

logger = logging.getLogger("verification_engine.smtp")

# Per-domain SMTP concurrency limiters
_domain_semaphores: Dict[str, asyncio.Semaphore] = {}

def get_domain_semaphore(domain: str, max_concurrent: int = 5) -> asyncio.Semaphore:
    domain_clean = domain.lower().strip()
    if domain_clean not in _domain_semaphores:
        _domain_semaphores[domain_clean] = asyncio.Semaphore(max_concurrent)
    return _domain_semaphores[domain_clean]

def map_smtp_response(code: int, message: str) -> Tuple[str, str]:
    """
    Map SMTP response codes and error messages to structured statuses and detailed reasons.
    Ensures 220/221 greetings are NEVER treated as Deliverable.
    """
    msg_lower = message.lower()

    if "error on mail from" in msg_lower:
        if code >= 500:
            return "Protected", f"Sender address rejected during MAIL FROM ({code}): {message}"
        return "Temporary Failure", f"Temporary error during MAIL FROM ({code}): {message}"

    if code in (220, 221):
        return "Temporary Failure", f"Protocol greeting/closing response code {code} during RCPT TO stage"
    if code in (250, 251):
        return "Deliverable", "Recipient address explicitly accepted by target server"
    if code == 252:
        return "Catch-All", "Cannot verify mailbox directly; server accepts recipient tentatively (code 252)"

    # Temporary & Resource Quota Errors (4xx)
    if code == 421:
        return "Temporary Failure", "SMTP service unavailable or closing transmission channel"
    if code == 422:
        return "Mailbox Full", "Recipient mailbox full or storage quota exceeded"
    if code == 431:
        return "Temporary Failure", "Server out of memory or temporary resource constraint"
    if code == 432:
        return "Temporary Failure", "Server queue paused or suppressed"
    if code == 450:
        if "greylist" in msg_lower:
            return "Greylisted", "Server greylisting active (mailbox temporarily unavailable)"
        return "Temporary Failure", "Requested mail action not taken: mailbox busy or unavailable"
    if code == 451:
        if "greylist" in msg_lower:
            return "Greylisted", "Server greylisting active (requested action aborted)"
        return "Greylisted", "Server temporary policy restriction or greylisting"
    if code == 452:
        return "Mailbox Full", "Insufficient system storage or mailbox space exceeded"
    if code == 454:
        return "Temporary Failure", "TLS negotiation error or temporary authentication failure"

    # Protocol & Handshake Command Restrictions (500-504)
    if code in (500, 501, 502, 503, 504):
        return "Protected", f"Server restricts interactive SMTP verification commands ({code} Command Syntax/Policy)"

    # Security, Auth & Firewall Restrictions (521, 530, 535, 571)
    if code == 521:
        return "Protected", "Server rejects mail connections or service down"
    if code in (530, 535):
        return "Protected", "SMTP verification blocked: authentication required by target server"
    if code == 571:
        return "Protected", "Delivery unauthorized by recipient security policy"

    # Permanent Failures (550, 551, 552, 553, 554)
    if code == 550:
        # Check explicit recipient non-existence indicators first
        if any(term in msg_lower for term in ["user unknown", "no such user", "does not exist", "mailbox unavailable", "invalid recipient", "recipient unknown", "mailbox not found", "not found", "no such", "5.1.1", "bad destination"]):
            return "Undeliverable", f"Mailbox does not exist (550 User unknown): {message}"
        if any(term in msg_lower for term in ["disabled", "inactive", "suspended", "closed"]):
            return "Disabled", "Recipient mailbox is disabled or suspended"
        if any(term in msg_lower for term in ["spam", "blackhole", "rbl", "reputation", "policy", "barracuda", "proofpoint", "mimecast", "dmarc", "spf", "dkim", "relay access", "relay denied", "blocked by", "client host blocked", "access denied"]):
            return "Protected", f"SMTP verification blocked by recipient anti-spam/security policy ({message})"
        if any(term in msg_lower for term in ["unknown", "invalid", "unreachable", "recipient", "user", "address rejected"]):
            return "Undeliverable", f"Mailbox rejected (550): {message}"
        return "Undeliverable", f"Recipient rejected by target server (550): {message}"
    if code == 551:
        return "Undeliverable", "User not local; please try forwarding path"
    if code == 552:
        return "Mailbox Full", "Mailbox full or storage allocation exceeded"
    if code == 553:
        return "Undeliverable", "Requested action not taken: mailbox name invalid"
    if code == 554:
        if any(term in msg_lower for term in ["user unknown", "no such", "unknown", "not found", "does not exist", "5.1.1"]):
            return "Undeliverable", f"Mailbox rejected (554): {message}"
        return "Protected", f"Transaction failed due to anti-spam policy or security reject: {message}"

    # Connection & Socket Errors (Code 0)
    if code == 0:
        if any(term in msg_lower for term in ["refused", "reset", "closed", "connect", "firewall", "blocked"]):
            return "Protected", f"Port 25 connection reset or blocked by target firewall: {message}"
        if "timeout" in msg_lower:
            return "Temporary Failure", f"SMTP connection timeout: {message}"
        return "Temporary Failure", f"Network / socket connection failed: {message}"

    return "Unknown", f"Inconclusive SMTP response code {code}: {message}"

async def connect_and_check_transcript(
    mx_server: str, 
    email: str, 
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> Tuple[int, str, Dict[str, Any]]:
    """
    Connect to SMTP server, execute handshake using configured HELO/MAIL FROM, and record full SMTP Transcript.
    Returns (status_code, response_message, transcript_dict)
    """
    sender_email = sender_email or settings.SMTP_MAIL_FROM
    helo_host = helo_host or settings.SMTP_HELO_HOST

    start_time = time.perf_counter()
    transcript = {
        "banner": "",
        "ehlo": "",
        "capabilities": [],
        "starttls": False,
        "auth_support": False,
        "tls_version": "None",
        "cipher": "None",
        "rtt_ms": 0.0
    }

    try:
        smtp = aiosmtplib.SMTP(
            hostname=mx_server, 
            port=25, 
            timeout=settings.SMTP_CONNECT_TIMEOUT,
            local_hostname=helo_host
        )
        connect_res = await smtp.connect()
        transcript["banner"] = str(connect_res[1]).strip()

        # EHLO Handshake
        try:
            ehlo_code, ehlo_msg = await smtp.ehlo(hostname=helo_host, timeout=settings.SMTP_COMMAND_TIMEOUT)
            transcript["ehlo"] = f"{ehlo_code} {ehlo_msg}"
        except Exception:
            helo_code, helo_msg = await smtp.helo(hostname=helo_host, timeout=settings.SMTP_COMMAND_TIMEOUT)
            transcript["ehlo"] = f"{helo_code} {helo_msg}"

        transcript["capabilities"] = list(smtp.esmtp_extensions.keys()) if hasattr(smtp, "esmtp_extensions") else []
        transcript["auth_support"] = "auth" in [c.lower() for c in transcript["capabilities"]]

        # STARTTLS
        if smtp.supports_extension("STARTTLS"):
            try:
                await smtp.starttls(timeout=settings.SMTP_COMMAND_TIMEOUT)
                transcript["starttls"] = True
                try:
                    await smtp.ehlo(hostname=helo_host, timeout=settings.SMTP_COMMAND_TIMEOUT)
                except Exception:
                    await smtp.helo(hostname=helo_host, timeout=settings.SMTP_COMMAND_TIMEOUT)

                if hasattr(smtp, "transport") and smtp.transport:
                    ssl_obj = smtp.transport.get_extra_info("ssl_object")
                    if ssl_obj:
                        transcript["tls_version"] = ssl_obj.version() or "TLSv1.2/1.3"
                        cipher_tuple = ssl_obj.cipher()
                        if cipher_tuple:
                            transcript["cipher"] = cipher_tuple[0]
            except Exception as tls_err:
                logger.debug(f"STARTTLS negotiation failed for {mx_server}: {tls_err}")

        # MAIL FROM
        mail_from_res = await smtp.mail(sender_email, timeout=settings.SMTP_COMMAND_TIMEOUT)
        if mail_from_res.code >= 400:
            msg = mail_from_res.message.lower()
            code = mail_from_res.code
            try:
                await smtp.quit(timeout=settings.SMTP_COMMAND_TIMEOUT)
            except Exception:
                pass
            rtt = (time.perf_counter() - start_time) * 1000.0
            transcript["rtt_ms"] = round(rtt, 2)
            return code, f"error on MAIL FROM: {msg}", transcript

        # RCPT TO
        rcpt_to_res = await smtp.rcpt(email, timeout=settings.SMTP_COMMAND_TIMEOUT)
        try:
            await smtp.quit(timeout=settings.SMTP_COMMAND_TIMEOUT)
        except Exception:
            pass

        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return rcpt_to_res.code, rcpt_to_res.message, transcript

    except aiosmtplib.SMTPResponseException as e:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return e.code, e.message, transcript
    except aiosmtplib.SMTPConnectTimeoutError:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return 0, "SMTP connection timed out", transcript
    except aiosmtplib.SMTPTimeoutError:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return 0, "SMTP command timed out", transcript
    except aiosmtplib.SMTPException as e:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return 0, f"SMTP exception: {str(e)}", transcript
    except (ConnectionResetError, ConnectionRefusedError, TimeoutError, OSError) as e:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return 0, f"Socket error: {str(e)}", transcript
    except Exception as e:
        rtt = (time.perf_counter() - start_time) * 1000.0
        transcript["rtt_ms"] = round(rtt, 2)
        return 0, f"Connection failed: {str(e)}", transcript

async def connect_and_check(
    mx_server: str, 
    email: str, 
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> Tuple[int, str, bool]:
    """
    Backward compatible helper returning (status_code, message, tls_used).
    """
    code, msg, transcript = await connect_and_check_transcript(mx_server, email, sender_email, helo_host)
    return code, msg, transcript.get("starttls", False)

async def _verify_smtp_inner(
    mx_server: str, 
    email: str, 
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify email via SMTP with exponential backoff retries for temporary errors.
    Returns structured result dictionary including full SMTP transcript telemetry.
    """
    sender_email = sender_email or settings.SMTP_MAIL_FROM
    helo_host = helo_host or settings.SMTP_HELO_HOST
    delays = settings.RETRY_DELAYS  # e.g. [1, 2, 4] or [5, 30, 120]
    domain = email.split('@')[1] if '@' in email else "generic"
    sem = get_domain_semaphore(domain, max_concurrent=settings.PER_DOMAIN_CONCURRENT)

    last_code = 0
    last_msg = ""
    last_transcript = {}

    non_retryable_codes = {220, 221, 250, 251, 252, 500, 501, 502, 503, 504, 521, 530, 535, 550, 551, 553, 554, 571}

    async with sem:
        for attempt in range(len(delays) + 1):
            code, msg, transcript = await connect_and_check_transcript(mx_server, email, sender_email, helo_host)
            last_code = code
            last_msg = msg
            last_transcript = transcript

            status, reason = map_smtp_response(code, msg)

            # Permanent failure or success -> return immediately without retrying
            if code in non_retryable_codes or status in ("Deliverable", "Undeliverable", "Protected", "Disabled", "Catch-All"):
                return {
                    "status": status,
                    "smtp_code": code,
                    "reason": reason,
                    "raw_message": msg,
                    "tls_used": transcript.get("starttls", False),
                    "retry_attempts": attempt,
                    "smtp_transcript": transcript
                }

            # Check if retryable (421, 422, 431, 432, 450, 451, 452, 454 or connection timeouts)
            is_retryable = code in (421, 422, 431, 432, 450, 451, 452, 454) or code == 0 or status in ("Greylisted", "Temporary Failure")
            if is_retryable and attempt < len(delays):
                delay = delays[attempt]
                logger.info(f"[SMTP Retry {attempt+1}/{len(delays)}] {email} on {mx_server} got code {code} ({reason}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            else:
                break

    status, reason = map_smtp_response(last_code, last_msg)
    return {
        "status": status,
        "smtp_code": last_code,
        "reason": reason,
        "raw_message": last_msg,
        "tls_used": last_transcript.get("starttls", False),
        "retry_attempts": min(attempt, len(delays)),
        "smtp_transcript": last_transcript
    }

async def verify_smtp_with_retries(
    mx_server: str, 
    email: str, 
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> Dict[str, Any]:
    """
    Outer wrapper with hard timeout enforcement.
    Returns structured dictionary with backward compatible 'status' and 'reason'.
    """
    sender_email = sender_email or settings.SMTP_MAIL_FROM
    helo_host = helo_host or settings.SMTP_HELO_HOST
    try:
        res = await asyncio.wait_for(
            _verify_smtp_inner(mx_server, email, sender_email, helo_host),
            timeout=settings.SMTP_HARD_TIMEOUT
        )
        return res
    except asyncio.TimeoutError:
        return {
            "status": "Temporary Failure",
            "smtp_code": 408,
            "reason": "SMTP hard timeout limit exceeded",
            "raw_message": "Hard timeout",
            "tls_used": False,
            "retry_attempts": 0,
            "smtp_transcript": {"banner": "", "ehlo": "", "capabilities": [], "starttls": False, "rtt_ms": 0.0}
        }

async def check_catch_all_detailed(
    mx_server: str, 
    domain: str,
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs dual-probe catch-all verification using two distinct non-existent addresses.
    If both probes return code 250, domain is confirmed Catch-All.
    """
    sender_email = sender_email or settings.SMTP_MAIL_FROM
    helo_host = helo_host or settings.SMTP_HELO_HOST

    probe1 = f"chk-probe1-{uuid.uuid4().hex[:12]}@{domain}"
    probe2 = f"chk-probe2-{uuid.uuid4().hex[:12]}@{domain}"

    code1, msg1, _ = await connect_and_check(mx_server, probe1, sender_email=sender_email, helo_host=helo_host)
    if code1 not in (250, 251):
        return {
            "is_catch_all": False,
            "confidence": 0.95,
            "reason": f"First random probe rejected with code {code1}: {msg1}"
        }

    code2, msg2, _ = await connect_and_check(mx_server, probe2, sender_email=sender_email, helo_host=helo_host)
    if code2 in (250, 251):
        return {
            "is_catch_all": True,
            "confidence": 0.90,
            "reason": "Both random probe emails accepted by target MX server (Catch-All domain)"
        }
    else:
        return {
            "is_catch_all": False,
            "confidence": 0.85,
            "reason": f"Second probe rejected with code {code2}: {msg2}"
        }

async def check_catch_all(
    mx_server: str, 
    domain: str,
    sender_email: Optional[str] = None,
    helo_host: Optional[str] = None
) -> bool:
    """
    Checks if the domain is a catch-all for backward compatibility.
    """
    res = await check_catch_all_detailed(mx_server, domain, sender_email, helo_host)
    return res["is_catch_all"]
