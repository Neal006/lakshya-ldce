import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.services.auth import refresh_tokens_store

TEST_DATABASE_URL = "sqlite:///./test_ts14.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    from app.models import models as app_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_token_store():
    refresh_tokens_store.clear()
    yield
    refresh_tokens_store.clear()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def register_user(client):
    def _register(email="test@example.com", password="Password123", name="Test User", role="admin"):
        resp = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": role,
        })
        return resp
    return _register


@pytest.fixture
def auth_headers(client):
    resp = client.post("/auth/register", json={
        "email": "headers@example.com",
        "password": "Password123",
        "name": "Headers User",
        "role": "admin",
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_tokens(client, register_user):
    resp = register_user()
    data = resp.json()["data"]
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "user": data["user"],
    }