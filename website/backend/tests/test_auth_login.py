import pytest


class TestLoginHappyPath:
    def test_login_returns_200(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert resp.status_code == 200

    def test_login_response_has_data_key(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert "data" in resp.json()

    def test_login_returns_user(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        user = resp.json()["data"]["user"]
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"

    def test_login_returns_access_token(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert "access_token" in resp.json()["data"]

    def test_login_returns_refresh_token(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert "refresh_token" in resp.json()["data"]

    def test_login_user_has_id(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert "id" in resp.json()["data"]["user"]

    def test_login_user_has_role(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert resp.json()["data"]["user"]["role"] == "admin"


class TestLoginFailureModes:
    def test_wrong_password_returns_401(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword1",
        })
        assert resp.status_code == 401

    def test_wrong_password_error_code(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword1",
        })
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_nonexistent_email_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123",
        })
        assert resp.status_code == 401

    def test_nonexistent_email_error_code(self, client):
        resp = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123",
        })
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_error_format_matches_contract(self, client, register_user):
        register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword1",
        })
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_login_does_not_leak_which_field_is_wrong(self, client, register_user):
        register_user()
        wrong_pass_resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword1",
        })
        wrong_email_resp = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123",
        })
        assert wrong_pass_resp.json()["error"]["code"] == wrong_email_resp.json()["error"]["code"]

    def test_empty_body_returns_422(self, client):
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 422