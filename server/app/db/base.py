"""
Base class SQLAlchemy untuk semua model database.
Base ini dipakai Alembic untuk generate migrasi otomatis.
"""
from sqlalchemy.orm import declarative_base

# Buat base class yang bakal diwariskan ke semua model
Base = declarative_base()

# Metadata ini yang dibaca Alembic untuk generate migrasi
metadata = Base.metadata