"""
Integration test script testing all FastAPI endpoints against the trained Q-table.
Simulates real requests and asserts expected access-control decisions.
"""

import json
from fastapi.testclient import TestClient
from main import app, agent
from config import MODEL_PATH

client = TestClient(app)

# Ensure trained model is loaded
agent.load(MODEL_PATH)


def test_integration():
    print("=" * 70)
    print("RUNNING INTEGRATION VERIFICATION OF FASTAPI ENDPOINTS & RL POLICY")
    print("=" * 70)

    # 1. Health Endpoint
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print(f"[PASS] /health: status={health['status']}, model_loaded={health['model']['loaded']}")
    assert health["model"]["loaded"] is True

    # 2. Database Test Endpoint
    res = client.get("/db/test")
    assert res.status_code == 200
    db_res = res.json()
    print(f"[PASS] /db/test: connected={db_res['connected']}, status={db_res['status']}")

    # 3. Predict: Legitimate Routine Doctor Request
    payload_routine = {
        "user_id": "DR-SMITH-10",
        "patient_id": "PAT-402",
        "record_id": "REC-9912",
        "role": "DOCTOR",
        "department_match": True,
        "record_sensitivity": "MEDIUM",
        "request_time": "NORMAL_HOURS",
        "location": "INTERNAL_HOSPITAL",
        "request_frequency": "NORMAL",
        "emergency_status": False
    }
    res = client.post("/predict", json=payload_routine)
    assert res.status_code == 200
    data = res.json()
    print(f"[PASS] Routine Doctor Request Decision : {data['action']:<10} (Latency: {data['decision_time_ms']} ms)")
    print(f"    Explanation: {data['explanation']}")
    assert data["action"] == "ALLOW", f"Expected ALLOW for routine doctor, got {data['action']}"

    # 4. Predict: Emergency Access (Cross-Department, Off-Hours)
    payload_emergency = {
        "user_id": "DR-ER-CHIEF",
        "patient_id": "PAT-TRAUMA-9",
        "record_id": "REC-5510",
        "role": "DOCTOR",
        "department_match": False,  # Cross-dept trauma consult!
        "record_sensitivity": "HIGH",
        "request_time": "OFF_HOURS",
        "location": "INTERNAL_HOSPITAL",
        "request_frequency": "ELEVATED",
        "emergency_status": True   # CRITICAL EMERGENCY
    }
    res = client.post("/predict", json=payload_emergency)
    assert res.status_code == 200
    data = res.json()
    print(f"[PASS] Emergency Trauma Request Decision: {data['action']:<10} (Latency: {data['decision_time_ms']} ms)")
    print(f"    Explanation: {data['explanation']}")
    assert data["action"] == "ALLOW", f"Expected ALLOW in emergency, got {data['action']}"

    # 5. Predict: Simulated Stolen Credential (External Unknown IP, Off-Hours, High Sensitivity)
    payload_stolen = {
        "user_id": "DR-COMPROMISED",
        "patient_id": "PAT-VIP-1",
        "record_id": "REC-VIP-99",
        "role": "DOCTOR",
        "department_match": False,
        "record_sensitivity": "CRITICAL_VIP",
        "request_time": "OFF_HOURS",
        "location": "EXTERNAL_UNKNOWN",  # Suspicious external IP
        "request_frequency": "ELEVATED",
        "emergency_status": False
    }
    res = client.post("/predict", json=payload_stolen)
    assert res.status_code == 200
    data = res.json()
    print(f"[PASS] Stolen Credential Attack Decision: {data['action']:<10} (Latency: {data['decision_time_ms']} ms)")
    print(f"    Explanation: {data['explanation']}")
    assert data["action"] in ("DENY", "CHALLENGE"), f"Expected DENY or CHALLENGE for stolen credentials, got {data['action']}"

    # 6. Predict: Mass Scraping Attack (Burst High Frequency, External)
    payload_mass = {
        "user_id": "BOT-SCRAPER",
        "patient_id": "PAT-BULK-001",
        "record_id": "REC-BULK",
        "role": "STAFF",
        "department_match": False,
        "record_sensitivity": "HIGH",
        "request_time": "OFF_HOURS",
        "location": "EXTERNAL_UNKNOWN",
        "request_frequency": "BURST_HIGH",  # >20 queries/min
        "emergency_status": False
    }
    res = client.post("/predict", json=payload_mass)
    assert res.status_code == 200
    data = res.json()
    print(f"[PASS] Mass Exfiltration Attack Decision: {data['action']:<10} (Latency: {data['decision_time_ms']} ms)")
    print(f"    Explanation: {data['explanation']}")
    assert data["action"] in ("DENY", "CHALLENGE"), f"Expected DENY or CHALLENGE for mass access, got {data['action']}"

    # 7. Simulate Endpoint
    res = client.get("/simulate?scenario=EMERGENCY_ACCESS")
    assert res.status_code == 200
    sim = res.json()
    print(f"[PASS] /simulate?scenario=EMERGENCY_ACCESS -> Action: {sim['rl_decision']['action']}, Reward: {sim['rl_decision']['reward_awarded']}")

    # 8. Metrics Endpoint
    res = client.get("/metrics")
    assert res.status_code == 200
    metrics = res.json()
    print(f"[PASS] /metrics: attack_blocking_rate={metrics['data']['metrics']['attack_blocking_rate_pct']}%, legitimate_rate={metrics['data']['metrics']['legitimate_access_rate_pct']}%")

    print("=" * 70)
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_integration()
