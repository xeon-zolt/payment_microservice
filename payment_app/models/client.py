"""Module for payment entities."""
from typing import List

from sqlmodel import Relationship, SQLModel, Field

from payment_app.models.timestampsmixin import TimeStampMixin


class ClientBase(SQLModel):
    """Base model for client."""
    name: str = Field(max_length=20)
    callback_url: str = Field(max_length=255)
    api_key: str = Field(max_length=64)
    active: bool = Field(default=True)


class Client(ClientBase, TimeStampMixin, table=True):
    """Client entity."""
    __tablename__ = "clients"
    id: int = Field(default=None, primary_key=True, nullable=False)
    transactions: List["Transaction"] = Relationship(back_populates="client")
    access_client_mappers: List["AccessClientMapper"] = Relationship(back_populates="client")
    client_gateways: List["ClientGateway"] = Relationship(back_populates="client")

