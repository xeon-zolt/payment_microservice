"""Module for payment entities."""
from datetime import datetime
from typing import Optional

import ulid
from sqlalchemy import Column, TEXT
from sqlmodel import SQLModel, Field, DateTime, Relationship
from typing_extensions import Annotated

from payment_app.models.timestampsmixin import TimeStampMixin
from payment_app.models.transaction import Transaction


class TransactionCommunicationsBase(SQLModel):
    """
    Transaction communication base model.
    Once the status of communication is success it will remove the entry.
    """

    transaction_id: str = Field(nullable=False, foreign_key="transactions.id")
    communication_count: int = Field(default=1, nullable=False)
    event: str = Field(nullable=False)
    status: str = Field(nullable=False)
    error: str = Field(sa_column=Column(TEXT))

class TransactionCommunications(
    TransactionCommunicationsBase, TimeStampMixin, table=True
):
    """Transaction communication entity."""
    __tablename__ = "transaction_communications"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    transaction: Optional[Transaction] = Relationship(
        back_populates="transaction_communication"
    )
