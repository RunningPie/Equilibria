'''
Core modul untuk eksekusi SQL user dan perbandingan dengan kunci jawaban.

Fix (2026-03-13):
  - Sandbox sekarang pakai koneksi terpisah yang di-SET ROLE ke sandbox_executor
    dan SET search_path ke sandbox
  - statement_timeout di-set SEBELUM query dijalankan.
  - Kegagalan sandbox tidak mencemari transaksi sesi utama (db)
'''

import asyncio
import re
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from app.core.logging_config import get_loggers
from app.core.config import settings   # exposes settings.DATABASE_URL & settings.SANDBOX_DB_ROLE
from decimal import Decimal
from datetime import datetime, date
import uuid

logger = get_loggers()[0]


def parse_sqlalchemy_error(error_msg: str) -> str:
    """
    Parse SQLAlchemy error messages to extract user-friendly error text.
    
    SQLAlchemy errors typically have this format:
    (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.X'>: USER_FRIENDLY_MSG [SQL: ...]
    
    We want to extract the USER_FRIENDLY_MSG part.
    
    Examples:
    - "column 'x' does not exist"
    - "unterminated quoted identifier at or near 'y'"
    - "relation 'z' does not exist"
    - "syntax error at or near 'w'"
    """
    if not error_msg:
        return "Query execution failed"
    
    # Pattern 1: Extract between ">: " and " [SQL:" 
    # This captures: ...ProgrammingError) <class 'X.Y'>: EXTRACT_THIS [SQL: ...
    pattern1 = r'>:\s*(.+?)\s*\[SQL:'
    match = re.search(pattern1, error_msg)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: Extract between ") " and " [SQL:" (for non-class exception format)
    pattern2 = r'\)\s+([^.]+?)\s*\[SQL:'
    match = re.search(pattern2, error_msg)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Extract PostgreSQL-style DETAIL or HINT if present
    detail_match = re.search(r'DETAIL:\s*(.+?)(?:\n|$)', error_msg)
    if detail_match:
        return detail_match.group(1).strip()
    
    # Pattern 4: Common PostgreSQL error patterns at start
    pg_patterns = [
        r"column\s+.+?\s+does not exist",
        r"relation\s+.+?\s+does not exist",
        r"syntax error at or near .+",
        r"unterminated quoted identifier.+",
        r"operator does not exist:.+",
        r"function .+? does not exist",
        r"table .+? does not exist",
        r"database .+? does not exist",
        r"permission denied for .+",
    ]
    for pattern in pg_patterns:
        match = re.search(pattern, error_msg, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    # Fallback: if message is too long, truncate and clean
    if len(error_msg) > 200:
        # Remove common SQLAlchemy boilerplate prefixes
        cleaned = re.sub(r'^\([^)]+\)\s*', '', error_msg)  # Remove (sqlalchemy...) prefix
        cleaned = re.sub(r"<class '[^']+'>\s*", '', cleaned)  # Remove <class '...'>
        cleaned = re.sub(r'\[SQL:.+$', '', cleaned, flags=re.DOTALL)  # Remove [SQL:... onwards
        return cleaned.strip()[:200]
    
    return error_msg


def serialize_value(value):
    """Convert asyncpg/SQLAlchemy types to JSON-serializable types."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    # Handle asyncpg.Record or other row-like types that may appear as nested values
    if hasattr(value, '__class__') and 'asyncpg' in value.__class__.__module__:
        if hasattr(value, '__dict__'):
            return str(value)
        elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            return [serialize_value(v) for v in value]
        else:
            return str(value)
    return value


def serialize_row(row):
    """Convert a row mapping to a JSON-serializable dict."""
    # Handle both RowMapping objects and asyncpg.Record objects
    if hasattr(row, 'items'):
        return {key: serialize_value(value) for key, value in row.items()}
    elif hasattr(row, '__dict__'):
        return {key: serialize_value(value) for key, value in row.__dict__.items()}
    elif hasattr(row, '__iter__') and hasattr(row, '_fields'):
        # asyncpg.Record style
        return {field: serialize_value(row[i]) for i, field in enumerate(row._fields)}
    else:
        # Fallback: convert to dict if possible
        return dict(row)


class SandboxExecutionError(Exception):
    """Custom exception untuk sandbox execution failures"""
    pass

'''
Dedicated engine untuk sandbox
URL sama tapi diisolasi melalui SET ROLE + SET search_path di level sesi
'''

_sandbox_engine = None


def _get_sandbox_engine():
    """
    singleton engine untuk sandbox.
    """
    global _sandbox_engine
    if _sandbox_engine is None:
        _sandbox_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
    return _sandbox_engine


BANNED_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
    'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'PG_', '--',
]


def _validate_query(query: str) -> str:
    """
    Tolak query yang mengandung keyword berbahaya.
    Kembalikan query yang sudah dibersihkan (tanpa trailing semicolon).
    """
    query_upper = query.upper()
    for keyword in BANNED_KEYWORDS:
        if keyword in query_upper:
            logger.warning(f"Keyword berbahaya terdeteksi: {keyword}")
            raise SandboxExecutionError(f"Keyword berbahaya terdeteksi: {keyword}")

    return query.strip().rstrip(";").strip()


async def execute_query_in_sandbox(
    query: str,
    timeout_ms: int = 5000,
) -> dict:
    """
    Eksekusi query SQL secara aman di skema sandbox:
      1. Keyword blocklist (DROP, DELETE, INSERT, dll.)
      2. Koneksi terpisah dari sesi utama — kegagalan tidak abort transaksi app.
      3. SET ROLE ke sandbox_executor (hanya punya SELECT di skema sandbox).
      4. SET search_path = sandbox  → unqualified table names mengarah ke sandbox.
      5. SET statement_timeout = <timeout_ms> SEBELUM query dijalankan.

    Parameter db sengaja dihapus — sandbox tidak boleh menyentuh sesi utama sama sekali.
    """
    clean_query = _validate_query(query)

    engine = _get_sandbox_engine()

    try:
        # begin() membuka koneksi baru + implicit transaction, auto-rollback on error.
        async with engine.begin() as conn:
            # 1. Turunkan hak akses ke sandbox_executor role.
            await conn.execute(text(f"SET ROLE {settings.SANDBOX_DB_ROLE}"))

            # 2. Arahkan unqualified table names ke skema sandbox.
            await conn.execute(text("SET search_path = sandbox"))

            # 3. Terapkan timeout SEBELUM query dijalankan.
            await conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))

            # 4. Jalankan query user.
            result = await conn.execute(text(clean_query))
            rows = result.mappings().all()

            return {
                "success": True,
                "rows": [serialize_row(row) for row in rows],
                "row_count": len(rows),
            }

    except SandboxExecutionError:
        raise
    except asyncio.TimeoutError:
        logger.error(f"Query timeout setelah {timeout_ms}ms: {clean_query!r}")
        raise SandboxExecutionError(f"Query execution timeout ({timeout_ms}ms)")
    except Exception as e:
        # Parse SQLAlchemy error to get user-friendly message
        error_msg = parse_sqlalchemy_error(str(e))
        logger.error(f"Sandbox execution error: {str(e)}")  # Log full error for debugging
        raise SandboxExecutionError(error_msg)


async def compare_query_results(
    user_query: str,
    target_query: str,
) -> dict:
    """
    Bandingkan hasil query user dengan target query secara order-insensitive.

    Returns:
        dict dengan format:
        {
            "is_correct": bool,
            "user_result": dict | None,  # Hasil query user (rows, row_count)
            "error": str | None           # Error message jika execution gagal
        }

    Mengembalikan result dengan is_correct=False (bukan raise) untuk semua kasus
    kegagalan sehingga pemanggil (submit handler) bisa tetap melanjutkan update sesi utama.
    """
    try:
        user_result = await execute_query_in_sandbox(user_query)
        target_result = await execute_query_in_sandbox(target_query)

        # Quick-fail: jumlah baris berbeda → pasti salah.
        if user_result["row_count"] != target_result["row_count"]:
            return {
                "is_correct": False,
                "user_result": user_result,
                "error": None
            }

        # Order-insensitive comparison menggunakan set of frozensets.
        user_rows = {frozenset(row.items()) for row in user_result["rows"]}
        target_rows = {frozenset(row.items()) for row in target_result["rows"]}

        is_correct = user_rows == target_rows

        return {
            "is_correct": is_correct,
            "user_result": user_result,
            "error": None
        }

    except SandboxExecutionError as e:
        return {
            "is_correct": False,
            "user_result": None,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return {
            "is_correct": False,
            "user_result": None,
            "error": "Query execution failed"
        }