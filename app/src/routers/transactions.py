import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_user
from src.logging_config import get_logger
from src.models.user import User
from src.schemas.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionResponse,
)
from src.services import transaction_service


router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = get_logger("transactions")


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    transaction = await transaction_service.create_transaction(
        db, current_user.id, payload
    )
    logger.info(
        "transaction_created",
        transaction_id=str(transaction.id),
        currency=transaction.currency,
    )

    return TransactionResponse.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    transaction = await transaction_service.get_transaction(
        db, current_user.id, transaction_id
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return TransactionResponse.model_validate(transaction)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    currency: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    min_amount: float | None = Query(default=None, gt=0),
    max_amount: float | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TransactionResponse]:
    filters = TransactionFilter(
        currency=currency,
        status=status_filter,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit,
        offset=offset,
    )
    transactions = await transaction_service.list_transactions(
        db, current_user.id, filters
    )

    return [TransactionResponse.model_validate(t) for t in transactions]
