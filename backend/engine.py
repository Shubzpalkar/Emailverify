import re
import asyncio
import datetime
from typing import Dict, Any, Tuple
from database import get_db
from config import settings

from dns_checks import check_domain
from smtp_verifier import verify_smtp_with_retries, check_catch_all as check_catch_all_smtp

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

def check_syntax(email: str) -> bool:
    if not isinstance(email, str) or len(email) > 254:
        return False
    # Check for double dots specifically as per requirements
    if ".." in email:
        return False
    return bool(EMAIL_REGEX.match(email))

def check_role(email: str) -> bool:
    local_part = email.split('@')[0].lower()
    return local_part in ROLE_PREFIXES

def check_disposable(domain: str) -> bool:
    db = get_db()
    res = db.execute("SELECT domain FROM disposable_domains WHERE domain = ?", [domain]).fetchone()
    return res is not None

async def get_domain_intelligence(domain: str) -> dict:
    db = get_db()
    res = db.execute("SELECT mx_server, catch_all, disposable, reputation_score FROM domain_intelligence "
                     "WHERE domain = ? AND (epoch(CURRENT_TIMESTAMP) - epoch(last_checked)) < ?", 
                     [domain, settings.DOMAIN_INTELLIGENCE_TTL]).fetchone()
    if res:
        return {
            "mx_server": res[0],
            "catch_all": res[1],
            "disposable": res[2],
            "reputation_score": res[3]
        }
    return None

async def save_domain_intelligence(domain: str, info: dict):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO domain_intelligence 
        (domain, mx_server, catch_all, disposable, reputation_score, last_checked)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [domain, info.get("mx_server"), info.get("catch_all"), info.get("disposable"), info.get("reputation_score", 1.0), datetime.datetime.now()])

async def get_email_cache(email: str) -> dict:
    db = get_db()
    res = db.execute("SELECT status, confidence FROM email_cache "
                     "WHERE email = ? AND (epoch(CURRENT_TIMESTAMP) - epoch(verified_at)) < ?", 
                     [email, settings.EMAIL_CACHE_TTL]).fetchone()
    if res:
        return {"status": res[0], "confidence": res[1]}
    return None

async def save_email_cache(email: str, status: str, confidence: float):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO email_cache 
        (email, status, confidence, verified_at)
        VALUES (?, ?, ?, ?)
    """, [email, status, confidence, datetime.datetime.now()])

def get_confidence_and_status(smtp_result: Dict[str, str], domain_info: dict, is_role: bool) -> Tuple[str, float]:
    """Risk classification and confidence scoring based on all factors."""
    if domain_info.get("disposable"):
        return "disposable", 0.0
        
    if smtp_result["status"] == "invalid":
        return "invalid", 0.0
        
    if domain_info.get("catch_all"):
        return "catch_all", 0.60
        
    if smtp_result["status"] == "valid":
        if is_role:
            return "role_based", 0.85
        return "valid", 0.95
        
    # 'unknown' (temporary errors, blocked, max retries exceeded)
    return "unknown", 0.40

async def verify_single_email(email: str, check_catch_all: bool = True) -> Dict[str, Any]:
    # 1. Syntax Phase
    if not check_syntax(email):
        return {
            "email": email,
            "status": "invalid",
            "confidence": 0.0,
            "domain": email.split('@')[1] if '@' in email else None,
            "mx_server": None,
            "catch_all": False,
            "disposable": False,
            "role_based": False,
            "smtp_result": "invalid_syntax"
        }
        
    local_part, domain = email.split('@')
    domain = domain.lower()
    is_role = check_role(email)
    
    # 2. Check Verification Cache
    cached_result = await get_email_cache(email)
    if cached_result:
        # Re-fetch domain intelligence just to populate the full response object
        domain_info = await get_domain_intelligence(domain) or {"mx_server": None, "catch_all": False, "disposable": False}
        return {
            "email": email,
            "status": cached_result["status"],
            "confidence": cached_result["confidence"],
            "domain": domain,
            "mx_server": domain_info.get("mx_server"),
            "catch_all": domain_info.get("catch_all", False),
            "disposable": domain_info.get("disposable", False),
            "role_based": is_role,
            "smtp_result": "cached"
        }

    # 3. Domain Intelligence Check & Update
    domain_info = await get_domain_intelligence(domain)
    
    if not domain_info:
        # A. DNS Check
        dns_status, mx_records_str = await check_domain(domain)
        
        if dns_status == "invalid":
            # DNS invalid means everything fails
            domain_info = {
                "mx_server": None,
                "catch_all": False,
                "disposable": False,
                "reputation_score": 0.0
            }
            await save_domain_intelligence(domain, domain_info)
            await save_email_cache(email, "invalid", 0.0)
            
            return {
                "email": email,
                "status": "invalid",
                "confidence": 0.0,
                "domain": domain,
                "mx_server": None,
                "catch_all": False,
                "disposable": False,
                "role_based": is_role,
                "smtp_result": mx_records_str # contains "domain_not_found"
            }
            
        # Has MX
        primary_mx = mx_records_str.split(",")[0]
        
        # B. Disposable Detection
        is_disposable = check_disposable(domain)
        
        # C. Catch-All Detection
        catch_all = False
        if check_catch_all and not is_disposable:
             catch_all = await check_catch_all_smtp(primary_mx, domain)
             
        domain_info = {
            "mx_server": primary_mx,
            "catch_all": catch_all,
            "disposable": is_disposable,
            "reputation_score": 1.0 if not is_disposable else 0.0
        }
        await save_domain_intelligence(domain, domain_info)

    # 4. Disposable Fast-Fail
    if domain_info["disposable"]:
        status, confidence = "disposable", 0.0
        await save_email_cache(email, status, confidence)
        return {
            "email": email,
            "status": status,
            "confidence": confidence,
            "domain": domain,
            "mx_server": domain_info["mx_server"],
            "catch_all": False,
            "disposable": True,
            "role_based": is_role,
            "smtp_result": "disposable_domain"
        }

    # 5. SMTP Mailbox Verification (with retries)
    if domain_info["mx_server"]:
        smtp_res = await verify_smtp_with_retries(domain_info["mx_server"], email)
    else:
        smtp_res = {"status": "invalid", "reason": "no_mx_server"}

    # 6. Risk Classification & Confidence
    final_status, final_confidence = get_confidence_and_status(smtp_res, domain_info, is_role)
    
    # 7. Final Cache Save
    await save_email_cache(email, final_status, final_confidence)

    import logging
    logger = logging.getLogger("verification_engine")
    
    result_data = {
        "email": email,
        "status": final_status,
        "confidence": final_confidence,
        "domain": domain,
        "mx_server": domain_info["mx_server"],
        "catch_all": bool(domain_info["catch_all"]),
        "disposable": bool(domain_info["disposable"]),
        "role_based": is_role,
        "smtp_result": smtp_res["reason"],
        "verification_time": datetime.datetime.now().isoformat()
    }
    
    logger.info(f"Verified {email} | Domain: {domain} | MX: {domain_info['mx_server']} | Status: {final_status} | SMTP: {smtp_res['reason']}")
    
    return result_data
