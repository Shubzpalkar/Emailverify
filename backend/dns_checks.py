import aiodns
import asyncio
import dns.resolver
import dns.reversename
from typing import Tuple, List, Optional
from config import settings
from database import get_db, get_db_write_lock

# Cache DNSResolver per event loop to avoid loop mismatch errors
_resolver_cache = {}

def get_resolver():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return aiodns.DNSResolver(
            nameservers=settings.DNS_RESOLVERS,
            timeout=5,
            tries=2
        )
    
    if loop not in _resolver_cache:
        _resolver_cache[loop] = aiodns.DNSResolver(
            nameservers=settings.DNS_RESOLVERS,
            timeout=5,
            tries=2,
            loop=loop
        )
    return _resolver_cache[loop]

async def resolve_domain(domain: str) -> bool:
    """Check if the domain resolves to any A or AAAA records."""
    resolver = get_resolver()
    try:
        # Check A record
        await asyncio.wait_for(
            resolver.query(domain, 'A'),
            timeout=settings.DNS_LOOKUP_TIMEOUT
        )
        return True
    except (asyncio.TimeoutError, aiodns.error.DNSError):
        pass
    
    try:
        # Check AAAA record
        await asyncio.wait_for(
            resolver.query(domain, 'AAAA'),
            timeout=settings.DNS_LOOKUP_TIMEOUT
        )
        return True
    except (asyncio.TimeoutError, aiodns.error.DNSError):
        return False

async def lookup_mx(domain: str) -> Tuple[bool, List[str]]:
    """Lookup MX records for a domain and return them sorted by priority."""
    resolver = get_resolver()
    try:
        answers = await asyncio.wait_for(
            resolver.query(domain, 'MX'),
            timeout=settings.DNS_LOOKUP_TIMEOUT
        )
        # Sort by priority (lowest integer value is highest priority)
        mx_records = sorted(answers, key=lambda r: r.priority)
        return True, [r.host for r in mx_records]
    except (asyncio.TimeoutError, aiodns.error.DNSError, Exception):
        return False, []

async def check_domain(domain: str) -> Tuple[str, str]:
    """
    Check if a domain exists and has MX records.
    Returns (status, reason)
    """
    has_mx, mx_records = await lookup_mx(domain)
    if has_mx and mx_records:
        return "valid", ",".join(mx_records)
    
    # If no MX, check if domain resolves at all to provide better error
    resolves = await resolve_domain(domain)
    if resolves:
        return "invalid", "no_mx_record"
    
    return "invalid", "domain_not_found"

async def detect_domain_type(domain: str) -> str:
    db = get_db()
    try:
        row = db.execute(
            "SELECT server_type FROM domain_intelligence "
            "WHERE domain = ? AND server_type IS NOT NULL AND server_type != 'unknown' "
            f"AND (epoch(CURRENT_TIMESTAMP) - epoch(last_checked)) < {settings.DOMAIN_INTELLIGENCE_TTL}",
            [domain]
        ).fetchone()
        if row:
            return row[0]
    except Exception:
        pass
        
    has_mx, mx_records = await lookup_mx(domain)
    server_type = "postfix_other"
    
    if has_mx and mx_records:
        mx_str = ",".join(mx_records).lower()
        if "protection.outlook.com" in mx_str or "eo.outlook.com" in mx_str:
            server_type = "exchange_online"
        elif "pphosted.com" in mx_str or "mimecast.com" in mx_str or "barracudanetworks.com" in mx_str or "proofpoint.com" in mx_str:
            server_type = "gateway"
        elif "google.com" in mx_str or "googlemail.com" in mx_str or "aspmx.l.google.com" in mx_str:
            server_type = "google_workspace"
        elif domain in mx_str:
            server_type = "exchange_onprem"

    async with get_db_write_lock():
        db.execute(
            "INSERT INTO domain_intelligence (domain, server_type, last_checked) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(domain) DO UPDATE SET server_type = excluded.server_type, last_checked = excluded.last_checked",
            [domain, server_type]
        )
        
    return server_type

async def prefetch_domain_types(domains: list[str]) -> dict[str, str]:
    sem = asyncio.Semaphore(settings.DNS_MAX_CONCURRENT_PREFETCH)
    
    async def _detect_one(domain: str) -> Tuple[str, str]:
        async with sem:
            dtype = await detect_domain_type(domain)
            return domain, dtype
            
    results = await asyncio.gather(
        *[_detect_one(d) for d in domains],
        return_exceptions=True
    )
    
    return {
        domain: dtype
        for domain, dtype in results
        if not isinstance(dtype, Exception)
    }
async def resolve_mx_ip(hostname: str) -> Optional[str]:
    """
    Resolve an MX hostname to its first A record IP address.
    Uses dnspython in a separate thread for Windows reliability.
    """
    if not hostname:
        return None
        
    def _sync_a_lookup():
        try:
            res = dns.resolver.Resolver()
            res.timeout = settings.DNS_LOOKUP_TIMEOUT
            res.lifetime = settings.DNS_LOOKUP_TIMEOUT
            if settings.DNS_RESOLVERS:
                res.nameservers = settings.DNS_RESOLVERS
                
            answers = res.resolve(hostname, "A")
            if answers:
                return str(answers[0])
        except Exception:
            pass
        return None

    return await asyncio.to_thread(_sync_a_lookup)

async def get_ptr_record(ip_address: str) -> Optional[str]:
    """
    Perform a reverse DNS lookup (PTR) for an IP address.
    Uses dnspython in a separate thread to avoid blocking.
    """
    if not ip_address:
        return None
        
    def _sync_ptr_lookup():
        try:
            rev_name = dns.reversename.from_address(ip_address)
            # Use default system resolver for PTR or a specific one if needed
            # For simplicity and robustness, we use a fresh resolver instance
            res = dns.resolver.Resolver()
            res.timeout = settings.DNS_LOOKUP_TIMEOUT
            res.lifetime = settings.DNS_LOOKUP_TIMEOUT
            if settings.DNS_RESOLVERS:
                res.nameservers = settings.DNS_RESOLVERS
                
            answers = res.resolve(rev_name, "PTR")
            if answers:
                return str(answers[0].target).rstrip('.')
        except Exception:
            pass
        return None

    return await asyncio.to_thread(_sync_ptr_lookup)
