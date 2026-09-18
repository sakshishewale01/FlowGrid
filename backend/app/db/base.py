"""
SQLAlchemy Declarative Base
===========================
Defines the base class for all ORM models across FlowGrid.

In SQLAlchemy 2.0:
------------------
We use `DeclarativeBase` as the modern, type-safe superclass for database models.
Any table defined in future phases (e.g. Warehouses, Shipments, Products)
will inherit from this `Base` class.

Alembic inspects `Base.metadata` to detect model definitions and autogenerate
database schema migration scripts.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Root declarative base for all FlowGrid SQLAlchemy models.
    """
    pass
