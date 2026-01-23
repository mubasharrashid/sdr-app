"""
Common API Response Schemas.

Standardized response format for all API endpoints:
{
  "statusCode": 200,
  "isSuccess": true,
  "message": "Success",
  "data": {...},
  "errors": []
}
"""

from pydantic import BaseModel, Field
from typing import Any, List, Optional, Union
from math import ceil


class PaginatedData(BaseModel):
    """Paginated data structure."""
    
    data: List[Any] = Field(default_factory=list, description="Array of data items")
    totalCount: int = Field(default=0, ge=0, description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page number")
    pageSize: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    totalPages: int = Field(default=0, ge=0, description="Total number of pages")
    hasNextPage: bool = Field(default=False, description="Whether there is a next page")
    hasPreviousPage: bool = Field(default=False, description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedData":
        """Create a paginated data response."""
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            data=items,
            totalCount=total,
            page=page,
            pageSize=page_size,
            totalPages=total_pages,
            hasNextPage=page < total_pages,
            hasPreviousPage=page > 1
        )


class ApiResponse(BaseModel):
    """Standard API response format."""
    
    statusCode: int = Field(description="HTTP status code")
    isSuccess: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: Optional[Union[Any, PaginatedData]] = Field(default=None, description="Response data")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    
    @classmethod
    def success(
        cls,
        data: Optional[Any] = None,
        message: str = "Success",
        status_code: int = 200
    ) -> "ApiResponse":
        """Create a successful response."""
        return cls(
            statusCode=status_code,
            isSuccess=True,
            message=message,
            data=data,
            errors=[]
        )
    
    @classmethod
    def success_paginated(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "Success",
        status_code: int = 200
    ) -> "ApiResponse":
        """Create a successful paginated response."""
        paginated_data = PaginatedData.create(items, total, page, page_size)
        return cls(
            statusCode=status_code,
            isSuccess=True,
            message=message,
            data=paginated_data,
            errors=[]
        )
    
    @classmethod
    def error(
        cls,
        message: str = "Error",
        errors: Optional[List[str]] = None,
        status_code: int = 400
    ) -> "ApiResponse":
        """Create an error response."""
        return cls(
            statusCode=status_code,
            isSuccess=False,
            message=message,
            data=None,
            errors=errors or [message]
        )
