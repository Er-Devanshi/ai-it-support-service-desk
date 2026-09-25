"""
Phase 1 verification script.
Run with: python tests/verify_phase1.py
Requires the backend to be running on http://127.0.0.1:8000
"""

import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8000"

tests = [
    ("My Wi-Fi is not working",         "network",     "answered"),
    ("I need to reset my password",     "account",     "answered"),
    ("VPN is not connecting",           "network",     "answered"),
    ("My email is not syncing",         "email",       "answered"),
    ("The printer is not responding",   "hardware",    "answered"),
    ("I need to install software",      "software",    "answered"),
    ("My account is locked",            "account",     "answered"),
    ("My computer is very slow",        "performance", "answered"),
    ("MFA authenticator not working",   "security",    "answered"),
    ("I have no internet connectivity", "network",     "answered"),
    ("Something very unusual happened", "unknown",     "escalate"),
]


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())


def main():
    print("=" * 60)
    print("ServiceDesk-AI — Phase 1 Verification")
    print("=" * 60)

    # Health check
    health = json.loads(urllib.request.urlopen(BASE + "/api/health").read())
    print(f"\n[HEALTH] {health['status']} | {health['service']} | {health['phase']}")

    # Chat tests
    print("\n[CHAT TESTS]")
    failures = []
    for msg, exp_cat, exp_status in tests:
        r = post("/api/chat", {"message": msg})
        ok = r["category"] == exp_cat and r["status"] == exp_status
        symbol = "PASS" if ok else "FAIL"
        print(f"  [{symbol}] \"{msg[:45]}\"")
        print(f"         got  category={r['category']} status={r['status']}")
        if not ok:
            print(f"         want category={exp_cat} status={exp_status}")
            failures.append(msg)

    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        sys.exit(1)
    else:
        print(f"RESULT: ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    main()
