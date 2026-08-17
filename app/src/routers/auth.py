from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.logging_config import get_logger
from src.ratelimit import limiter
from src.config import settings
from src.schemas.auth import LoginRequest, TokenResponse
from src.security.jwt import create_access_token
from src.services.auth_service import authenticate_user


router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth")


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, payload.username, payload.password)
    if user is None:
        logger.warning("login_failed", username=payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, expires_in = create_access_token(str(user.id))
    logger.info("login_succeeded", user_id=str(user.id))

    return TokenResponse(access_token=token, expires_in=expires_in)
