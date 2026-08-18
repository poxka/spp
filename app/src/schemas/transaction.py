import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from src.config import ALLOWED_CURRENCIES


Money = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]


class TransactionCreate(BaseModel):
    amount: Money
    currency: str
    card_token: uuid.UUID

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in ALLOWED_CURRENCIES:
            raise ValueError(
                f"currency must be one of {sorted(ALLOWED_CURRENCIES)}"
            )
        return normalized


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    currency: str
    card_token: uuid.UUID
    status: str
    created_at: datetime

    @field_serializer("amount")
    def _serialize_amount(self, value: Decimal) -> str:
        return format(value, "f")


class TransactionFilter(BaseModel):
    currency: str | None = None
    status: str | None = None
    min_amount: Money | None = None
    max_amount: Money | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    # @field_validator("currency")
    # @classmethod
    # def _normalize_currency(cls, value: str | None) -> str | None:
    #     if value is None:
    #         return None

    #     normalized = value.strip().upper()
    #     if normalized not in ALLOWED_CURRENCIES:
    #         raise ValueError(
    #             f"currency must be one of {sorted(ALLOWED_CURRENCIES)}"
    #         )
    #     return normalized
