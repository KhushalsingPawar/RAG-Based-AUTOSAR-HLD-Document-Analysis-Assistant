import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Online"
    assert "AUTOSAR" in data["title"]


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Healthy"
    assert "SQLite Connected" in data["database"]


def test_projects_unauthenticated():
    # Without token, must return 401 Unauthorized
    response = client.get("/api/projects")
    assert response.status_code == 401


def test_auth_and_user_data_isolation():
    # 1. Register User A
    user_a = f"usera_{uuid.uuid4().hex[:6]}"
    res_a = client.post("/api/auth/register", json={"username": user_a, "password": "password123", "full_name": "User Alpha"})
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. User A gets projects (auto-seeded personal workspace)
    p_res_a = client.get("/api/projects", headers=headers_a)
    assert p_res_a.status_code == 200
    projects_a = p_res_a.json()
    assert len(projects_a) >= 1
    proj_a_id = projects_a[0]["id"]

    # User A starts with 0 documents
    docs_a = client.get("/api/documents", headers=headers_a, params={"project_id": proj_a_id}).json()
    assert len(docs_a) == 0

    # 3. Register User B
    user_b = f"userb_{uuid.uuid4().hex[:6]}"
    res_b = client.post("/api/auth/register", json={"username": user_b, "password": "password123", "full_name": "User Beta"})
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B gets their own workspace
    p_res_b = client.get("/api/projects", headers=headers_b)
    assert p_res_b.status_code == 200
    projects_b = p_res_b.json()
    assert len(projects_b) >= 1
    proj_b_id = projects_b[0]["id"]
    assert proj_a_id != proj_b_id  # Workspaces are distinct

    # User B starts with 0 documents
    docs_b = client.get("/api/documents", headers=headers_b, params={"project_b": proj_b_id}).json()
    assert len(docs_b) == 0

    # User B cannot see User A's documents
    docs_b_attempt_a = client.get("/api/documents", headers=headers_b, params={"project_id": proj_a_id}).json()
    assert len(docs_b_attempt_a) == 0


def test_document_deletion():
    # 1. Register User
    username = f"userdel_{uuid.uuid4().hex[:6]}"
    res = client.post("/api/auth/register", json={"username": username, "password": "password123", "full_name": "Delete Tester"})
    assert res.status_code == 201
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get user's project
    p_res = client.get("/api/projects", headers=headers)
    proj_id = p_res.json()[0]["id"]

    # 3. Ingest sample document
    up_res = client.post(
        "/api/upload/sample",
        headers=headers,
        data={"sample_name": "Brake_System_HLD_v2.0.pdf", "project_id": proj_id, "version": "v1.0.0"},
    )
    assert up_res.status_code == 200
    doc_id = up_res.json()["document_id"]

    # Verify document is listed
    docs = client.get("/api/documents", headers=headers, params={"project_id": proj_id}).json()
    assert any(d["id"] == doc_id for d in docs)

    # 4. Another user cannot delete this document
    other_user = f"other_{uuid.uuid4().hex[:6]}"
    other_res = client.post("/api/auth/register", json={"username": other_user, "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_res.json()['access_token']}"}
    del_forbidden = client.delete(f"/api/documents/{doc_id}", headers=other_headers)
    assert del_forbidden.status_code == 404

    # 5. Owner deletes the document
    del_res = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted_id"] == doc_id

    # Verify document is no longer listed
    docs_after = client.get("/api/documents", headers=headers, params={"project_id": proj_id}).json()
    assert not any(d["id"] == doc_id for d in docs_after)

