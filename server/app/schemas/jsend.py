"""
JSend Response Schema
Technical Specifications v2 - Section 7.1

JSend is a standardized response format for JSON APIs.
Reference: https://github.com/omniti-labs/jsend
"""
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class StatusEnum(str, Enum):
    """JSend status values."""
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"


T = TypeVar('T')


class JSendResponse(BaseModel, Generic[T]):
    """
    Generic JSend response wrapper.
    
    Attributes:
        status: Response status (success/fail/error)
        code: HTTP status code
        data: Response payload (optional, present on success)
        message: Error or info message (optional, present on fail/error)
    """
    status: StatusEnum = Field(..., description="Response status")
    code: int = Field(..., description="HTTP status code", ge=100, le=599)
    data: Optional[T] = Field(None, description="Response payload")
    message: Optional[str] = Field(None, description="Error or info message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": {},
                "message": None
            }
        }


class JSendSuccess(BaseModel, Generic[T]):
    """Helper for success responses."""
    status: StatusEnum = StatusEnum.SUCCESS
    code: int = 200
    data: T
    message: Optional[str] = None


class JSendFail(BaseModel):
    """Helper for fail responses (client errors)."""
    status: StatusEnum = StatusEnum.FAIL
    code: int = 400
    data: None = None
    message: str


class JSendError(BaseModel):
    """Helper for error responses (server errors)."""
    status: StatusEnum = StatusEnum.ERROR
    code: int = 500
    data: None = None
    message: str


# Type alias for common response types
AnyResponse = JSendResponse[Any]


def success_response(data: T, code: int = 200, message: Optional[str] = None) -> JSendResponse[T]:
    """
    Create a success JSend response.
    
    Args:
        data: Response payload
        code: HTTP status code (default 200)
        message: Optional success message
    
    Returns:
        JSendResponse with status=success
    """
    return JSendResponse[T](
        status=StatusEnum.SUCCESS,
        code=code,
        data=data,
        message=message
    )


def fail_response(message: str, code: int = 400, data: Optional[Any] = None) -> JSendResponse:
    """
    Create a fail JSend response (client error).
    
    Args:
        message: Error message
        code: HTTP status code (default 400)
        data: Optional additional data
    
    Returns:
        JSendResponse with status=fail
    """
    return JSendResponse(
        status=StatusEnum.FAIL,
        code=code,
        data=data,
        message=message
    )


def error_response(message: str, code: int = 500) -> JSendResponse:
    """
    Create an error JSend response (server error).
    
    Args:
        message: Error message
        code: HTTP status code (default 500)
    
    Returns:
        JSendResponse with status=error
    """
    return JSendResponse(
        status=StatusEnum.ERROR,
        code=code,
        data=None,
        message=message
    )