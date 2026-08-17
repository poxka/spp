from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.security.password import hash_password, verify_password


_DUMMY_HASH = hash_password("timing-parity-placeholder")


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    stored_hash = user.hashed_password if user else _DUMMY_HASH
    password_ok = verify_password(password, stored_hash)

    if user is None or not user.is_active or not password_ok:
        return None

    return user
