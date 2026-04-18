import pytest


class TestRefreshHappyPath:
    def test_refresh_returns_200(self, client, auth_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert resp.status_code == 200

    def test_refresh_returns_new_access_token(self, client, auth_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert "access_token" in resp.json()["data"]

    def test_refresh_returns_new_refresh_token(self, client, auth_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert "refresh_token" in resp.json()["data"]

    def test_refresh_new_tokens_are_different(self, client, auth_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        new_data = resp.json()["data"]
        assert new_data["access_token"] != auth_tokens["access_token"]
        assert new_data["refresh_token"] != auth_tokens["refresh_token"]

    def test_refresh_rotation_old_token_revoked(self, client, auth_tokens):
        client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert resp.status_code == 401

    def test_refresh_rotation_old_token_error_code(self, client, auth_tokens):
        client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    def test_refresh_new_token_is_usable(self, client, auth_tokens):
        resp1 = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"],
        })
        new_rt = resp1.json()["data"]["refresh_token"]
        resp2 = client.post("/auth/refresh", json={
            "refresh_token": new_rt,
        })
        assert resp2.status_code == 200


class TestRefreshFailureModes:
    def test_invalid_refresh_token_returns_401(self, client):
        resp = client.post("/auth/refresh", json={
            "refresh_token": "invalid.jwt.token",
        })
        assert resp.status_code == 401

    def test_invalid_refresh_token_error_code(self, client):
        resp = client.post("/auth/refresh", json={
            "refresh_token": "invalid.jwt.token",
        })
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    def test_access_token_as_refresh_returns_401(self, client, auth_tokens):
        resp = client.post("/auth/refresh", json={
            "refresh_token": auth_tokens["access_token"],
        })
        assert resp.status_code == 401

    def test_empty_body_returns_422(self, client):
        resp = client.post("/auth/refresh", json={})
        assert resp.status_code == 422

    def test_error_format_matches_contract(self, client):
        resp = client.post("/auth/refresh", json={
            "refresh_token": "invalid.jwt.token",
        })
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]