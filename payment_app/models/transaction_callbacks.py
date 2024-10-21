"""Module for payment entities."""
from typing import Final
from sqlalchemy import Column
from sqlmodel import JSON, SQLModel, Field
from payment_app.models.timestampsmixin import TimeStampMixin

CALLBACK_ORDER: Final = "payment"
CALLBACK_REFUND: Final = "refund"


class TransactionCallbacksBase(SQLModel):
    """
    Transaction callback base model.
    To store all callbacks to the payment gateway.
    """
    transaction_id: str = Field(nullable=True, foreign_key="transactions.id")
    callback: dict = Field(sa_column=Column(JSON))
    event: str = Field(nullable=True)
    type: str = Field(nullable=True, default=CALLBACK_ORDER)


class TransactionCallbacks(
    TransactionCallbacksBase, TimeStampMixin, table=True
):
    """Transaction call back entity."""
    __tablename__ = "transaction_callbacks"
    id: int = Field(default=None, primary_key=True, nullable=False)
