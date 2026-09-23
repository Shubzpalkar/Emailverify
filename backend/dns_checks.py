import aiodns
import asyncio
import time
import logging
from typing import Tuple, List, Optional, Dict, Any
import dns.resolver
import dns.asyncresolver
import dns.reversename

from config import settings
from database import get_db, get_db_write_lock
from provider_engine import provider_engine

logger = logging.getLogger("verification_engine.dns")

# Default Enterprise Public Resolvers Pool
DEFAULT_RESOLVER_POOL = [
    "1.1.1.1",       # Cloudflare Primary
    "1.0.0.1",       # Cloudflare Secondary
    "8.8.8.8",       # Google Primary
    "8.8.4.4",       # Google Secondary
    "9.9.9.9",       # Quad9 Primary
    "149.112.112.112", # Quad9 Secondary
    "208.67.222.222",# OpenDNS Primary
    "208.67.220.220" # OpenDNS Secondary
]

class ResolverHealth:
    def __init__(self, ip: str):
        self.ip = ip
        self.latency_ms = 10.0
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.consecutive_failures = 0
        self.health_score = 1.0  # Range 0.0 to 1.0
        self.is_healthy = True

    def record_success(self, latency_ms: float):
        self.success_count += 1
        self.consecutive_failures = 0
        # Exponential moving average for smooth latency measurement
        self.latency_ms = (0.7 * self.latency_ms) + (0.3 * latency_ms)
        self.health_score = min(1.0, self.health_score + 0.05)
        self.is_healthy = True

    def record_failure(self, is_timeout: bool = False):
        self.failure_count += 1
        self.consecutive_failures += 1
        if is_timeout:
            self.timeout_count += 1
            self.health_score -= 0.3
        else:
            self.health_score -= 0.2

        self.health_score = max(0.0, self.health_score)
        if self.consecutive_failures >= 3 or self.health_score < 0.3:
            if self.is_healthy:
                logger.warning(f"[DNS Health Monitor] Disabling unhealthy resolver {self.ip} (Score: {self.health_score:.2f}, Consecutive Failures: {self.consecutive_failures})")
            self.is_healthy = False

class DNSHealthMonitor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DNSHealthMonitor, cls).__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        resolvers = list(dict.fromkeys((settings.DNS_RESOLVERS or []) + DEFAULT_RESOLVER_POOL))
        self.health_map: Dict[str, ResolverHealth] = {ip: ResolverHealth(ip) for ip in resolvers}
        self.current_index = 0

    def get_healthy_resolvers(self) -> List[str]:
        healthy = [ip for ip, h in self.health_map.items() if h.is_healthy]
        if not healthy:
            # Fallback to all if none healthy to avoid total blackout
            return list(self.health_map.keys())
        # Sort healthy resolvers by latency (fastest first)
        return sorted(healthy, key=lambda ip: self.health_map[ip].latency_ms)

    def get_best_resolver_ip(self) -> str:
        healthy = self.get_healthy_resolvers()
        return healthy[0] if healthy else "1.1.1.1"

    def record_result(self, resolver_ip: str, success: bool, latency_ms: float = 0.0, is_timeout: bool = False):
        if resolver_ip in self.health_map:
            health = self.health_map[resolver_ip]
            if success:
                health.record_success(latency_ms)
            else:
                health.record_failure(is_timeout)

    def get_metrics_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "ip": ip,
                "health_score": round(h.health_score, 2),
                "is_healthy": h.is_healthy,
                "latency_ms": round(h.latency_ms, 1),
                "success_count": h.success_count,
                "failure_count": h.failure_count,
                "consecutive_failures": h.consecutive_failures
            }
            for ip, h in self.health_map.items()
        ]

dns_health_monitor = DNSHealthMonitor()

# Cache aiodns resolvers per event loop
_aiodns_cache = {}
_dns_memory_cache: Dict[str, Dict[str, Any]] = {}

def get_aiodns_resolver():
    healthy_ips = dns_health_monitor.get_healthy_resolvers()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return aiodns.DNSResolver(
            nameservers=healthy_ips,
            timeout=settings.DNS_LOOKUP_TIMEOUT,
            tries=2
        )
    
    if loop not in _aiodns_cache:
        _aiodns_cache[loop] = aiodns.DNSResolver(
            nameservers=healthy_ips,
            timeout=settings.DNS_LOOKUP_TIMEOUT,
            tries=2,
            loop=loop
        )
    else:
        _aiodns_cache[loop].nameservers = healthy_ips

    return _aiodns_cache[loop]

def classify_dns_exception(exc: Exception) -> Tuple[str, str, bool]:
    """
    Classify DNS exceptions into structured (dns_status, reason, is_retryable) tuples.
    Differentiates: NXDOMAIN, NoAnswer, Timeout, SERVFAIL, Resolver Failure, Network Error.
    """
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout", "DNS lookup timed out", True

    if isinstance(exc, dns.resolver.NXDOMAIN):
        return "nxdomain", "Domain does not exist (NXDOMAIN)", False
    if isinstance(exc, dns.resolver.NoAnswer):
        return "no_mx_server", "No MX records found for domain", False
    if isinstance(exc, dns.resolver.Timeout):
        return "timeout", "DNS lookup timed out", True
    if isinstance(exc, dns.resolver.NoNameservers):
        return "servfail", "No nameservers responded (SERVFAIL)", True

    msg = str(exc).lower()
    args = getattr(exc, 'args', ())
    code = args[0] if args and isinstance(args[0], int) else None

    if code == 4 or "not found" in msg or "nxdomain" in msg or "domain name not found" in msg:
        return "nxdomain", "Domain does not exist (NXDOMAIN)", False
    if code == 1 or "no data" in msg or "nodata" in msg:
        return "no_mx_server", "No MX records found for domain", False
    if code == 2 or "servfail" in msg or "server failure" in msg:
        return "servfail", "DNS server failure (SERVFAIL)", True
    if "timeout" in msg:
        return "timeout", "DNS server timeout", True
    if "refused" in msg or "query refused" in msg:
        return "resolver_failure", "DNS query refused by resolver", True
    if "connection refused" in msg or "network" in msg or "unreachable" in msg:
        return "network_error", "DNS network connection error", True

    return "temp_failure", f"Temporary DNS failure: {msg}", True

async def dual_dns_query_mx(domain: str) -> Tuple[List[str], str, float, Optional[Exception]]:
    """
    Dual DNS Resolution Flow:
    1. Try high-performance primary aiodns.
    2. On non-NXDOMAIN failure, try dnspython asyncresolver fallback.
    Returns (mx_records, used_resolver_ip, latency_ms, exception)
    """
    start = time.perf_counter()
    best_ip = dns_health_monitor.get_best_resolver_ip()

    # Step 1: Primary aiodns query
    try:
        resolver = get_aiodns_resolver()
        answers = await asyncio.wait_for(
            resolver.query(domain, 'MX'),
            timeout=settings.DNS_LOOKUP_TIMEOUT
        )
        latency = (time.perf_counter() - start) * 1000.0
        dns_health_monitor.record_result(best_ip, success=True, latency_ms=latency)
        mx_records = [r.host for r in sorted(answers, key=lambda r: r.priority)]
        return mx_records, best_ip, latency, None
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000.0
        is_timeout = isinstance(exc, asyncio.TimeoutError) or "timeout" in str(exc).lower()
        dns_health_monitor.record_result(best_ip, success=False, latency_ms=latency, is_timeout=is_timeout)
        
        status, _, retryable = classify_dns_exception(exc)
        if status == "nxdomain" or not retryable:
            return [], best_ip, latency, exc

    # Step 2: Dual DNS Fallback using dnspython asyncresolver
    fallback_start = time.perf_counter()
    fallback_ip = dns_health_monitor.get_healthy_resolvers()[-1] if len(dns_health_monitor.get_healthy_resolvers()) > 1 else best_ip
    try:
        async_res = dns.asyncresolver.Resolver()
        async_res.nameservers = [fallback_ip]
        async_res.lifetime = settings.DNS_LOOKUP_TIMEOUT
        answers = await async_res.resolve(domain, 'MX')
        latency = (time.perf_counter() - fallback_start) * 1000.0
        dns_health_monitor.record_result(fallback_ip, success=True, latency_ms=latency)
        mx_records = [str(r.exchange).rstrip('.') for r in sorted(answers, key=lambda r: r.preference)]
        return mx_records, fallback_ip, latency, None
    except Exception as exc:
        latency = (time.perf_counter() - fallback_start) * 1000.0
        is_timeout = isinstance(exc, dns.resolver.Timeout) or "timeout" in str(exc).lower()
        dns_health_monitor.record_result(fallback_ip, success=False, latency_ms=latency, is_timeout=is_timeout)
        return [], fallback_ip, latency, exc

async def resolve_domain_detail(domain: str) -> Dict[str, Any]:
    """
    Perform complete structured DNS check for a domain with smart retries.
    Returns structured dictionary:
    {
        "dns_status": "valid" | "no_mx_server" | "nxdomain" | "timeout" | "servfail" | "resolver_failure" | "network_error",
        "resolver": str,
        "reason": str,
        "latency_ms": float,
        "retryable": bool,
        "confidence": float,
        "mx_records": List[str],
        "has_a_record": bool
    }
    """
    domain = domain.strip().lower()
    if domain in _dns_memory_cache:
        return _dns_memory_cache[domain]

    backoff_delays = [0.5, 1.0, 2.0]  # Exponential backoff: 500ms, 1000ms, 2000ms
    last_exc = None
    used_ip = "1.1.1.1"
    last_latency = 0.0

    for attempt, delay in enumerate([0.0] + backoff_delays):
        if delay > 0:
            await asyncio.sleep(delay)

        mx_records, used_ip, last_latency, last_exc = await dual_dns_query_mx(domain)

        if not last_exc and mx_records:
            result = {
                "dns_status": "valid",
                "resolver": used_ip,
                "reason": "MX records resolved successfully",
                "latency_ms": round(last_latency, 2),
                "retryable": False,
                "confidence": 1.0,
                "mx_records": mx_records,
                "has_a_record": True
            }
            _dns_memory_cache[domain] = result
            return result

        status, reason, retryable = classify_dns_exception(last_exc) if last_exc else ("no_mx_server", "No MX records", False)

        # Do NOT retry NXDOMAIN or NoAnswer / No MX
        if not retryable or status in ("nxdomain", "no_mx_server"):
            break

    # If MX failed, check A/AAAA record fallback to distinguish No MX from NXDOMAIN
    has_a = False
    try:
        resolver = get_aiodns_resolver()
        await asyncio.wait_for(resolver.query(domain, 'A'), timeout=settings.DNS_LOOKUP_TIMEOUT)
        has_a = True
    except Exception:
        try:
            async_res = dns.asyncresolver.Resolver()
            async_res.lifetime = settings.DNS_LOOKUP_TIMEOUT
            await async_res.resolve(domain, 'AAAA')
            has_a = True
        except Exception:
            has_a = False

    status, reason, retryable = classify_dns_exception(last_exc) if last_exc else ("no_mx_server", "No MX records", False)

    if status == "no_mx_server" and has_a:
        result = {
            "dns_status": "no_mx_server",
            "resolver": used_ip,
            "reason": "Domain resolves A/AAAA but has no MX records",
            "latency_ms": round(last_latency, 2),
            "retryable": False,
            "confidence": 0.95,
            "mx_records": [],
            "has_a_record": True
        }
    elif status == "no_mx_server" and not has_a:
        result = {
            "dns_status": "nxdomain",
            "resolver": used_ip,
            "reason": "Domain does not exist or resolve (NXDOMAIN)",
            "latency_ms": round(last_latency, 2),
            "retryable": False,
            "confidence": 0.99,
            "mx_records": [],
            "has_a_record": False
        }
    else:
        result = {
            "dns_status": status,
            "resolver": used_ip,
            "reason": reason,
            "latency_ms": round(last_latency, 2),
            "retryable": retryable,
            "confidence": 0.50 if retryable else 0.95,
            "mx_records": [],
            "has_a_record": has_a
        }

    _dns_memory_cache[domain] = result
    return result

async def lookup_mx(domain: str) -> Tuple[bool, List[str]]:
    """Lookup MX records for a domain and return them sorted by priority."""
    detail = await resolve_domain_detail(domain)
    if detail["dns_status"] == "valid" and detail["mx_records"]:
        return True, detail["mx_records"]
    return False, []

async def resolve_domain(domain: str) -> bool:
    """Check if the domain resolves to any A or AAAA records."""
    detail = await resolve_domain_detail(domain)
    return detail.get("has_a_record", False) or detail["dns_status"] == "valid"

async def check_domain(domain: str) -> Tuple[str, str]:
    """
    Check if a domain exists and has MX records.
    Returns (status, reason) for backward compatibility.
    """
    detail = await resolve_domain_detail(domain)
    if detail["dns_status"] == "valid" and detail["mx_records"]:
        return "valid", ",".join(detail["mx_records"])
    
    if detail["dns_status"] == "no_mx_server":
        return "no_mx", "no_mx_record"
    
    if detail["dns_status"] == "nxdomain":
        return "invalid", "domain_not_found"

    return "unknown", detail["reason"]

def detect_provider_details(mx_records: List[str], domain: str) -> Tuple[str, str]:
    """
    Detect email service provider and provider type using ProviderEngine.
    Returns (provider_name, provider_type)
    """
    res = provider_engine.detect_provider(mx_records, banner="", domain=domain)
    return res["provider_name"], res["provider_type"]

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
    provider_name, provider_type = detect_provider_details(mx_records, domain)
    
    server_type_map = {
        "Microsoft 365": "exchange_online",
        "Google Workspace": "google_workspace",
        "Proofpoint": "gateway",
        "Mimecast": "gateway",
        "Cisco Secure Email": "gateway",
        "Barracuda": "gateway",
        "Trend Micro": "gateway",
        "Self-Hosted / Exchange On-Prem": "exchange_onprem"
    }
    server_type = server_type_map.get(provider_name, "postfix_other")

    try:
        async with get_db_write_lock():
            db.execute(
                "INSERT INTO domain_intelligence (domain, server_type, last_checked) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(domain) DO UPDATE SET server_type = excluded.server_type, last_checked = excluded.last_checked",
                [domain, server_type]
            )
    except Exception:
        pass
        
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
            healthy_ips = dns_health_monitor.get_healthy_resolvers()
            if healthy_ips:
                res.nameservers = healthy_ips
                
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
            res = dns.resolver.Resolver()
            res.timeout = settings.DNS_LOOKUP_TIMEOUT
            res.lifetime = settings.DNS_LOOKUP_TIMEOUT
            healthy_ips = dns_health_monitor.get_healthy_resolvers()
            if healthy_ips:
                res.nameservers = healthy_ips
                
            answers = res.resolve(rev_name, "PTR")
            if answers:
                return str(answers[0].target).rstrip('.')
        except Exception:
            pass
        return None

    return await asyncio.to_thread(_sync_ptr_lookup)
