"""
Helper functions for creating standardized API responses.

Import these in your API endpoints to easily create standardized responses.
"""

from typing import Any, Optional, List
from app.schemas.response import ApiResponse, PaginatedData


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> ApiResponse:
    """
    Create a standardized success response.
    
    Usage in endpoints:
        return success_response(data=result, message="User created successfully")
    """
    return ApiResponse.success(data=data, message=message, status_code=status_code)


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
    status_code: int = 200
) -> ApiResponse:
    """
    Create a standardized paginated response.
    
    Usage in endpoints:
        return paginated_response(items=users, total=count, page=page, page_size=page_size)
    """
    return ApiResponse.success_paginated(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        status_code=status_code
    )
