"""Module for payment entities."""
import ulid
from sqlalchemy import Column
from sqlmodel import JSON, Index, SQLModel, Field
from typing_extensions import Annotated

from payment_app.models.timestampsmixin import TimeStampMixin

class PaymentLinkBase(SQLModel):
    """Base model for payment link."""
    transaction_id: str = Field(default=None, foreign_key="transactions.id")
    plink_id: str = Field(max_length=64)
    api_response: dict = Field(sa_column=Column(JSON))
    update_count: int = Field(default=1, nullable=False)
    notify_sms_count: int = Field(default=1, nullable=False)
    notify_email_count: int = Field(default=1, nullable=False)
    status: str = Field(default='issued', nullable=False)


class PaymentLink(PaymentLinkBase, TimeStampMixin, table=True):
    """Payment link entity"""
    __tablename__ = "payment_links"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    # transaction: Optional[Transaction] = Relationship(back_populates="payment_links")
    __table_args__ = (
        Index(
            "payment_link_comp_index",
            "transaction_id",
            "plink_id",
        ),
    )
