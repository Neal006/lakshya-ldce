import pytest


class TestAuthServiceUnit:
    def test_hash_password_and_verify(self):
        from app.services.auth import hash_password, verify_password
        hashed = hash_password("Password123")
        assert verify_password("Password123", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_create_and_decode_access_token(self):
        from app.services.auth import create_access_token, decode_token
        token = create_access_token("user-123", "admin")
        payload = decode_token(token, "access")
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        from app.services.auth import create_refresh_token, decode_token
        token = create_refresh_token("user-123", "qa")
        payload = decode_token(token, "refresh")
        assert payload["sub"] == "user-123"
        assert payload["role"] == "qa"
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_access_token_cannot_be_used_as_refresh(self):
        from app.services.auth import create_access_token, decode_token
        token = create_access_token("user-123", "admin")
        try:
            decode_token(token, "refresh")
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert e.status_code == 401

    def test_refresh_token_cannot_be_used_as_access(self):
        from app.services.auth import create_refresh_token, decode_token
        token = create_refresh_token("user-123", "admin")
        try:
            decode_token(token, "access")
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert e.status_code == 401

    def test_invalid_token_raises_401(self):
        from app.services.auth import decode_token
        try:
            decode_token("invalid.jwt.token", "access")
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert e.status_code == 401

    def test_refresh_token_rotation(self):
        from app.services.auth import (
            create_refresh_token, verify_refresh_token,
            revoke_refresh_token,
        )
        rt1 = create_refresh_token("user-1", "admin")
        verify_refresh_token(rt1)

        revoke_refresh_token(rt1)

        try:
            verify_refresh_token(rt1)
            assert False, "Revoked token should raise"
        except Exception:
            pass

        rt2 = create_refresh_token("user-1", "admin")
        verify_refresh_token(rt2)

        try:
            verify_refresh_token(rt1)
            assert False, "Old token should still be revoked"
        except Exception:
            pass

    def test_multiple_refresh_tokens_not_collision(self):
        from app.services.auth import create_refresh_token, verify_refresh_token
        rt1 = create_refresh_token("user-1", "admin")
        rt2 = create_refresh_token("user-1", "admin")
        assert rt1 != rt2
        verify_refresh_token(rt1)
        verify_refresh_token(rt2)


class TestPasswordValidation:
    def test_valid_password_accepted(self, client):
        resp = client.post("/auth/register", json={
            "email": "validpass@example.com",
            "password": "ValidPass123",
            "name": "Valid Pass User",
        })
        assert resp.status_code == 201

    def test_password_too_short(self, client):
        resp = client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "Sh1",
            "name": "Short Pass",
        })
        assert resp.status_code == 422

    def test_password_no_lowercase(self, client):
        resp = client.post("/auth/register", json={
            "email": "nolower@example.com",
            "password": "ALLUPPER123",
            "name": "No Lower",
        })
        assert resp.status_code == 422

    def test_password_no_uppercase(self, client):
        resp = client.post("/auth/register", json={
            "email": "noupper@example.com",
            "password": "alllower123",
            "name": "No Upper",
        })
        assert resp.status_code == 422

    def test_password_no_digit(self, client):
        resp = client.post("/auth/register", json={
            "email": "nodigit@example.com",
            "password": "NoDigitsHere",
            "name": "No Digit",
        })
        assert resp.status_code == 422

    def test_password_exactly_8_chars_valid(self, client):
        resp = client.post("/auth/register", json={
            "email": "eightchar@example.com",
            "password": "Pass1234",
            "name": "Eight Char",
        })
        assert resp.status_code == 201


class TestProtectedRoutes:
    def test_no_authorization_header_returns_403(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 403

    def test_invalid_bearer_token_returns_401(self, client):
        resp = client.post("/auth/logout", headers={
            "Authorization": "Bearer not.a.real.token",
        })
        assert resp.status_code == 401

    def test_valid_token_accesses_protected_route(self, client, auth_headers):
        resp = client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200


class TestEndToEndAuthFlow:
    def test_full_auth_flow(self, client):
        resp_register = client.post("/auth/register", json={
            "email": "e2e@example.com",
            "password": "Password123",
            "name": "E2E User",
            "role": "call_attender",
        })
        assert resp_register.status_code == 201
        register_data = resp_register.json()["data"]
        access_token = register_data["access_token"]
        refresh_token = register_data["refresh_token"]

        resp_login = client.post("/auth/login", json={
            "email": "e2e@example.com",
            "password": "Password123",
        })
        assert resp_login.status_code == 200
        login_data = resp_login.json()["data"]
        assert login_data["user"]["email"] == "e2e@example.com"

        resp_refresh = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp_refresh.status_code == 200
        new_rt = resp_refresh.json()["data"]["refresh_token"]
        new_at = resp_refresh.json()["data"]["access_token"]

        resp_old_refresh = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp_old_refresh.status_code == 401

        resp_new_refresh = client.post("/auth/refresh", json={
            "refresh_token": new_rt,
        })
        assert resp_new_refresh.status_code == 200

        resp_logout = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {new_at}",
        })
        assert resp_logout.status_code == 200