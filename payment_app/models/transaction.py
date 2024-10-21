"""Module for payment entities."""
from typing import Final, List, Optional

import ulid
from pydantic import condecimal
from sqlalchemy import Column, SMALLINT
from sqlmodel import JSON, Index, SQLModel, Field, Relationship
from typing_extensions import Annotated

from payment_app.models.client import Client
from payment_app.models.timestampsmixin import TimeStampMixin

from payment_app.schemas.requests.v1.make_payment_in import StoreType

STATUS_SUCCESS: Final = "success"
STATUS_PENDING: Final = "pending"
STATUS_FAILED: Final = "failed"
STATUS_CANCEL = "cancelled"

PAYMENT_TYPE: Final = 'link'
IN_COUNTRY_CODE: Final = '+91'
IN_CURRENCY_SHORT_CODE: Final = 'INR'
CONVERT_IN_PAISE: Final = 100


class TransactionBase(SQLModel):
    """Base model for transactions."""
    total_amount: condecimal(decimal_places=2) = Field(default=0)
    amount: condecimal(decimal_places=2) = Field(default=0)
    source_id: str = Field(max_length=64)
    payment_type: str = Field(max_length=20)
    store_type: StoreType = Field(max_length=20, nullable=True)
    driver: int = Field(nullable=True)  # mapped to config id
    gateway_order_id: str = Field(nullable=True, max_length=100, index=True)
    gateway_payment_id: str = Field(nullable=True, max_length=100, index=True)
    status: str = Field(max_length=10, default="pending")  # pending failed sucess
    api_request: dict = Field(sa_column=Column(JSON))
    api_response: dict = Field(sa_column=Column(JSON))
    callback_response: dict = Field(sa_column=Column(JSON))
    api_status: int = Field(sa_column=Column(SMALLINT))
    store_id: str = Field(max_length=64)
    client_id: int = Field(default=None, foreign_key="clients.id")
    additional_info: dict = Field(sa_column=Column(JSON))
    api_version: int
    client_version: str = Field(nullable=True, max_length=10)


class Transaction(TransactionBase, TimeStampMixin, table=True):
    """Transacton entity."""
    __tablename__ = "transactions"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    client: Optional[Client] = Relationship(back_populates="transactions")
    transaction_communication: List["TransactionCommunications"] = Relationship(
        back_populates="transaction"
    )
    refund_transaction: List["RefundTransaction"] = Relationship(
        back_populates="transaction"
    )
    __table_args__ = (
        Index(
            "transaction_comp_index",
            "source_id",
            "payment_type",
            "store_id",
            "client_id",
        ),
    )
