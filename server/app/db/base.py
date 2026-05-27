"""
Base class SQLAlchemy untuk semua model database.
Base ini dipakai Alembic untuk generate migrasi otomatis.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Metadata ini yang dibaca Alembic untuk generate migrasi
metadata = Base.metadata