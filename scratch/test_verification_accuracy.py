import asyncio
import sys
import os

# Add backend directory to sys.path
backend_dir = r"c:\Users\CW250413\Desktop\lattest\Emailverify\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from engine import verify_single_email
from dns_checks import resolve_domain_detail, check_domain
from smtp_verifier import map_smtp_response

async def run_test_suite():
    print("=" * 70)
    print("RUNNING VERIFICATION ACCURACY TEST SUITE")
    print("=" * 70)

    # Unit Test 1: SMTP Mapping - Ensure 220/221 are NEVER deliverable
    st1, r1 = map_smtp_response(220, "220 mx.google.com ESMTP")
    assert st1 != "Deliverable", f"FAIL: 220 greeting mapped to {st1}"
    print("[PASS] Unit Test 1: 220 greeting is NOT mapped to Deliverable")

    st2, r2 = map_smtp_response(221, "221 2.0.0 Bye")
    assert st2 != "Deliverable", f"FAIL: 221 closing mapped to {st2}"
    print("[PASS] Unit Test 2: 221 closing is NOT mapped to Deliverable")

    # Unit Test 2: 550 Anti-spam block is Protected, NOT Undeliverable
    st3, r3 = map_smtp_response(550, "550 5.7.1 Blocked by Spamhaus RBL")
    assert st3 == "Protected", f"FAIL: 550 Spamhaus mapped to {st3}"
    print("[PASS] Unit Test 3: 550 anti-spam block is mapped to Protected (UNKNOWN)")

    # Test Emails
    test_cases = [
        ("invalid..syntax@gmail.com", "Syntax Invalid"),
        ("nonexistent_user_9871239847@gmail.com", "Explicit Recipient Rejection (INVALID)"),
        ("user@nonexistentdomain98123749.com", "NXDOMAIN (INVALID)"),
        ("info@gmail.com", "Role-Based / Protected"),
        ("support@dispostable.com", "Disposable / Role")
    ]

    results_summary = {
        "valid": 0,
        "invalid": 0,
        "unknown": 0,
        "catch_all": 0,
        "disposable": 0,
        "role_based": 0
    }

    print("\n--- LIVE VERIFICATION ENGINE TESTS ---")
    for email, desc in test_cases:
        try:
            res = await verify_single_email(email)
            st = res.get("status")
            det = res.get("detailed_status")
            conf = res.get("confidence")
            reason = res.get("reason")
            results_summary[st] = results_summary.get(st, 0) + 1
            print(f"Email: {email:<40} | Status: {st:<10} | Detailed: {det:<15} | Conf: {conf:<4} | Reason: {reason}")
        except Exception as e:
            print(f"Email: {email:<40} | ERROR: {e}")

    print("\n--- SUMMARY OF RESULTS ---")
    for k, v in results_summary.items():
        print(f"  {k.upper()}: {v}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_test_suite())
