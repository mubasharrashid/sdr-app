"""
SQLAlchemy Base Class for all models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    All models should inherit from this class to ensure
    consistent behavior and shared functionality.
    """
    pass
