'''
Core modul untuk mengeksekusi SQL user dan membandingkan dengan kunci jawaban.

Fix (2026-03-13):
  - Sandbox sekarang pakai koneksi terpisah yang di-SET ROLE ke sandbox_executor
    dan SET search_path ke sandbox
  - statement_timeout di-set SEBELUM query dijalankan.
  - Kegagalan sandbox tidak mencemari transaksi sesi utama (db)
'''

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from app.core.logging_config import get_loggers
from app.core.config import settings   # exposes settings.DATABASE_URL & settings.SANDBOX_DB_ROLE

logger = get_loggers()[0]


class SandboxExecutionError(Exception):
    """Custom exception for sandbox execution failures"""
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
            logger.warning(f"Dangerous keyword detected: {keyword}")
            raise SandboxExecutionError(f"Dangerous keyword detected: {keyword}")

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

            # 3. Terapkan timeout SEBELUM query user dijalankan.
            await conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))

            # 4. Jalankan query user.
            result = await conn.execute(text(clean_query))
            rows = result.mappings().all()

            return {
                "success": True,
                "rows": [dict(row) for row in rows],
                "row_count": len(rows),
            }

    except SandboxExecutionError:
        raise
    except asyncio.TimeoutError:
        logger.error(f"Query timeout after {timeout_ms}ms: {clean_query!r}")
        raise SandboxExecutionError(f"Query execution timeout ({timeout_ms}ms)")
    except Exception as e:
        logger.error(f"Sandbox execution error: {e}")
        raise SandboxExecutionError(f"Query execution failed: {str(e)}")


async def compare_query_results(
    user_query: str,
    target_query: str,
) -> bool:
    """
    Bandingkan hasil query user dengan target query secara order-insensitive.

    Mengembalikan False (bukan raise) untuk semua kasus kegagalan sehingga
    pemanggil (submit handler) bisa tetap melanjutkan update sesi utama.
    """
    try:
        user_result = await execute_query_in_sandbox(user_query)
        target_result = await execute_query_in_sandbox(target_query)

        # Quick-fail: jumlah baris berbeda → pasti salah.
        if user_result["row_count"] != target_result["row_count"]:
            return False

        # Order-insensitive comparison menggunakan set of frozensets.
        user_rows = {frozenset(row.items()) for row in user_result["rows"]}
        target_rows = {frozenset(row.items()) for row in target_result["rows"]}

        return user_rows == target_rows

    except SandboxExecutionError:
        return False
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return False