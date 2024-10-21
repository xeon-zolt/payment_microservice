"""Module for payment entities."""
from typing import Optional

from sqlmodel import Relationship, SQLModel, Field
from payment_app.models.client import Client

from payment_app.models.timestampsmixin import TimeStampMixin


class ClientGatewayBase(SQLModel):
    """Base model for client gateways."""
    driver_id: int = Field(nullable=False)
    default: bool = Field(default=False)
    active: bool = Field(default=True)
    client_id: int = Field(default=None, foreign_key="clients.id")


class ClientGateway(ClientGatewayBase, TimeStampMixin, table=True):
    """Client gateway entity."""
    __tablename__ = "client_gateways"
    id: int = Field(default=None, primary_key=True, nullable=False)
    client: Optional[Client] = Relationship(back_populates="client_gateways")
