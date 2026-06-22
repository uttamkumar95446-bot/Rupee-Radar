"""Full pipeline integration test using FastAPI TestClient.

Tests: health -> upload -> poll -> categorization -> recurring -> overrides.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    print("  [PASS] Health check v" + data["version"])


def test_upload():
    csv_path = os.path.join(os.path.dirname(__file__), "seed_data", "sample_transactions.csv")
    with open(csv_path, "rb") as f:
        response = client.post("/api/upload", files={"file": ("sample.csv", f, "text/csv")})
    assert response.status_code == 202, str(response.json())
    data = response.json()
    assert data["status"] == "processing"
    assert "job_id" in data
    print("  [PASS] Upload: job_id=" + data["job_id"])
    return data["job_id"]


def poll_analysis(job_id, max_retries=15):
    for attempt in range(max_retries):
        response = client.get("/api/analysis/" + job_id)
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            print("  [PASS] Analysis completed (poll " + str(attempt + 1) + ")")
            return data["data"]
        elif data["status"] == "failed":
            raise AssertionError("Analysis failed: " + data.get("error", "Unknown"))
        time.sleep(1)
    raise TimeoutError("Analysis did not complete after " + str(max_retries) + "s")


def print_results(analysis):
    txns = analysis["transactions"]
    metrics = analysis["metrics"]
    recurring = analysis.get("recurring_payments", [])

    print("  Transactions: " + str(len(txns)))
    print("  Income: " + str(metrics["total_income"]))
    print("  Spend: " + str(metrics["total_spend"]))
    print("  Savings: " + str(metrics["savings"]))

    # Math check
    calc = metrics["total_income"] - metrics["total_spend"]
    assert abs(calc - metrics["savings"]) < 0.01
    print("  [PASS] Math verified")

    # Categories
    cats = {}
    for t in txns:
        c = t.get("category", "Other")
        cats[c] = cats.get(c, 0) + 1
    print("  Categories (" + str(len(cats)) + "):")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print("    " + c + ": " + str(n))

    # Recurring
    flagged = sum(1 for t in txns if t.get("is_recurring"))
    print("  Recurring patterns: " + str(len(recurring)))
    for r in recurring:
        print("    " + r["merchant"] + ": " + str(r["amount"]) + "/" + r["frequency"] + " (" + r["r_type"] + ")")
    print("  Flagged recurring: " + str(flagged))


def test_override_category(job_id, analysis):
    txn_id = analysis["transactions"][0]["id"]
    old_cat = analysis["transactions"][0]["category"]
    response = client.put("/api/analysis/" + job_id + "/transactions/" + txn_id + "/category", params={"category": "Food"})
    assert response.status_code == 200, str(response.json())
    print("  [PASS] Category override: " + old_cat + " -> Food")


def test_override_recurring(job_id, analysis):
    txn_id = analysis["transactions"][0]["id"]
    response = client.put("/api/analysis/" + job_id + "/transactions/" + txn_id + "/recurring",
                          params={"is_recurring": True, "recurring_type": "subscription"})
    assert response.status_code == 200, str(response.json())
    print("  [PASS] Recurring override: set to subscription")


def main():
    print("=" * 55)
    print("  RupeeRadar - Full Pipeline Integration Test")
    print("=" * 55)
    print()

    print("1. Health Check")
    test_health()
    print()

    print("2. Upload CSV")
    job_id = test_upload()
    print()

    print("3. Analysis Results")
    analysis = poll_analysis(job_id)
    print()

    print("4. Pipeline Results")
    print_results(analysis)
    print()

    print("5. Category Override")
    test_override_category(job_id, analysis)
    print()

    print("6. Recurring Override")
    test_override_recurring(job_id, analysis)
    print()

    print("7. Verify Overrides Persisted")
    updated = poll_analysis(job_id)
    txn = updated["transactions"][0]
    assert txn["category"] == "Food", "Category not persisted: " + txn["category"]
    assert txn["is_recurring"] == True, "Recurring flag not persisted"
    print("  [PASS] Overrides persisted correctly")
    print()

    print("=" * 55)
    print("  ALL PIPELINE TESTS PASSED!")
    print("=" * 55)


if __name__ == "__main__":
    main()
