from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=== TEAMMEMORYOS v5 DIRECT TESTCLIENT SUITE ===")
    
    # 1. Health
    r = client.get("/api/v1/workspace/health")
    print(f"1. GET /workspace/health -> Status: {r.status_code}, Data: {r.json()}")
    assert r.status_code == 200

    # 2. Activity
    r = client.get("/api/v1/workspace/activity")
    print(f"2. GET /workspace/activity -> Status: {r.status_code}, Count: {len(r.json().get('activities', []))}")
    assert r.status_code == 200

    # 3. Create Workspace
    r = client.post("/api/v1/workspace/create", json={"name": "SunBots Technologies", "repository_url": "github.com/sunbots/teammemoryos"})
    print(f"3. POST /workspace/create -> Status: {r.status_code}, Name: {r.json().get('name')}")
    assert r.status_code == 200

    # 4. Onboard Workspace
    r = client.post("/api/v1/workspace/onboard", json={"workspace_id": "test-id"})
    print(f"4. POST /workspace/onboard -> Status: {r.status_code}, Stages: {len(r.json().get('stages', []))}")
    assert r.status_code == 200

    # 5. AI Chat Query
    r = client.post("/api/v1/chat/query", json={"query": "How does authentication work?"})
    print(f"5. POST /chat/query -> Status: {r.status_code}, Title: {r.json().get('title')}, Evidence: {len(r.json().get('evidence', []))}")
    assert r.status_code == 200

    # 6. Timeline
    r = client.get("/api/v1/knowledge/timeline")
    print(f"6. GET /knowledge/timeline -> Status: {r.status_code}, Events: {len(r.json())}")
    assert r.status_code == 200

    # 7. Knowledge Graph
    r = client.get("/api/v1/knowledge/graph")
    print(f"7. GET /knowledge/graph -> Status: {r.status_code}, Nodes: {len(r.json().get('nodes', []))}, Edges: {len(r.json().get('edges', []))}")
    assert r.status_code == 200

    # 8. Incident Analyze
    r = client.post("/api/v1/incident/analyze", json={"crash_log": "FATAL: connection limit exceeded for non-superusers"})
    print(f"8. POST /incident/analyze -> Status: {r.status_code}, Classification: {r.json().get('classification')}, Match: {r.json().get('similar_incident_id')}")
    assert r.status_code == 200

    # 9. Incident Save
    r = client.post("/api/v1/incident/save", json={
        "title": "Resolved: PostgreSQL Pool Exhaustion",
        "classification": "PostgreSQL Pool Exhaustion",
        "root_cause": "Connection pool starvation under concurrency load",
        "solution": "Set pool_size=50 and max_overflow=20",
        "services_affected": ["PostgreSQL Database", "Session Manager"]
    })
    print(f"9. POST /incident/save -> Status: {r.status_code}, New Health: {r.json().get('new_health_score')}%")
    assert r.status_code == 200

    # 10. PR Guardian Review
    r = client.post("/api/v1/guardian/review", json={
        "diff": "query = f\"SELECT * FROM users WHERE email = '{email}'\"\ndb.execute(query)",
        "pr_title": "PR #205: User Lookup",
        "author": "Devin"
    })
    print(f"10. POST /guardian/review -> Status: {r.status_code}, Verdict: {r.json().get('verdict')}, Risk: {r.json().get('risk_score')}/100")
    assert r.status_code == 200

    print("\n🎉 ALL 10 v5 ENDPOINTS TESTED AND 100% OPERATIONAL!")

if __name__ == "__main__":
    run_tests()
