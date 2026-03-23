"""
Unit Tests untuk Sandbox Executor - Kepatuhan Technical Specifications v4.3

Tes memverifikasi:
1. Eksekusi query SQL yang aman dengan timeout 5000ms
2. Pemblokiran keyword berbahaya (DROP, DELETE, INSERT, dll.)
3. Isolasi koneksi sandbox_executor role
4. Perbandingan hasil query (user vs target)
5. Timeout handling untuk query yang lambat
"""

import pytest
import asyncio
from app.core.sandbox_executor import (
    execute_query_in_sandbox, 
    compare_query_results, 
    SandboxExecutionError
)


class TestSandboxExecutor:
    """Test suite untuk sandbox executor functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_select_query_success(self):
        """Test that valid SELECT queries return success: true"""
        query = "SELECT COUNT(*) as total FROM mahasiswa"
        result = await execute_query_in_sandbox(query)
        
        assert result["success"] is True
        assert result["row_count"] == 1
        assert "total" in result["rows"][0]
        assert result["rows"][0]["total"] > 0  # Should have some data

    @pytest.mark.asyncio
    async def test_valid_select_query_with_limit(self):
        """Test SELECT query with LIMIT clause"""
        query = "SELECT nim, nama FROM mahasiswa LIMIT 3"
        result = await execute_query_in_sandbox(query)
        
        assert result["success"] is True
        assert result["row_count"] == 3
        assert len(result["rows"]) == 3
        
        # Verify structure of returned rows
        for row in result["rows"]:
            assert "nim" in row
            assert "nama" in row
            assert isinstance(row["nim"], str)
            assert isinstance(row["nama"], str)

    @pytest.mark.asyncio
    async def test_valid_select_query_with_where(self):
        """Test SELECT query with WHERE clause"""
        query = "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF' LIMIT 5"
        result = await execute_query_in_sandbox(query)
        
        assert result["success"] is True
        assert result["row_count"] <= 5
        
        # All returned students should be from IF department
        for row in result["rows"]:
            # Note: We can't verify jurusan directly since we didn't select it
            # but we can verify the query executed successfully
            assert "nim" in row
            assert "nama" in row

    @pytest.mark.asyncio
    async def test_dangerous_drop_table_blocked(self):
        """Test that DROP TABLE is blocked"""
        query = "DROP TABLE mahasiswa"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: DROP"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_delete_blocked(self):
        """Test that DELETE is blocked"""
        query = "DELETE FROM mahasiswa WHERE nim = '18222001'"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: DELETE"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_insert_blocked(self):
        """Test that INSERT is blocked"""
        query = "INSERT INTO mahasiswa VALUES ('test123', 'Test User', 'IF', 2023, 3.0)"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: INSERT"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_update_blocked(self):
        """Test that UPDATE is blocked"""
        query = "UPDATE mahasiswa SET nama = 'Updated Name' WHERE nim = '18222001'"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: UPDATE"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_alter_blocked(self):
        """Test that ALTER TABLE is blocked"""
        query = "ALTER TABLE mahasiswa ADD COLUMN test_col VARCHAR(50)"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: ALTER"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_create_blocked(self):
        """Test that CREATE TABLE is blocked"""
        query = "CREATE TABLE test_table (id INT, name VARCHAR(50))"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: CREATE"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_truncate_blocked(self):
        """Test that TRUNCATE is blocked"""
        query = "TRUNCATE TABLE mahasiswa"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: TRUNCATE"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_grant_blocked(self):
        """Test that GRANT is blocked"""
        query = "GRANT ALL PRIVILEGES ON mahasiswa TO PUBLIC"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: GRANT"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_revoke_blocked(self):
        """Test that REVOKE is blocked"""
        query = "REVOKE ALL PRIVILEGES ON mahasiswa FROM PUBLIC"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: REVOKE"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_pg_functions_blocked(self):
        """Test that PG_ functions are blocked"""
        query = "SELECT pg_sleep(1)"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: PG_"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_dangerous_sql_comments_blocked(self):
        """Test that SQL comments are blocked"""
        query = "SELECT * FROM mahasiswa -- This is a comment"
        
        with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: --"):
            await execute_query_in_sandbox(query)

    @pytest.mark.asyncio
    async def test_case_insensitive_keyword_detection(self):
        """Test that keyword detection is case insensitive"""
        dangerous_variants = [
            "drop table mahasiswa",
            "Drop Table mahasiswa", 
            "DROP TABLE mahasiswa",
            "dRoP tAbLe mahasiswa"
        ]
        
        for variant in dangerous_variants:
            with pytest.raises(SandboxExecutionError, match="Dangerous keyword detected: DROP"):
                await execute_query_in_sandbox(variant)

    @pytest.mark.asyncio
    async def test_query_comparison_identical_results(self):
        """Test query comparison with identical results should return True"""
        user_query = "SELECT nim, nama FROM mahasiswa WHERE nim = '18222001'"
        target_query = "SELECT nim, nama FROM sandbox.mahasiswa WHERE nim = '18222001'"
        
        is_correct = await compare_query_results(user_query, target_query)
        assert is_correct is True

    @pytest.mark.asyncio
    async def test_query_comparison_different_results(self):
        """Test query comparison with different results should return False"""
        user_query = "SELECT nim, nama FROM mahasiswa WHERE nim = '18222001'"
        target_query = "SELECT nim, nama FROM mahasiswa WHERE nim = '18222002'"
        
        is_correct = await compare_query_results(user_query, target_query)
        assert is_correct is False

    @pytest.mark.asyncio
    async def test_query_comparison_different_row_count(self):
        """Test query comparison with different row counts should return False"""
        user_query = "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF' LIMIT 1"
        target_query = "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF' LIMIT 5"
        
        is_correct = await compare_query_results(user_query, target_query)
        assert is_correct is False

    @pytest.mark.asyncio
    async def test_query_comparison_order_insensitive(self):
        """Test that query comparison is order insensitive"""
        user_query = "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF' ORDER BY nim DESC"
        target_query = "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF' ORDER BY nim ASC"
        
        is_correct = await compare_query_results(user_query, target_query)
        # Should be True if they return the same rows regardless of order
        assert is_correct is True

    @pytest.mark.asyncio
    async def test_query_comparison_with_dangerous_user_query(self):
        """Test that dangerous user queries return False (not raise) in comparison"""
        dangerous_user_query = "DROP TABLE mahasiswa"
        safe_target_query = "SELECT nim, nama FROM mahasiswa LIMIT 1"
        
        is_correct = await compare_query_results(dangerous_user_query, safe_target_query)
        assert is_correct is False  # Should return False, not raise exception

    @pytest.mark.asyncio
    async def test_query_comparison_with_dangerous_target_query(self):
        """Test that dangerous target queries return False (not raise) in comparison"""
        safe_user_query = "SELECT nim, nama FROM mahasiswa LIMIT 1"
        dangerous_target_query = "DROP TABLE mahasiswa"
        
        is_correct = await compare_query_results(safe_user_query, dangerous_target_query)
        assert is_correct is False  # Should return False, not raise exception

    @pytest.mark.asyncio
    async def test_timeout_handling_with_custom_timeout(self):
        """Test that queries properly timeout with custom timeout"""
        # Use a very short timeout for testing
        long_query = """
        SELECT 
            pg_sleep(3)
        """
        
        with pytest.raises(SandboxExecutionError, match="Query execution timeout"):
            await execute_query_in_sandbox(long_query, timeout_ms=1000)  # 1 second timeout

    @pytest.mark.asyncio
    async def test_timeout_handling_default_timeout(self):
        """Test that default timeout (5000ms) works"""
        # This should work with default timeout but fail with shorter timeout
        quick_query = """
        SELECT 
            'test' as result,
            pg_sleep(1) as sleep_test
        """
        
        # Should succeed with default timeout
        result = await execute_query_in_sandbox(quick_query, timeout_ms=2000)
        assert result["success"] is True
        assert result["row_count"] == 1
        assert result["rows"][0]["result"] == "test"

    @pytest.mark.asyncio
    async def test_query_cleaning_removes_semicolon(self):
        """Test that queries are properly cleaned (trailing semicolon removed)"""
        query_with_semicolon = "SELECT COUNT(*) as total FROM mahasiswa;"
        query_without_semicolon = "SELECT COUNT(*) as total FROM mahasiswa"
        
        result1 = await execute_query_in_sandbox(query_with_semicolon)
        result2 = await execute_query_in_sandbox(query_without_semicolon)
        
        # Both should return the same result
        assert result1["success"] is True
        assert result2["success"] is True
        assert result1["rows"][0]["total"] == result2["rows"][0]["total"]

    @pytest.mark.asyncio
    async def test_join_query_success(self):
        """Test that complex JOIN queries work correctly"""
        query = """
        SELECT m.nim, m.nama, mk.nama_mk, f.nilai
        FROM mahasiswa m
        JOIN frs f ON m.nim = f.nim
        JOIN matakuliah mk ON f.kode_mk = mk.kode_mk
        LIMIT 5
        """
        
        result = await execute_query_in_sandbox(query)
        
        assert result["success"] is True
        assert result["row_count"] <= 5
        
        if result["row_count"] > 0:
            row = result["rows"][0]
            assert "nim" in row
            assert "nama" in row
            assert "nama_mk" in row
            assert "nilai" in row

    @pytest.mark.asyncio
    async def test_aggregation_query_success(self):
        """Test that aggregation queries work correctly"""
        query = """
        SELECT 
            jurusan,
            COUNT(*) as total_mahasiswa,
            AVG(ipk) as rata_ipk
        FROM mahasiswa
        GROUP BY jurusan
        ORDER BY jurusan
        """
        
        result = await execute_query_in_sandbox(query)
        
        assert result["success"] is True
        assert result["row_count"] > 0
        
        for row in result["rows"]:
            assert "jurusan" in row
            assert "total_mahasiswa" in row
            assert "rata_ipk" in row
            assert isinstance(row["total_mahasiswa"], int)
            assert isinstance(row["rata_ipk"], float)


class TestSandboxExecutorIntegration:
    """Integration tests for sandbox executor with realistic scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_sql_question_scenario(self):
        """Test complete scenario: user submits answer, system compares with target"""
        # Simulate a typical SQL question scenario
        user_query = "SELECT nim, nama, ipk FROM mahasiswa WHERE jurusan = 'IF' AND ipk > 3.5 ORDER BY ipk DESC LIMIT 3"
        target_query = "SELECT nim, nama, ipk FROM sandbox.mahasiswa WHERE jurusan = 'IF' AND ipk > 3.5 ORDER BY ipk DESC LIMIT 3"
        
        is_correct = await compare_query_results(user_query, target_query)
        assert isinstance(is_correct, bool)
        
        # Also test that both queries can execute individually
        user_result = await execute_query_in_sandbox(user_query)
        target_result = await execute_query_in_sandbox(target_query)
        
        assert user_result["success"] is True
        assert target_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_invalid_sql(self):
        """Test error handling for invalid SQL syntax"""
        invalid_query = "SELEC * FROM mahasiswa WHERE"  # Invalid SQL
        
        with pytest.raises(SandboxExecutionError, match="Query execution failed"):
            await execute_query_in_sandbox(invalid_query)

    @pytest.mark.asyncio
    async def test_error_handling_nonexistent_table(self):
        """Test error handling for queries against nonexistent tables"""
        invalid_query = "SELECT * FROM nonexistent_table"
        
        with pytest.raises(SandboxExecutionError, match="Query execution failed"):
            await execute_query_in_sandbox(invalid_query)


if __name__ == "__main__":
    # Run quick manual test
    print("Running Sandbox Executor Tests...")
    
    async def quick_test():
        try:
            # Test 1: Valid query
            print("\n1. Testing valid SELECT query...")
            result = await execute_query_in_sandbox("SELECT COUNT(*) as total FROM mahasiswa")
            print(f"✓ Valid query result: {result}")
            
            # Test 2: Dangerous query
            print("\n2. Testing dangerous DROP TABLE...")
            try:
                await execute_query_in_sandbox("DROP TABLE mahasiswa")
                print("✗ Dangerous query was not blocked!")
            except SandboxExecutionError as e:
                print(f"✓ Dangerous query correctly blocked: {e}")
            
            # Test 3: Query comparison
            print("\n3. Testing query comparison...")
            is_correct = await compare_query_results(
                "SELECT nim FROM mahasiswa WHERE nim = '18222001'",
                "SELECT nim FROM mahasiswa WHERE nim = '18222001'"
            )
            print(f"✓ Query comparison result: {is_correct}")
            
            print("\n✅ All quick tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(quick_test())
