import pytest

from app import data_access
from app.modules.authentication import authenticate_user, create_user, get_user
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-123")
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)


def create_account(client, email="admin@example.test", role="admin"):
    created, status = create_user({
        "name": "Test Account", "email": email,
        "password": "TestPass123", "role": role,
    })
    assert status == 201
    response = client.post("/auth/login", json={
        "email": email, "password": "TestPass123",
    })
    return created, {"Authorization": f"Bearer {response.json['access_token']}"}


def test_login_returns_public_user_and_token(client):
    create_user({"name": "Staff Member", "email": "staff@example.test",
                 "password": "TestPass123", "role": "staff"})

    response = client.post("/auth/login", json={
        "email": " STAFF@example.test ", "password": "TestPass123",
    })

    assert response.status_code == 200
    assert response.json["user"]["email"] == "staff@example.test"
    assert "password" not in response.json["user"]
    assert response.json["access_token"]


@pytest.mark.parametrize("payload", [None, {}, {"email": "x", "password": "bad"}])
def test_login_rejects_missing_or_invalid_credentials(client, payload):
    response = client.post("/auth/login", json=payload)
    assert response.status_code in {400, 401}


def test_admin_can_create_staff_account(client):
    _, admin_headers = create_account(client)

    response = client.post("/auth/users", headers=admin_headers, json={
        "name": "New Staff", "email": "new-staff@example.test",
        "password": "NewPass123", "role": "staff",
    })

    assert response.status_code == 201
    assert response.json["user"]["role"] == "staff"
    assert "password" not in response.json["user"]


def test_user_creation_requires_admin_and_valid_payload(client):
    _, staff_headers = create_account(client, "staff@example.test", "staff")
    forbidden = client.post("/auth/users", headers=staff_headers, json={
        "name": "New", "email": "new@example.test", "password": "password",
    })
    unauthorized = client.post("/auth/users", json={})
    admin_headers = create_account(client)[1]
    invalid = client.post("/auth/users", headers=admin_headers, json={"name": ""})

    assert forbidden.status_code == 403
    assert unauthorized.status_code == 401
    assert invalid.status_code == 400


def test_authentication_service_hashes_password_rejects_duplicate_and_fetches_user():
    user, status = create_user({
        "name": "Service User", "email": " SERVICE@example.test ",
        "password": "SecretPass123", "role": "staff",
    })
    found, auth_status = authenticate_user("service@example.test", "SecretPass123")
    failed, failed_status = authenticate_user("service@example.test", "incorrect")
    duplicate, duplicate_status = create_user({
        "name": "Duplicate", "email": "service@example.test",
        "password": "SecretPass123", "role": "staff",
    })

    assert status == 201
    assert user["password"] != "SecretPass123"
    assert auth_status == 200 and found["id"] == user["id"]
    assert failed_status == 401 and "error" in failed
    assert duplicate_status == 409 and "error" in duplicate
    assert get_user(str(user["id"]))["email"] == "service@example.test"
    assert get_user("invalid") is None
