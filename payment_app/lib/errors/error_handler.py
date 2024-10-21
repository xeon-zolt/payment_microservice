"""Module to handle errors."""
from http import HTTPStatus

class CustomException(Exception):
    """Base class for exceptions."""
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description

    def __init__(self, message=None):
        if message:
            self.message = message

class NotFoundException(CustomException):
    """Class to raise not found exception."""
    code = HTTPStatus.NOT_FOUND
    error_code = HTTPStatus.NOT_FOUND
    message = HTTPStatus.NOT_FOUND.description

class InternalServerException(CustomException):
    """Class to raise server exception."""
    code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message = HTTPStatus.INTERNAL_SERVER_ERROR.description

class UnprocessableEntity(CustomException):
    """Class to raise not found exception."""
    code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = HTTPStatus.UNPROCESSABLE_ENTITY.description

class UnauthorizedException(CustomException):
    """Class to raise unauthorized exception."""
    code = HTTPStatus.UNAUTHORIZED
    error_code = HTTPStatus.UNAUTHORIZED
    message = HTTPStatus.UNAUTHORIZED.description

class ForbiddenException(CustomException):
    """Class to raise not accessible exception."""
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = HTTPStatus.FORBIDDEN.description


def error_mapper(error_type: str):
    """Error mapper."""
    error_config_type =  {
        'ERR_NOT_FOUND': NotFoundException(),
        'ERR_DATABASE': InternalServerException(),
    }
    return error_config_type[error_type]
