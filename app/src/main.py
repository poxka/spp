from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import select

import src.models
from src.config import settings
from src.database import Base, SessionLocal, engine
from src.logging_config import configure_logging, get_logger
from src.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from src.ratelimit import limiter
from src.routers import auth, health, transactions
from src.security.password import hash_password


logger = get_logger("app")


async def _init_local_db() -> None:
    from src.models.user import User

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if not (settings.seed_user and settings.seed_password):
        return

    async with SessionLocal() as session:
        existing = await session.execute(
            select(User).where(User.username == settings.seed_user)
        )
        if existing.scalar_one_or_none() is None:
            session.add(
                User(
                    username=settings.seed_user,
                    hashed_password=hash_password(settings.seed_password),
                )
            )
            await session.commit()
            logger.info("seed_user_created", username=settings.seed_user)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    if settings.environment == "local":
        await _init_local_db()
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SecurePay API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],        # DEMO VULN: any origin
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(transactions.router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
