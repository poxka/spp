import os


os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-secret-not-for-production-0123456789abcdef"
)
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:3000")


import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app
from src.models.user import User
from src.ratelimit import limiter
from src.security.password import hash_password


limiter.enabled = False

TEST_USERNAME = "demo-user"
TEST_PASSWORD = "demo-password-123"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        session.add(
            User(username=TEST_USERNAME, hashed_password=hash_password(TEST_PASSWORD))
        )
        await session.commit()

    async def _override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_headers(client):
    response = await client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
