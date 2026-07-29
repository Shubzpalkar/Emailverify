import re
import asyncio
import datetime
import time
import logging
from typing import Dict, Any, Tuple, Optional, List

from database import get_db
from config import settings

from dns_checks import (
    resolve_domain_detail, 
    detect_provider_details, 
    resolve_mx_ip, 
    get_ptr_record,
    dns_health_monitor
)
from smtp_verifier import (
    verify_smtp_with_retries, 
    check_catch_all_detailed
)
from provider_engine import provider_engine

logger = logging.getLogger("verification_engine")

class EngineMetrics:
    def __init__(self):
        self.total_verifications = 0
        self.total_latency_ms = 0.0
        self.dns_latency_ms = 0.0
        self.smtp_latency_ms = 0.0
        self.status_counts = {}
        self.provider_counts = {}

    def record_verification(self, status: str, provider: str, latency_ms: float, dns_ms: float = 0.0, smtp_ms: float = 0.0):
        self.total_verifications += 1
        self.total_latency_ms += latency_ms
        self.dns_latency_ms += dns_ms
        self.smtp_latency_ms += smtp_ms
        self.status_counts[status] = self.status_counts.get(status, 0) + 1
        self.provider_counts[provider] = self.provider_counts.get(provider, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        avg_lat = round(self.total_latency_ms / self.total_verifications, 1) if self.total_verifications > 0 else 0.0
        avg_dns = round(self.dns_latency_ms / self.total_verifications, 1) if self.total_verifications > 0 else 0.0
        avg_smtp = round(self.smtp_latency_ms / self.total_verifications, 1) if self.total_verifications > 0 else 0.0
        unknown_cnt = self.status_counts.get("Unknown", 0) + self.status_counts.get("unknown", 0)
        unknown_rate = round((unknown_cnt / self.total_verifications) * 100, 2) if self.total_verifications > 0 else 0.0

        return {
            "total_verifications": self.total_verifications,
            "avg_verification_time_ms": avg_lat,
            "avg_dns_latency_ms": avg_dns,
            "avg_smtp_latency_ms": avg_smtp,
            "unknown_rate_pct": unknown_rate,
            "status_breakdown": self.status_counts,
            "provider_distribution": self.provider_counts,
            "dns_resolvers": dns_health_monitor.get_metrics_summary()
        }

engine_metrics = EngineMetrics()

# Strict email syntax validation
EMAIL_REGEX = re.compile(
    r"^(?!\.)(\"([^\"\\]|\\[\"\\])*\"|[-a-zA-Z0-9!#$%&'*+/=?^_`{|}~]+(\.[-a-zA-Z0-9!#$%&'*+/=?^_`{|}~]+)*)@"
    r"(?!-)(?:[a-zA-Z0-9-]{0,62}[a-zA-Z0-9]\.)+[a-zA-Z]{2,6}$"
)

ROLE_PREFIXES = {
    "admin", "info", "sales", "support", "contact", "billing",
    "hello", "jobs", "careers", "marketing", "office", "help",
    "webmaster", "postmaster", "hostmaster", "abuse", "team"
}

FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
    "protonmail.com", "zoho.com", "mail.com", "gmx.com", "yandex.com", "live.com"
}

def check_syntax(email: str) -> bool:
    if not isinstance(email, str) or len(email) > 254:
        return False
    if ".." in email:
        return False
    return bool(EMAIL_REGEX.match(email))

def check_role(email: str) -> bool:
    if '@' not in email:
        return False
    local_part = email.split('@')[0].lower()
    return local_part in ROLE_PREFIXES

def check_disposable(domain: str) -> bool:
    db = get_db()
    res = db.execute("SELECT domain FROM disposable_domains WHERE domain = ?", [domain.lower()]).fetchone()
    return res is not None

def compute_quality_and_confidence(detailed_status: str, is_role: bool = False, is_disposable: bool = False) -> Tuple[str, float]:
    """
    Compute final quality classification and multi-signal confidence score.
    Granular statuses supported:
    Deliverable, Undeliverable, Catch-All, Protected, Greylisted, Mailbox Full, Mailbox Disabled,
    Temporary Failure, DNS Timeout, DNS Failure, Resolver Failure, SMTP Timeout, SMTP Failure,
    Invalid Domain, No MX, Disposable, Role Based, Risky, Unknown.
    """
    if is_disposable:
        return "Risky", 0.0

    quality_map = {
        "Deliverable": ("Good", 0.95 if not is_role else 0.85),
        "Catch-All": ("Risky", 0.60),
        "Greylisted": ("Risky", 0.50),
        "Mailbox Full": ("Risky", 0.40),
        "Protected": ("Risky", 0.30),
        "Role Based": ("Risky", 0.80),
        "Disposable": ("Risky", 0.0),
        "Undeliverable": ("Bad", 0.0),
        "Mailbox Disabled": ("Bad", 0.0),
        "Invalid Domain": ("Bad", 0.0),
        "No MX": ("Bad", 0.0),
        "Disabled": ("Bad", 0.0),
        "Temporary Failure": ("Risky", 0.35),
        "DNS Timeout": ("Risky", 0.30),
        "DNS Failure": ("Risky", 0.30),
        "Resolver Failure": ("Risky", 0.30),
        "SMTP Timeout": ("Risky", 0.35),
        "SMTP Failure": ("Risky", 0.35),
        "Risky": ("Risky", 0.50),
        "Unknown": ("Unknown", 0.20)
    }

    return quality_map.get(detailed_status, ("Unknown", 0.40))

def map_to_legacy_status(detailed_status: str, is_role: bool, is_disposable: bool) -> str:
    """Ensure 100% backward compatibility for legacy DB and API consumers."""
    if is_disposable:
        return "disposable"
    if detailed_status in ("Deliverable", "valid"):
        return "role_based" if is_role else "valid"
    if detailed_status in ("Undeliverable", "Invalid Domain", "No MX", "Disabled", "Mailbox Disabled", "invalid"):
        return "invalid"
    if detailed_status in ("Catch-All", "catch_all"):
        return "catch_all"
    if detailed_status == "Greylisted":
        return "greylisted"
    if detailed_status == "Protected":
        return "protected"
    if detailed_status == "Mailbox Full":
        return "mailbox_full"
    if detailed_status in ("Role Based", "role_based"):
        return "role_based"
    return "unknown"

async def get_domain_intelligence(domain: str) -> Optional[dict]:
    db = get_db()
    res = db.execute("SELECT mx_server, catch_all, disposable, reputation_score FROM domain_intelligence "
                     "WHERE domain = ? AND (epoch(CURRENT_TIMESTAMP) - epoch(last_checked)) < ?", 
                     [domain.lower(), settings.DOMAIN_INTELLIGENCE_TTL]).fetchone()
    if res:
        return {
            "mx_server": res[0],
            "catch_all": bool(res[1]),
            "disposable": bool(res[2]),
            "reputation_score": res[3]
        }
    return None

async def save_domain_intelligence(domain: str, info: dict):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO domain_intelligence 
        (domain, mx_server, catch_all, disposable, reputation_score, last_checked)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [domain.lower(), info.get("mx_server"), info.get("catch_all"), info.get("disposable"), info.get("reputation_score", 1.0), datetime.datetime.now()])

async def get_email_cache(email: str) -> Optional[dict]:
    db = get_db()
    res = db.execute("SELECT status, confidence FROM email_cache "
                     "WHERE email = ? AND (epoch(CURRENT_TIMESTAMP) - epoch(verified_at)) < ?", 
                     [email.lower(), settings.EMAIL_CACHE_TTL]).fetchone()
    if res:
        return {"status": res[0], "confidence": res[1]}
    return None

async def save_email_cache(email: str, status: str, confidence: float):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO email_cache 
        (email, status, confidence, verified_at)
        VALUES (?, ?, ?, ?)
    """, [email.lower(), status, confidence, datetime.datetime.now()])

async def verify_single_email(email: str, check_catch_all: bool = True) -> Dict[str, Any]:
    start_ts = time.perf_counter()
    start_time = datetime.datetime.now()

    # 1. Syntax Phase
    if not check_syntax(email):
        domain = email.split('@')[1] if '@' in email else None
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification("Undeliverable", "None", elapsed_ms)
        return {
            "email": email,
            "status": "invalid",
            "detailed_status": "Undeliverable",
            "quality": "Bad",
            "confidence": 0.0,
            "domain": domain,
            "mx_server": None,
            "mx_host": None,
            "catch_all": False,
            "disposable": False,
            "is_disposable": False,
            "role_based": False,
            "is_role": False,
            "provider_name": "None",
            "provider_type": "none",
            "provider": "None",
            "reason": "Invalid email syntax structure",
            "smtp_result": "invalid_syntax",
            "smtp_code": 0,
            "smtp_message": "invalid_syntax",
            "dns_status": "invalid_syntax",
            "retryable": False,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": False,
                "domain": domain,
                "dns": {"dns_status": "invalid_syntax", "reason": "Syntax check failed"},
                "mx": {"has_mx": False, "records": []},
                "smtp": {"code": 0, "response": "invalid_syntax"},
                "tls": False,
                "catch_all": False,
                "disposable": False,
                "role_account": False,
                "free_provider": False,
                "mailbox_exists": False,
                "greylisted": False,
                "protected": False,
                "confidence_score": 0.0,
                "final_quality": "Bad"
            }
        }

    local_part, domain = email.split('@')
    domain = domain.lower()
    is_role = check_role(email)
    is_free = domain in FREE_PROVIDERS

    # 2. Check Verification Cache
    cached = await get_email_cache(email)
    if cached:
        domain_info = await get_domain_intelligence(domain) or {"mx_server": None, "catch_all": False, "disposable": False}
        legacy_status = cached["status"]
        quality, conf = compute_quality_and_confidence(legacy_status.capitalize(), is_role, domain_info.get("disposable", False))
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification(legacy_status, "Cached", elapsed_ms)
        return {
            "email": email,
            "status": legacy_status,
            "detailed_status": legacy_status.capitalize(),
            "quality": quality,
            "confidence": cached["confidence"],
            "domain": domain,
            "mx_server": domain_info.get("mx_server"),
            "mx_host": domain_info.get("mx_server"),
            "catch_all": domain_info.get("catch_all", False),
            "disposable": domain_info.get("disposable", False),
            "is_disposable": domain_info.get("disposable", False),
            "role_based": is_role,
            "is_role": is_role,
            "provider_name": "Cached",
            "provider_type": "cached",
            "provider": "Cached",
            "reason": "Retrieved from cache",
            "smtp_result": "cached",
            "smtp_code": 250,
            "smtp_message": "cached",
            "dns_status": "valid",
            "retryable": False,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": True,
                "domain": domain,
                "dns": {"dns_status": "valid", "reason": "Cached"},
                "mx": {"has_mx": bool(domain_info.get("mx_server")), "records": [domain_info.get("mx_server")] if domain_info.get("mx_server") else []},
                "smtp": {"code": 250, "response": "cached"},
                "tls": True,
                "catch_all": domain_info.get("catch_all", False),
                "disposable": domain_info.get("disposable", False),
                "role_account": is_role,
                "free_provider": is_free,
                "mailbox_exists": legacy_status == "valid",
                "greylisted": False,
                "protected": False,
                "confidence_score": cached["confidence"],
                "final_quality": quality
            }
        }

    # 3. DNS Lookup Phase
    dns_start = time.perf_counter()
    dns_detail = await resolve_domain_detail(domain)
    dns_ms = (time.perf_counter() - dns_start) * 1000.0

    if dns_detail["dns_status"] == "nxdomain":
        detailed_status = "Invalid Domain"
        quality, conf = compute_quality_and_confidence(detailed_status, is_role, False)
        legacy_status = map_to_legacy_status(detailed_status, is_role, False)
        reason = dns_detail["reason"]

        await save_email_cache(email, legacy_status, conf)
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification(detailed_status, "None", elapsed_ms, dns_ms=dns_ms)
        return {
            "email": email,
            "status": legacy_status,
            "detailed_status": detailed_status,
            "quality": quality,
            "confidence": conf,
            "domain": domain,
            "mx_server": None,
            "mx_host": None,
            "catch_all": False,
            "disposable": False,
            "is_disposable": False,
            "role_based": is_role,
            "is_role": is_role,
            "provider_name": "None",
            "provider_type": "none",
            "provider": "None",
            "reason": reason,
            "smtp_result": reason,
            "smtp_code": 0,
            "smtp_message": "nxdomain",
            "dns_status": dns_detail["dns_status"],
            "retryable": False,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": True,
                "domain": domain,
                "dns": dns_detail,
                "mx": {"has_mx": False, "records": []},
                "smtp": {"code": 0, "response": "nxdomain"},
                "tls": False,
                "catch_all": False,
                "disposable": False,
                "role_account": is_role,
                "free_provider": is_free,
                "mailbox_exists": False,
                "greylisted": False,
                "protected": False,
                "confidence_score": conf,
                "final_quality": quality
            }
        }

    if dns_detail["dns_status"] == "no_mx_server" or not dns_detail["mx_records"]:
        detailed_status = "No MX"
        quality, conf = compute_quality_and_confidence(detailed_status, is_role, False)
        legacy_status = map_to_legacy_status(detailed_status, is_role, False)
        reason = dns_detail["reason"]

        await save_email_cache(email, legacy_status, conf)
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification(detailed_status, "None", elapsed_ms, dns_ms=dns_ms)
        return {
            "email": email,
            "status": legacy_status,
            "detailed_status": detailed_status,
            "quality": quality,
            "confidence": conf,
            "domain": domain,
            "mx_server": None,
            "mx_host": None,
            "catch_all": False,
            "disposable": False,
            "is_disposable": False,
            "role_based": is_role,
            "is_role": is_role,
            "provider_name": "None",
            "provider_type": "none",
            "provider": "None",
            "reason": reason,
            "smtp_result": reason,
            "smtp_code": 0,
            "smtp_message": "no_mx_server",
            "dns_status": dns_detail["dns_status"],
            "retryable": False,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": True,
                "domain": domain,
                "dns": dns_detail,
                "mx": {"has_mx": False, "records": []},
                "smtp": {"code": 0, "response": "no_mx_server"},
                "tls": False,
                "catch_all": False,
                "disposable": False,
                "role_account": is_role,
                "free_provider": is_free,
                "mailbox_exists": False,
                "greylisted": False,
                "protected": False,
                "confidence_score": conf,
                "final_quality": quality
            }
        }

    # Handle temporary DNS failures without classifying as Invalid
    if dns_detail["dns_status"] in ("timeout", "servfail", "resolver_failure", "network_error", "temp_failure"):
        detailed_status = "DNS Timeout" if dns_detail["dns_status"] == "timeout" else "DNS Failure"
        quality, conf = compute_quality_and_confidence(detailed_status, is_role, False)
        legacy_status = "unknown"
        reason = dns_detail["reason"]

        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification(detailed_status, "None", elapsed_ms, dns_ms=dns_ms)
        return {
            "email": email,
            "status": legacy_status,
            "detailed_status": detailed_status,
            "quality": quality,
            "confidence": conf,
            "domain": domain,
            "mx_server": None,
            "mx_host": None,
            "catch_all": False,
            "disposable": False,
            "is_disposable": False,
            "role_based": is_role,
            "is_role": is_role,
            "provider_name": "None",
            "provider_type": "none",
            "provider": "None",
            "reason": reason,
            "smtp_result": reason,
            "smtp_code": 0,
            "smtp_message": dns_detail["dns_status"],
            "dns_status": dns_detail["dns_status"],
            "retryable": True,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": True,
                "domain": domain,
                "dns": dns_detail,
                "mx": {"has_mx": False, "records": []},
                "smtp": {"code": 0, "response": dns_detail["dns_status"]},
                "tls": False,
                "catch_all": False,
                "disposable": False,
                "role_account": is_role,
                "free_provider": is_free,
                "mailbox_exists": False,
                "greylisted": False,
                "protected": False,
                "confidence_score": conf,
                "final_quality": quality
            }
        }

    # 4. Provider & Intelligence Lookup
    mx_records = dns_detail["mx_records"]
    primary_mx = mx_records[0]
    p_info = provider_engine.detect_provider(mx_records, banner="", domain=domain)
    provider_name = p_info["provider_name"]
    provider_type = p_info["provider_type"]

    domain_info = await get_domain_intelligence(domain)
    if not domain_info:
        is_disposable = check_disposable(domain)
        catch_all_info = {"is_catch_all": False}
        if check_catch_all and not is_disposable:
            catch_all_info = await check_catch_all_detailed(primary_mx, domain)

        domain_info = {
            "mx_server": primary_mx,
            "catch_all": catch_all_info["is_catch_all"],
            "disposable": is_disposable,
            "reputation_score": 1.0 if not is_disposable else 0.0
        }
        await save_domain_intelligence(domain, domain_info)

    # 5. Disposable Check Fast-Fail
    if domain_info["disposable"]:
        detailed_status = "Disposable"
        quality, conf = compute_quality_and_confidence(detailed_status, is_role, True)
        legacy_status = map_to_legacy_status(detailed_status, is_role, True)
        reason = "Disposable temporary email provider"

        await save_email_cache(email, legacy_status, conf)
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        engine_metrics.record_verification(detailed_status, provider_name, elapsed_ms, dns_ms=dns_ms)
        return {
            "email": email,
            "status": legacy_status,
            "detailed_status": detailed_status,
            "quality": quality,
            "confidence": conf,
            "domain": domain,
            "mx_server": primary_mx,
            "mx_host": primary_mx,
            "catch_all": False,
            "disposable": True,
            "is_disposable": True,
            "role_based": is_role,
            "is_role": is_role,
            "provider_name": provider_name,
            "provider_type": provider_type,
            "provider": provider_name,
            "reason": reason,
            "smtp_result": reason,
            "smtp_code": 0,
            "smtp_message": "disposable_domain",
            "dns_status": dns_detail["dns_status"],
            "retryable": False,
            "latency_ms": round(elapsed_ms, 2),
            "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
            "smtp_transcript": {},
            "verification_report": {
                "syntax": True,
                "domain": domain,
                "dns": dns_detail,
                "mx": {"has_mx": True, "records": mx_records},
                "smtp": {"code": 0, "response": "disposable_domain"},
                "tls": False,
                "catch_all": False,
                "disposable": True,
                "role_account": is_role,
                "free_provider": is_free,
                "mailbox_exists": False,
                "greylisted": False,
                "protected": False,
                "confidence_score": conf,
                "final_quality": quality
            }
        }

    # 6. SMTP Verification Phase
    smtp_start = time.perf_counter()
    smtp_res = await verify_smtp_with_retries(primary_mx, email)
    smtp_ms = (time.perf_counter() - smtp_start) * 1000.0

    # PTR Enrichment for security blocked / unknown
    if smtp_res["status"] in ("Unknown", "Protected", "Temporary Failure"):
        mx_ip = await resolve_mx_ip(primary_mx)
        if mx_ip:
            ptr = await get_ptr_record(mx_ip)
            if ptr:
                smtp_res["reason"] += f" [PTR: {ptr}]"

    # 7. Weighted Decision Engine & Final Status Determination
    raw_status = smtp_res["status"]
    if raw_status == "Deliverable":
        if domain_info["catch_all"]:
            detailed_status = "Catch-All"
        elif is_role:
            detailed_status = "Role Based"
        else:
            detailed_status = "Deliverable"
    elif raw_status == "Protected" and p_info.get("rules", {}).get("hide_mailbox_existence"):
        detailed_status = "Protected"
        smtp_res["reason"] = f"{provider_name} protection active: {smtp_res['reason']}"
    else:
        detailed_status = raw_status

    quality, conf = compute_quality_and_confidence(detailed_status, is_role, False)
    legacy_status = map_to_legacy_status(detailed_status, is_role, False)
    reason = smtp_res["reason"]

    await save_email_cache(email, legacy_status, conf)

    elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
    engine_metrics.record_verification(detailed_status, provider_name, elapsed_ms, dns_ms=dns_ms, smtp_ms=smtp_ms)

    transcript = smtp_res.get("smtp_transcript", {})

    report = {
        "syntax": True,
        "domain": domain,
        "dns": dns_detail,
        "mx": {"has_mx": True, "records": mx_records},
        "smtp": {
            "code": smtp_res.get("smtp_code", 0),
            "response": smtp_res.get("raw_message", "")
        },
        "tls": smtp_res.get("tls_used", False),
        "catch_all": domain_info["catch_all"],
        "disposable": False,
        "role_account": is_role,
        "free_provider": is_free,
        "mailbox_exists": detailed_status in ("Deliverable", "Role Based"),
        "greylisted": detailed_status == "Greylisted",
        "protected": detailed_status == "Protected",
        "confidence_score": conf,
        "final_quality": quality
    }

    result = {
        "email": email,
        "status": legacy_status,
        "detailed_status": detailed_status,
        "quality": quality,
        "confidence": conf,
        "domain": domain,
        "mx_server": primary_mx,
        "mx_host": primary_mx,
        "catch_all": domain_info["catch_all"],
        "disposable": False,
        "is_disposable": False,
        "role_based": is_role,
        "is_role": is_role,
        "provider_name": provider_name,
        "provider_type": provider_type,
        "provider": provider_name,
        "reason": reason,
        "smtp_result": reason,
        "smtp_code": smtp_res.get("smtp_code", 0),
        "smtp_message": smtp_res.get("raw_message", ""),
        "dns_status": dns_detail["dns_status"],
        "retryable": detailed_status in ("Temporary Failure", "DNS Timeout", "Greylisted"),
        "latency_ms": round(elapsed_ms, 2),
        "verification_time_seconds": round(elapsed_ms / 1000.0, 3),
        "smtp_transcript": transcript,
        "verification_report": report
    }

    logger.info(f"Verified {email} | Domain: {domain} | MX: {primary_mx} | Provider: {provider_name} | Status: {detailed_status} | Quality: {quality} | Time: {round(elapsed_ms/1000.0, 2)}s")

    return result
