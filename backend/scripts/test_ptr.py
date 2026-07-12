import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dns_checks import get_ptr_record, resolve_mx_ip

async def test_ptr():
    print("--- Testing PTR Logic ---")
    
    # Test 1: Resolve a known MX record to IP
    mx_host = "aspmx.l.google.com"
    print(f"Resolving IP for {mx_host}...")
    ip = await resolve_mx_ip(mx_host)
    if ip:
        print(f"IP found: {ip}")
        # Test 2: Perform PTR lookup on that IP
        print(f"Performing PTR lookup for {ip}...")
        ptr = await get_ptr_record(ip)
        if ptr:
            print(f"PTR record found: {ptr}")
        else:
            print("No PTR record found.")
    else:
        print(f"Could not resolve IP for {mx_host}")

    # Test 3: Test with a known IP that has a PTR
    ip_with_ptr = "8.8.8.8" # dns.google
    print(f"\nTesting with {ip_with_ptr}...")
    ptr = await get_ptr_record(ip_with_ptr)
    print(f"PTR for {ip_with_ptr}: {ptr}")

    # Test 4: Test with a local IP (likely no PTR)
    local_ip = "127.0.0.1"
    print(f"\nTesting with {local_ip}...")
    ptr = await get_ptr_record(local_ip)
    print(f"PTR for {local_ip}: {ptr}")

if __name__ == "__main__":
    asyncio.run(test_ptr())
