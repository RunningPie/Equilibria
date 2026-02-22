"""
SQLAlchemy Base Class untuk semua model database.
Base ini akan digunakan oleh Alembic untuk autogenerate migrations.
"""
from sqlalchemy.orm import declarative_base

# Membuat Base class yang akan di-inherit oleh semua model
Base = declarative_base()

# Metadata ini yang akan dibaca Alembic untuk autogenerate
metadata = Base.metadata