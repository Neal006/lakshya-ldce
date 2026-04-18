import pytest


class TestRegisterHappyPath:
    def test_register_returns_201(self, client, register_user):
        resp = register_user()
        assert resp.status_code == 201

    def test_register_response_has_data_key(self, client, register_user):
        resp = register_user()
        body = resp.json()
        assert "data" in body

    def test_register_response_has_user(self, client, register_user):
        resp = register_user()
        body = resp.json()
        assert "user" in body["data"]

    def test_register_user_has_id(self, client, register_user):
        resp = register_user()
        user = resp.json()["data"]["user"]
        assert "id" in user
        assert len(user["id"]) > 0

    def test_register_user_has_email(self, client, register_user):
        resp = register_user()
        user = resp.json()["data"]["user"]
        assert user["email"] == "test@example.com"

    def test_register_user_has_name(self, client, register_user):
        resp = register_user()
        user = resp.json()["data"]["user"]
        assert user["name"] == "Test User"

    def test_register_user_has_role(self, client, register_user):
        resp = register_user()
        user = resp.json()["data"]["user"]
        assert user["role"] == "admin"

    def test_register_user_has_created_at(self, client, register_user):
        resp = register_user()
        user = resp.json()["data"]["user"]
        assert "created_at" in user
        assert user["created_at"] is not None

    def test_register_returns_access_token(self, client, register_user):
        resp = register_user()
        data = resp.json()["data"]
        assert "access_token" in data
        assert len(data["access_token"]) > 0

    def test_register_returns_refresh_token(self, client, register_user):
        resp = register_user()
        data = resp.json()["data"]
        assert "refresh_token" in data
        assert len(data["refresh_token"]) > 0

    def test_register_password_not_exposed(self, client, register_user):
        resp = register_user()
        body_str = str(resp.json())
        assert "hashed_password" not in body_str
        assert "password" not in body_str or "Password123" not in body_str.replace("test@example.com", "")

    def test_register_each_role(self, client):
        for role in ["admin", "qa", "call_attender"]:
            resp = client.post("/auth/register", json={
                "email": f"{role}@example.com",
                "password": "Password123",
                "name": f"{role} User",
                "role": role,
            })
            assert resp.status_code == 201
            assert resp.json()["data"]["user"]["role"] == role

    def test_register_default_role_is_call_attender(self, client):
        resp = client.post("/auth/register", json={
            "email": "defaultrole@example.com",
            "password": "Password123",
            "name": "Default Role User",
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["user"]["role"] == "call_attender"


class TestRegisterFailureModes:
    def test_duplicate_email_returns_409(self, client, register_user):
        register_user()
        resp = register_user()
        assert resp.status_code == 409

    def test_duplicate_email_error_code(self, client, register_user):
        register_user()
        resp = register_user()
        body = resp.json()
        assert body["error"]["code"] == "EMAIL_TAKEN"

    def test_duplicate_email_error_format(self, client, register_user):
        register_user()
        resp = register_user()
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "Password123",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_short_password_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "short1",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_password_no_uppercase_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "noupper@example.com",
            "password": "alllowercase123",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_password_no_lowercase_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "nolower@example.com",
            "password": "ALLUPPERCASE123",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_password_no_digit_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "nodigit@example.com",
            "password": "NoDigitsHere",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_validation_error_format_matches_contract(self, client):
        resp = client.post("/auth/register", json={
            "email": "bad",
            "password": "short",
        })
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "message" in body["error"]
        assert "fields" in body["error"]

    def test_missing_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "password": "Password123",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "nopass@example.com",
            "name": "Test",
        })
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "noname@example.com",
            "password": "Password123",
        })
        assert resp.status_code == 422

    def test_empty_name_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "emptyname@example.com",
            "password": "Password123",
            "name": "",
        })
        assert resp.status_code == 422

    def test_invalid_role_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "badrole@example.com",
            "password": "Password123",
            "name": "Test",
            "role": "superadmin",
        })
        assert resp.status_code == 422

    def test_sql_injection_in_email_not_500(self, client):
        resp = client.post("/auth/register", json={
            "email": "'; DROP TABLE profiles; --@example.com",
            "password": "Password123",
            "name": "SQL Test",
        })
        assert resp.status_code != 500