"""Module to handle errors."""
from .error_handler import (
    CustomException,
    InternalServerException,
    NotFoundException,
    UnprocessableEntity,
    ForbiddenException
)

__all__ = [
    "CustomException",
    "InternalServerException",
    "NotFoundException",
    "UnprocessableEntity",
    "ForbiddenException"
]
