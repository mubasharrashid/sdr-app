"""
Response handlers for standardized API responses.

This module provides exception handlers that automatically format
all error responses in the standardized format.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.response import ApiResponse


def setup_response_handlers(app):
    """
    Setup exception handlers to standardize all error responses.
    
    Call this in main.py after creating the FastAPI app.
    This will automatically format all HTTP exceptions and validation errors
    in the standardized response format.
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with standardized format."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error(
                message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
                errors=[exc.detail] if isinstance(exc.detail, str) else [str(exc.detail)],
                status_code=exc.status_code
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with standardized format."""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "Validation error")
            errors.append(f"{field}: {msg}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiResponse.error(
                message="Validation error",
                errors=errors,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with standardized format."""
        import traceback
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse.error(
                message="Internal server error",
                errors=[str(exc)],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).model_dump()
        )

