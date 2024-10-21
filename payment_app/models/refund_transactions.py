"""Module for payment entities."""
from typing import Optional
from pydantic import condecimal
from sqlmodel import Relationship, SQLModel, Field, JSON
from typing_extensions import Annotated
import ulid
from sqlalchemy import Column

from payment_app.models import Transaction, TimeStampMixin

class RefundTransactionBase(SQLModel):
    """Base model for refund transactions."""
    transaction_id: str = Field(default=None, foreign_key="transactions.id")
    refund_id: str = Field(nullable=True, max_length=100, index=True, sa_column=Column(unique=True))
    api_request: dict = Field(sa_column=Column(JSON))
    api_response: dict = Field(sa_column=Column(JSON))
    api_status: int = Field(nullable=True)
    callback_response: dict = Field(sa_column=Column(JSON))
    status: str = Field(max_length=10, default="pending")
    amount: condecimal(decimal_places=2) = Field(default=0)
    additional_info: dict = Field(sa_column=Column(JSON))


class RefundTransaction(RefundTransactionBase, TimeStampMixin, table=True):
    """Refund transaction entity."""
    __tablename__ = "refund_transactions"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    transaction: Optional[Transaction] = Relationship(
        back_populates="refund_transaction"
    )
