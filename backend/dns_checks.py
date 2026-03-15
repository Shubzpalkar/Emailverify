import aiodns
import asyncio
from typing import Tuple, List

# Use robust public DNS resolvers
resolver = aiodns.DNSResolver(nameservers=['8.8.8.8', '1.1.1.1'])

async def resolve_domain(domain: str) -> bool:
    """Check if the domain resolves to any A or AAAA records."""
    try:
        # Check A record
        await resolver.query(domain, 'A')
        return True
    except aiodns.error.DNSError:
        pass
    
    try:
        # Check AAAA record
        await resolver.query(domain, 'AAAA')
        return True
    except aiodns.error.DNSError:
        return False

async def lookup_mx(domain: str) -> Tuple[bool, List[str]]:
    """Lookup MX records for a domain and return them sorted by priority."""
    try:
        answers = await resolver.query(domain, 'MX')
        # Sort by priority (lowest integer value is highest priority)
        mx_records = sorted(answers, key=lambda r: r.priority)
        return True, [r.host for r in mx_records]
    except (aiodns.error.DNSError, Exception):
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
