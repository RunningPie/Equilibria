"""
Script untuk seed database dengan soal-soal SQL CH01, CH02, & CH03
Tech Specs v4.2 - Initial difficulty set untuk Item Selection Strategy
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.db.models import Question, Module
from uuid import uuid4


async def seed_questions():
    """Seed database dengan soal-soal SQL untuk CH01, CH02, dan CH03"""
    
    async with async_session_factory() as db:
        try:
            # Cek apakah modul sudah ada
            existing_modules = await db.execute(
                "SELECT module_id FROM modules WHERE module_id IN ('CH01', 'CH02', 'CH03')"
            )
            module_ids = [row[0] for row in existing_modules.fetchall()]
            
            # Buat modul jika belum ada
            if 'CH01' not in module_ids:
                ch01 = Module(
                    module_id="CH01",
                    title="Basic Selection",
                    difficulty_min=-3.0,
                    difficulty_max=3.0,
                    unlock_theta_threshold=0.0,  # CH01 selalu terbuka
                    order_index=1,
                    content_html="<h1>Basic SQL Selection</h1><p>Learn basic SELECT statements...</p>"
                )
                db.add(ch01)
            
            if 'CH02' not in module_ids:
                ch02 = Module(
                    module_id="CH02", 
                    title="Aggregation",
                    difficulty_min=-2.0,
                    difficulty_max=2.0,
                    unlock_theta_threshold=900.0,  # Butuh theta >= 900
                    order_index=2,
                    content_html="<h1>SQL Aggregation</h1><p>Learn GROUP BY, COUNT, SUM...</p>"
                )
                db.add(ch02)
            
            if 'CH03' not in module_ids:
                ch03 = Module(
                    module_id="CH03", 
                    title="Advanced Queries",
                    difficulty_min=-1.0,
                    difficulty_max=1.0,
                    unlock_theta_threshold=1100.0,  # Butuh theta >= 1100
                    order_index=3,
                    content_html="<h1>Advanced SQL Queries</h1><p>Learn subqueries, joins, window functions...</p>"
                )
                db.add(ch03)
            
            await db.commit()
            
            # Soal-soal CH01 - Basic Selection
            ch01_questions = [
                {
                    "question_id": "CH01-001",
                    "content": "Tampilkan semua data mahasiswa",
                    "target_query": "SELECT * FROM mahasiswa;",
                    "initial_difficulty": -2.0,
                    "topic_tags": ["basic", "select", "all"]
                },
                {
                    "question_id": "CH01-002", 
                    "content": "Tampilkan NIM dan Nama mahasiswa dari jurusan IF",
                    "target_query": "SELECT nim, nama FROM mahasiswa WHERE jurusan = 'IF';",
                    "initial_difficulty": -1.5,
                    "topic_tags": ["basic", "select", "where"]
                },
                {
                    "question_id": "CH01-003",
                    "content": "Tampilkan mahasiswa perempuan (gender = 'P')",
                    "target_query": "SELECT * FROM mahasiswa WHERE gender = 'P';",
                    "initial_difficulty": -1.0,
                    "topic_tags": ["basic", "select", "where"]
                },
                {
                    "question_id": "CH01-004",
                    "content": "Tampilkan 5 mahasiswa pertama diurutkan berdasarkan NIM",
                    "target_query": "SELECT * FROM mahasiswa ORDER BY nim LIMIT 5;",
                    "initial_difficulty": -0.5,
                    "topic_tags": ["basic", "select", "order", "limit"]
                },
                {
                    "question_id": "CH01-005",
                    "content": "Hitung jumlah mahasiswa di setiap jurusan",
                    "target_query": "SELECT jurusan, COUNT(*) as jumlah FROM mahasiswa GROUP BY jurusan;",
                    "initial_difficulty": 0.0,
                    "topic_tags": ["aggregation", "count", "group"]
                },
                {
                    "question_id": "CH01-006",
                    "content": "Tampilkan mahasiswa dengan angkatan > 2020",
                    "target_query": "SELECT * FROM mahasiswa WHERE angkatan > 2020;",
                    "initial_difficulty": 0.5,
                    "topic_tags": ["basic", "select", "where", "comparison"]
                },
                {
                    "question_id": "CH01-007",
                    "content": "Cari mahasiswa dengan nama mengandung 'Ahmad'",
                    "target_query": "SELECT * FROM mahasiswa WHERE nama LIKE '%Ahmad%';",
                    "initial_difficulty": 1.0,
                    "topic_tags": ["basic", "select", "where", "like"]
                },
                {
                    "question_id": "CH01-008",
                    "content": "Tampilkan mahasiswa IF diurutkan descending berdasarkan angkatan",
                    "target_query": "SELECT * FROM mahasiswa WHERE jurusan = 'IF' ORDER BY angkatan DESC;",
                    "initial_difficulty": 1.5,
                    "topic_tags": ["basic", "select", "where", "order"]
                },
                {
                    "question_id": "CH01-009",
                    "content": "Hitung rata-rata angkatan mahasiswa per jurusan",
                    "target_query": "SELECT jurusan, AVG(angkatan) as rata_angkatan FROM mahasiswa GROUP BY jurusan;",
                    "initial_difficulty": 2.0,
                    "topic_tags": ["aggregation", "avg", "group"]
                },
                {
                    "question_id": "CH01-010",
                    "content": "Tampilkan jurusan dengan jumlah mahasiswa > 10",
                    "target_query": "SELECT jurusan, COUNT(*) as jumlah FROM mahasiswa GROUP BY jurusan HAVING COUNT(*) > 10;",
                    "initial_difficulty": 2.5,
                    "topic_tags": ["aggregation", "count", "group", "having"]
                }
            ]
            
            # Soal-soal CH02 - Aggregation  
            ch02_questions = [
                {
                    "question_id": "CH02-001",
                    "content": "Hitung total SKS yang diambil setiap mahasiswa",
                    "target_query": "SELECT nim, SUM(sks) as total_sks FROM frs GROUP BY nim;",
                    "initial_difficulty": -1.0,
                    "topic_tags": ["aggregation", "sum", "group"]
                },
                {
                    "question_id": "CH02-002",
                    "content": "Tampilkan mahasiswa dengan total SKS > 15",
                    "target_query": "SELECT nim, SUM(sks) as total_sks FROM frs GROUP BY nim HAVING SUM(sks) > 15;",
                    "initial_difficulty": -0.5,
                    "topic_tags": ["aggregation", "sum", "group", "having"]
                },
                {
                    "question_id": "CH02-003",
                    "content": "Hitung rata-rata SKS per mahasiswa per semester",
                    "target_query": "SELECT nim, semester, AVG(sks) as rata_sks FROM frs GROUP BY nim, semester;",
                    "initial_difficulty": 0.0,
                    "topic_tags": ["aggregation", "avg", "group"]
                },
                {
                    "question_id": "CH02-004",
                    "content": "Tampilkan matakuliah dengan SKS tertinggi",
                    "target_query": "SELECT * FROM matakuliah ORDER BY sks DESC LIMIT 1;",
                    "initial_difficulty": 0.5,
                    "topic_tags": ["basic", "select", "order", "limit"]
                },
                {
                    "question_id": "CH02-005",
                    "content": "Hitung jumlah matakuliah per dosen",
                    "target_query": "SELECT dosen_id, COUNT(*) as jumlah_matkul FROM matakuliah GROUP BY dosen_id;",
                    "initial_difficulty": 1.0,
                    "topic_tags": ["aggregation", "count", "group"]
                },
                {
                    "question_id": "CH02-006",
                    "content": "Tampilkan dosen dengan total SKS > 10",
                    "target_query": "SELECT d.dosen_id, d.nama, SUM(m.sks) as total_sks FROM dosen d JOIN matakuliah m ON d.dosen_id = m.dosen_id GROUP BY d.dosen_id, d.nama HAVING SUM(m.sks) > 10;",
                    "initial_difficulty": 1.5,
                    "topic_tags": ["aggregation", "sum", "group", "having", "join"]
                },
                {
                    "question_id": "CH02-007",
                    "content": "Cari mahasiswa yang mengambil matakuliah dengan SKS >= 4",
                    "target_query": "SELECT DISTINCT f.nim FROM frs f JOIN matakuliah m ON f.kode_mk = m.kode_mk WHERE m.sks >= 4;",
                    "initial_difficulty": 2.0,
                    "topic_tags": ["basic", "select", "join", "distinct"]
                },
                {
                    "question_id": "CH02-008",
                    "content": "Hitung statistik SKS per jurusan mahasiswa",
                    "target_query": "SELECT m.jurusan, COUNT(DISTINCT f.nim) as jumlah_mhs, AVG(f.sks) as rata_sks FROM mahasiswa m JOIN frs f ON m.nim = f.nim GROUP BY m.jurusan;",
                    "initial_difficulty": 2.5,
                    "topic_tags": ["aggregation", "count", "avg", "group", "join"]
                },
                {
                    "question_id": "CH02-009",
                    "content": "Tampilkan 3 matakuliah dengan SKS tertinggi beserta nama dosen",
                    "target_query": "SELECT m.kode_mk, m.nama, m.sks, d.nama as nama_dosen FROM matakuliah m JOIN dosen d ON m.dosen_id = d.dosen_id ORDER BY m.sks DESC LIMIT 3;",
                    "initial_difficulty": 3.0,
                    "topic_tags": ["basic", "select", "join", "order", "limit"]
                },
                {
                    "question_id": "CH02-010",
                    "content": "Cari mahasiswa yang mengambil semua matakuliah dari dosen tertentu",
                    "target_query": "SELECT f.nim, COUNT(*) as jumlah_matkul FROM frs f JOIN matakuliah m ON f.kode_mk = m.kode_mk WHERE m.dosen_id = 'D001' GROUP BY f.nim HAVING COUNT(*) = (SELECT COUNT(*) FROM matakuliah WHERE dosen_id = 'D001');",
                    "initial_difficulty": 3.5,
                    "topic_tags": ["aggregation", "count", "group", "having", "subquery"]
                }
            ]
            
            # Soal-soal CH03 - Advanced Queries
            ch03_questions = [
                {
                    "question_id": "CH03-001",
                    "content": "Tampilkan mahasiswa dengan IPK di atas rata-rata jurusannya",
                    "target_query": "SELECT m.* FROM mahasiswa m WHERE m.ipk > (SELECT AVG(ipk) FROM mahasiswa WHERE jurusan = m.jurusan);",
                    "initial_difficulty": -0.5,
                    "topic_tags": ["subquery", "comparison", "avg"]
                },
                {
                    "question_id": "CH03-002",
                    "content": "Cari mahasiswa yang tidak mengambil matakuliah sama sekali",
                    "target_query": "SELECT m.* FROM mahasiswa m LEFT JOIN frs f ON m.nim = f.nim WHERE f.nim IS NULL;",
                    "initial_difficulty": 0.0,
                    "topic_tags": ["join", "left", "null"]
                },
                {
                    "question_id": "CH03-003",
                    "content": "Tampilkan ranking mahasiswa berdasarkan IPK per jurusan",
                    "target_query": "SELECT jurusan, nim, nama, ipk, RANK() OVER (PARTITION BY jurusan ORDER BY ipk DESC) as ranking FROM mahasiswa;",
                    "initial_difficulty": 0.5,
                    "topic_tags": ["window", "rank", "partition"]
                },
                {
                    "question_id": "CH03-004",
                    "content": "Hitung selisih SKS antar semester untuk setiap mahasiswa",
                    "target_query": "SELECT nim, semester, sks, LAG(sks) OVER (PARTITION BY nim ORDER BY semester) as sks_sebelumnya, sks - LAG(sks) OVER (PARTITION BY nim ORDER BY semester) as selisih FROM frs;",
                    "initial_difficulty": 1.0,
                    "topic_tags": ["window", "lag", "partition"]
                },
                {
                    "question_id": "CH03-005",
                    "content": "Cari mahasiswa dengan total SKS tertinggi di setiap angkatan",
                    "target_query": "SELECT angkatan, nim, total_sks FROM (SELECT m.angkatan, f.nim, SUM(f.sks) as total_sks, RANK() OVER (PARTITION BY m.angkatan ORDER BY SUM(f.sks) DESC) as ranking FROM mahasiswa m JOIN frs f ON m.nim = f.nim GROUP BY m.angkatan, f.nim) ranked WHERE ranking = 1;",
                    "initial_difficulty": 1.5,
                    "topic_tags": ["subquery", "window", "rank", "join"]
                },
                {
                    "question_id": "CH03-006",
                    "content": "Tampilkan mahasiswa yang mengambil matakuliah dengan dosen yang sama di semester berbeda",
                    "target_query": "SELECT DISTINCT f1.nim FROM frs f1 JOIN frs f2 ON f1.nim = f2.nim JOIN matakuliah m1 ON f1.kode_mk = m1.kode_mk JOIN matakuliah m2 ON f2.kode_mk = m2.kode_mk WHERE f1.semester != f2.semester AND m1.dosen_id = m2.dosen_id;",
                    "initial_difficulty": 2.0,
                    "topic_tags": ["join", "self", "distinct"]
                },
                {
                    "question_id": "CH03-007",
                    "content": "Hitung moving average SKS per mahasiswa (3 semester window)",
                    "target_query": "SELECT nim, semester, sks, AVG(sks) OVER (PARTITION BY nim ORDER BY semester ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg FROM frs;",
                    "initial_difficulty": 2.5,
                    "topic_tags": ["window", "avg", "rows"]
                },
                {
                    "question_id": "CH03-008",
                    "content": "Cari jurusan dengan peningkatan jumlah mahasiswa terbesar",
                    "target_query": "SELECT jurusan, MAX(jumlah) - MIN(jumlah) as peningkatan FROM (SELECT jurusan, angkatan, COUNT(*) as jumlah FROM mahasiswa GROUP BY jurusan, angkatan) yearly GROUP BY jurusan ORDER BY peningkatan DESC LIMIT 1;",
                    "initial_difficulty": 3.0,
                    "topic_tags": ["subquery", "group", "max", "min"]
                },
                {
                    "question_id": "CH03-009",
                    "content": "Tampilkan mahasiswa dengan pattern SKS naik-turun naik",
                    "target_query": "SELECT nim FROM (SELECT nim, sks, LAG(sks) OVER (PARTITION BY nim ORDER BY semester) as prev_sks, LAG(sks, 2) OVER (PARTITION BY nim ORDER BY semester) as prev2_sks FROM frs) pattern WHERE sks > prev_sks AND prev_sks < prev2_sks;",
                    "initial_difficulty": 3.5,
                    "topic_tags": ["window", "lag", "pattern"]
                },
                {
                    "question_id": "CH03-010",
                    "content": "Rekomendasikan teman sejurusan dengan pola SKS mirip",
                    "target_query": "WITH user_patterns AS (SELECT nim, STRING_AGG(sks::text, ',' ORDER BY semester) as pattern FROM frs GROUP BY nim), similarity AS (SELECT p1.nim as user1, p2.nim as user2, similarity(p1.pattern, p2.pattern) as score FROM user_patterns p1 JOIN user_patterns p2 ON p1.nim != p2.nim AND p1.pattern = p2.pattern) SELECT s.user1, s.user2 FROM similarity s JOIN mahasiswa m1 ON s.user1 = m1.nim JOIN mahasiswa m2 ON s.user2 = m2.nim WHERE m1.jurusan = m2.jurusan;",
                    "initial_difficulty": 4.0,
                    "topic_tags": ["cte", "string_agg", "similarity"]
                }
            ]
            
            # Schema definition diambil dari init_sandbox.sql
            schema_definition = """
-- Schema Database untuk Equilibria Sandbox
CREATE TABLE IF NOT EXISTS sandbox.mahasiswa (
    nim        VARCHAR(15)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    jurusan    VARCHAR(10)    NOT NULL,
    angkatan   INTEGER        NOT NULL,
    ipk        DECIMAL(3,2)   CHECK (ipk BETWEEN 0.0 AND 4.0)
);

CREATE TABLE IF NOT EXISTS sandbox.matakuliah (
    kode_mk    VARCHAR(10)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    sks        INTEGER        NOT NULL,
    dosen_id   VARCHAR(10)    NOT NULL
);

CREATE TABLE IF NOT EXISTS sandbox.dosen (
    dosen_id   VARCHAR(10)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL
);

CREATE TABLE IF NOT EXISTS sandbox.frs (
    nim        VARCHAR(10)    NOT NULL,
    kode_mk    VARCHAR(10)    NOT NULL,
    semester   INTEGER        NOT NULL,
    sks        INTEGER        NOT NULL,
    nilai      VARCHAR(2)      NOT NULL,
    PRIMARY KEY (nim, kode_mk, semester),
    FOREIGN KEY (nim) REFERENCES sandbox.mahasiswa(nim),
    FOREIGN KEY (kode_mk) REFERENCES sandbox.matakuliah(kode_mk)
);
"""
            
            # Insert soal CH01
            for q_data in ch01_questions:
                # Cek apakah soal sudah ada
                existing = await db.execute(
                    "SELECT question_id FROM questions WHERE question_id = :qid",
                    {"qid": q_data["question_id"]}
                )
                
                if not existing.fetchone():
                    question = Question(
                        question_id=q_data["question_id"],
                        module_id="CH01",
                        content=q_data["content"],
                        target_query=q_data["target_query"],
                        current_difficulty=q_data["initial_difficulty"],
                        topic_tags=q_data["topic_tags"],
                        is_active=True
                    )
                    db.add(question)
            
            # Insert soal CH02
            for q_data in ch02_questions:
                # Cek apakah soal sudah ada
                existing = await db.execute(
                    "SELECT question_id FROM questions WHERE question_id = :qid", 
                    {"qid": q_data["question_id"]}
                )
                
                if not existing.fetchone():
                    question = Question(
                        question_id=q_data["question_id"],
                        module_id="CH02",
                        content=q_data["content"],
                        target_query=q_data["target_query"],
                        current_difficulty=q_data["initial_difficulty"],
                        topic_tags=q_data["topic_tags"],
                        is_active=True
                    )
                    db.add(question)
            
            # Insert soal CH03
            for q_data in ch03_questions:
                # Cek apakah soal sudah ada
                existing = await db.execute(
                    "SELECT question_id FROM questions WHERE question_id = :qid", 
                    {"qid": q_data["question_id"]}
                )
                
                if not existing.fetchone():
                    question = Question(
                        question_id=q_data["question_id"],
                        module_id="CH03",
                        content=q_data["content"],
                        target_query=q_data["target_query"],
                        current_difficulty=q_data["initial_difficulty"],
                        topic_tags=q_data["topic_tags"],
                        is_active=True
                    )
                    db.add(question)
            
            await db.commit()
            
            print("✅ Successfully seeded SQL questions:")
            print(f"   - CH01 (Basic Selection): {len(ch01_questions)} questions")
            print(f"   - CH02 (Aggregation): {len(ch02_questions)} questions") 
            print(f"   - CH03 (Advanced Queries): {len(ch03_questions)} questions")
            print(f"   - Total: {len(ch01_questions) + len(ch02_questions) + len(ch03_questions)} questions")
            print("🎯 Difficulty ranges: CH01 [-2.0, 2.5], CH02 [-1.0, 3.5], CH03 [-0.5, 4.0]")
            
        except Exception as e:
            print(f"❌ Error seeding questions: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🚀 Starting SQL questions seed...")
    asyncio.run(seed_questions())
    print("✅ Seeding completed!")
