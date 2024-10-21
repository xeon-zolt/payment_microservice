"""Module for payment entities."""
from datetime import datetime
import ulid
from pydantic import condecimal
from sqlalchemy import Column, SMALLINT
from sqlmodel import JSON, SQLModel, Field, TIMESTAMP
from typing_extensions import Annotated

from payment_app.models.timestampsmixin import TimeStampMixin

class QRCodeBase(SQLModel):
    qr_id: str = Field(max_length=65, nullable=True)
    usage: str = Field(max_length=20, default="multiple_use")
    type: str = Field(max_length=20, default="upi_qr")
    payment_amount: condecimal(decimal_places=2) = Field(default=0)
    is_fixed_amount: int= Field(sa_column=Column(SMALLINT))
    api_request: dict = Field(sa_column=Column(JSON))
    api_response: dict = Field(sa_column=Column(JSON))
    notes: dict = Field(sa_column=Column(JSON))
    image_url: str = Field(max_length=65, nullable=True)
    close_by: datetime = Field(sa_column=Column(TIMESTAMP), nullable=True)
    closed_at: datetime = Field(sa_column=Column(TIMESTAMP), nullable=True)
    close_reason: str = Field(max_length=20, nullable=True)
    status: str = Field(max_length=10, default="active")
    driver: int = Field(nullable=True)

class QRCode(QRCodeBase, TimeStampMixin, table=True):
    """QR code entity."""
    __tablename__ = "qr_codes"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
