from typing import Optional

from sqlmodel import Relationship, SQLModel, Field
from typing_extensions import Annotated
import ulid
from payment_app.models.access_points import AccessPoint

from payment_app.models.client import Client

class AccessClientMapperBase(SQLModel):
    client_id: int = Field(default=None, foreign_key='clients.id')
    endpoint_id: str = Field(default=None, foreign_key='access_points.id')
    active: bool = Field(default=True)

class AccessClientMapper(AccessClientMapperBase, table=True):
    __tablename__ = "access_client_relations"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    client: Optional[Client] = Relationship(
        back_populates="access_client_mappers"
    )
    access_point: Optional[AccessPoint] = Relationship(
        back_populates="access_client_relations"
    )
