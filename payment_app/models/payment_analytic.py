"""Module for payment entities."""
import ulid
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlmodel import SQLModel, Field
from typing_extensions import Annotated

class PaymentAnalyticBase(SQLModel):
    """Base model for payment analytics."""
    transaction_id: str = Field(max_length=64)
    order_id: str = Field(nullable=True, max_length=100)
    payment_id: str = Field(nullable=True, max_length=100, sa_column=Column(unique=True))
    razorpay_status: str = Field(nullable=True, max_length=20)
    status: str = Field(nullable=True, max_length=10)
    payment_method: str = Field(nullable=True, max_length=20)
    card_name: str = Field(nullable=True, max_length=30)
    card_id: str = Field(nullable=True, max_length=100)
    card_type: str = Field(nullable=True, max_length=20)
    card_network: str = Field(nullable=True, max_length=20)
    issuer: str = Field(nullable=True, max_length=64)
    step: str = Field(nullable=True, max_length=64)
    reason: str = Field(nullable=True, sa_column=Column(LONGTEXT))

class PaymentAnalytic(PaymentAnalyticBase, table=True):
    """Payment analytic entity."""
    __tablename__ = "payment_analytics"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    __table_args__ = ()
