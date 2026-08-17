import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transaction import Transaction
from src.schemas.transaction import TransactionCreate, TransactionFilter


async def create_transaction(
    db: AsyncSession, owner_id: uuid.UUID, payload: TransactionCreate
) -> Transaction:
    transaction = Transaction(
        amount=payload.amount,
        currency=payload.currency,
        card_token=payload.card_token,
        owner_id=owner_id,
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(transaction)

    return transaction


async def get_transaction(
    db: AsyncSession, owner_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction | None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def list_transactions(
    db: AsyncSession, owner_id: uuid.UUID, filters: TransactionFilter
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.owner_id == owner_id)

    if filters.currency is not None:
        stmt = stmt.where(Transaction.currency == filters.currency)
    if filters.status is not None:
        stmt = stmt.where(Transaction.status == filters.status)
    if filters.min_amount is not None:
        stmt = stmt.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        stmt = stmt.where(Transaction.amount <= filters.max_amount)

    stmt = (
        stmt.order_by(Transaction.created_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )

    result = await db.execute(stmt)

    return list(result.scalars().all())
