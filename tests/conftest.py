"""
Pytest fixtures for ServiceDesk-AI.
Sets up an isolated SQLite in-memory test database using StaticPool.
No live external API calls are made during tests.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db.session import get_db
from app.models.orm import Base, User, UserRole
from app.services.auth_service import hash_password, create_access_token
from app.main import app

# Shared In-memory SQLite with StaticPool so all connections share tables
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Ensure test environment variables are set."""
    os.environ["DEMO_MODE"] = "true"
    os.environ["LLM_PROVIDER"] = "mock"
    settings.DEMO_MODE = True
    settings.LLM_PROVIDER = "mock"


@pytest.fixture
def db_session():
    """Create a fresh database schema for each test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        # Seed test users
        emp = User(
            username="test_employee",
            email="employee@test.com",
            hashed_password=hash_password("empPass123"),
            role=UserRole.EMPLOYEE,
        )
        agent = User(
            username="test_agent",
            email="agent@test.com",
            hashed_password=hash_password("agentPass123"),
            role=UserRole.SUPPORT_AGENT,
        )
        adm = User(
            username="test_admin",
            email="admin@test.com",
            hashed_password=hash_password("adminPass123"),
            role=UserRole.ADMIN,
        )
        db.add_all([emp, agent, adm])
        db.commit()
        db.refresh(emp)
        db.refresh(agent)
        db.refresh(adm)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def employee_user(db_session) -> User:
    return db_session.query(User).filter(User.username == "test_employee").first()


@pytest.fixture
def agent_user(db_session) -> User:
    return db_session.query(User).filter(User.username == "test_agent").first()


@pytest.fixture
def admin_user(db_session) -> User:
    return db_session.query(User).filter(User.username == "test_admin").first()


@pytest.fixture
def employee_headers(employee_user) -> dict:
    token = create_access_token(employee_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def agent_headers(agent_user) -> dict:
    token = create_access_token(agent_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user) -> dict:
    token = create_access_token(admin_user)
    return {"Authorization": f"Bearer {token}"}
