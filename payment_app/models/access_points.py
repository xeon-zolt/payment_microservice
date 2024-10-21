from typing import List
from sqlmodel import Relationship, SQLModel, Field

from typing_extensions import Annotated
import ulid

class AccessPointBase(SQLModel):
    endpoint: str = Field(default=None)
    active: bool = Field(default=True)

class AccessPoint(AccessPointBase, table=True):
    __tablename__ = "access_points"
    id: Annotated[
        str,
        Field(primary_key=True, nullable=False, default_factory=lambda: ulid.ulid()),
    ]
    access_client_relations: List["AccessClientMapper"] = Relationship(
        back_populates="access_point"
    )
