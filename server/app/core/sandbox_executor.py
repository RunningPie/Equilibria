'''
Ini core modul untuk mengekseksui SQL
membandingkan jawaban user dengan kunci jawaban
'''

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.logging_config import get_loggers

logger = get_loggers()[0]

class SandboxExecutionError(Exception):
    """Custom exception for sandbox execution failures"""
    pass

async def execute_query_in_sandbox(
    db: AsyncSession,
    query: str,
    timeout_ms: int = 5000
) -> dict:
    '''
    Tugasnya eksekusi query SQL dengan aman:
    1. Hanya kata kunci yang berkaitan dengan operasi READ yang diperbolehkan
    2. Diterapkan query timeout
    3. Rolenya hanya sandbox_executor (jadi gabisa akses schema lain)
    '''
    
    banned_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'pg_', '--'
    ]
    
    query_upper = query.upper()
    for keyword in banned_keywords:
        logger.warning(f"Dangerous keyword detected: {keyword}")
        raise
    
    try:
        await db.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        
        result = await db.execute(text(f"SET search_path TO sandbox; {query}"))
        rows = result.fetchall()
        
        return {
            "success": True,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows)
        }
    except asyncio.TimeoutError:
        logger.error(f"Query timeout after {timeout_ms}ms")
        raise SandboxExecutionError(f"Query execution timeout ({timeout_ms}ms)")
    except Exception as e:
        logger.error(f"Sandbox execution error: {e}")
        raise SandboxExecutionError(f"Query execution failed: {str(e)}")

async def compare_query_results(
    db: AsyncSession,
    user_query: str,
    target_query: str
) -> bool:
    
    try:
        user_result = await execute_query_in_sandbox(db, user_query)
        target_result = await execute_query_in_sandbox(db, target_query)
        
        # bandingkan jumlah baris yang dikembalikan
        # sebagai quick fail
        if user_result["row_count"] != target_result["row_count"]:
            return False

        user_rows = {frozenset(row.items()) for row in user_result["rows"]}
        target_rows = {frozenset(row.items()) for row in target_result["rows"]}
        
        return user_rows == target_rows

    except SandboxExecutionError:
        return False
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return False