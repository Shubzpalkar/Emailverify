import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def verify_email(email):
    url = f"{BASE_URL}/api/verify/accuracy_test"
    data = json.dumps({"email": email}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode('utf-8')}
    except Exception as e:
        return {"error": str(e)}

def run_tests():
    test_emails = [
        ("invalid..syntax@gmail.com", "Syntax Invalid"),
        ("nonexistent_user_9871239847@gmail.com", "Explicit Recipient Rejection"),
        ("user@nonexistentdomain98123749.com", "NXDOMAIN"),
        ("info@gmail.com", "Role Account"),
        ("support@dispostable.com", "Disposable Email")
    ]

    print("=" * 110, flush=True)
    print("LIVE VERIFICATION ENGINE ACCURACY RESULTS", flush=True)
    print("=" * 110, flush=True)
    
    summary = {}
    for email, desc in test_emails:
        print(f"Testing {email}...", flush=True)
        res = verify_email(email)
        st = res.get("status")
        det = res.get("detailed_status")
        conf = res.get("confidence")
        reason = res.get("reason")
        summary[st] = summary.get(st, 0) + 1
        print(f"Email: {email:<42} | Status: {str(st):<10} | Detailed: {str(det):<15} | Conf: {str(conf):<5} | Reason: {reason}", flush=True)

    print("\n" + "=" * 110, flush=True)
    print("SUMMARY OF VERIFICATION RESULTS:", flush=True)
    for k, v in summary.items():
        print(f"  {str(k).upper()}: {v}", flush=True)
    print("=" * 110, flush=True)

if __name__ == "__main__":
    run_tests()
