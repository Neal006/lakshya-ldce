import pytest


class TestLogoutHappyPath:
    def test_logout_returns_200(self, client, auth_headers):
        resp = client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200

    def test_logout_returns_success_message(self, client, auth_headers):
        resp = client.post("/auth/logout", headers=auth_headers)
        body = resp.json()
        assert body["data"]["message"] == "Logged out successfully"

    def test_logout_with_refresh_token_revokes_it(self, client, auth_tokens, auth_headers):
        resp = client.post(
            "/auth/logout",
            headers=auth_headers,
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200

        refresh_resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert refresh_resp.status_code == 401


class TestLogoutFailureModes:
    def test_logout_without_token_returns_403(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 403

    def test_logout_with_invalid_token_returns_401(self, client):
        resp = client.post("/auth/logout", headers={
            "Authorization": "Bearer invalid.jwt.token",
        })
        assert resp.status_code == 401

    def test_logout_with_expired_token_returns_401(self, client):
        resp = client.post("/auth/logout", headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMiLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxfQ.invalid",
        })
        assert resp.status_code == 401