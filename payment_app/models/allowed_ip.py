"""Module for payment entities."""
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from payment_app.models.client import Client
from payment_app.models.timestampsmixin import TimeStampMixin


class AllowedIPBase(SQLModel):
    """Base model for allowed ips."""
    client_id: int = Field(default=None, foreign_key="clients.id")
    ip_range: str = Field(default=None)
    active: bool = Field(default=True)
    client: Optional[Client] = Relationship(back_populates="client")


class AllowedIP(AllowedIPBase, TimeStampMixin, table=True):
    """Allowed ip entity."""
    __tablename__ = "allowed_ips"
    id: int = Field(default=None, primary_key=True, nullable=False)
