"""Module for payment entities."""
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import TIMESTAMP, Column, Field, text, func


class TimeStampMixin(BaseModel):
    """Time Stamp entity."""
    created_at: datetime = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP,
            server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        )
    )
