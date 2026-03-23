# server/scripts/seed_sql_questions.py
"""
SQL Questions Seeding Script
Creates modules and SQL questions for adaptive assessment system.
Usage: python -m scripts.seed_sql_questions
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.db.base import Base
from app.db.models.module import Module
from app.db.models.question import Question
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


MODULES_DATA = [
    {
        "module_id": "CH01",
        "title": "Basic Selection",
        "description": "SELECT, WHERE, and basic filtering operations",
        "difficulty_min": 1000.0,
        "difficulty_max": 1400.0,
        "unlock_theta_threshold": 0.0,  # Always open
        "order_index": 1,
        "content_html": "<h1>Basic Selection</h1><p>Learn SELECT and WHERE clauses...</p>",
    },
    {
        "module_id": "CH02",
        "title": "Aggregation",
        "description": "GROUP BY, HAVING, and aggregate functions",
        "difficulty_min": 1200.0,
        "difficulty_max": 1600.0,
        "unlock_theta_threshold": 1300.0,
        "order_index": 2,
        "content_html": "<h1>Aggregation</h1><p>Learn GROUP BY and aggregate functions...</p>",
    },
    {
        "module_id": "CH03",
        "title": "Advanced Querying",
        "description": "JOINs, Subqueries, and CTEs",
        "difficulty_min": 1400.0,
        "difficulty_max": 1800.0,
        "unlock_theta_threshold": 1600.0,
        "order_index": 3,
        "content_html": "<h1>Advanced Querying</h1><p>Learn JOINs and subqueries...</p>",
    },
]


QUESTIONS_DATA = [
    # CH01 - Basic Selection (Difficulty: 1000-1400) - 15 questions
    {
        "question_id": "CH01-Q001",
        "module_id": "CH01",
        "content": "Select all students with GPA greater than 3.5",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk > 3.5",
        "initial_difficulty": 1050.0,
        "current_difficulty": 1050.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q002",
        "module_id": "CH01",
        "content": "Select student names from semester 5",
        "target_query": "SELECT nama FROM mahasiswa WHERE angkatan = 2020",
        "initial_difficulty": 1000.0,
        "current_difficulty": 1000.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q003",
        "module_id": "CH01",
        "content": "Find students with IPK between 3.0 and 4.0",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk BETWEEN 3.0 AND 4.0",
        "initial_difficulty": 1100.0,
        "current_difficulty": 1100.0,
        "topic_tags": ["SELECT", "WHERE", "BETWEEN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q004",
        "module_id": "CH01",
        "content": "Select students named Ahmad",
        "target_query": "SELECT * FROM mahasiswa WHERE nama LIKE '%Ahmad%'",
        "initial_difficulty": 1080.0,
        "current_difficulty": 1080.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q005",
        "module_id": "CH01",
        "content": "Count total students in database",
        "target_query": "SELECT COUNT(*) FROM mahasiswa",
        "initial_difficulty": 1150.0,
        "current_difficulty": 1150.0,
        "topic_tags": ["SELECT", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q006",
        "module_id": "CH01",
        "content": "Select students from IF department ordered by GPA descending",
        "target_query": "SELECT * FROM mahasiswa WHERE jurusan = 'IF' ORDER BY ipk DESC",
        "initial_difficulty": 1120.0,
        "current_difficulty": 1120.0,
        "topic_tags": ["SELECT", "WHERE", "ORDER BY"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q007",
        "module_id": "CH01",
        "content": "Find students with GPA exactly 4.0",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk = 4.0",
        "initial_difficulty": 1020.0,
        "current_difficulty": 1020.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q008",
        "module_id": "CH01",
        "content": "Select first 5 students ordered by NIM",
        "target_query": "SELECT * FROM mahasiswa ORDER BY nim LIMIT 5",
        "initial_difficulty": 1070.0,
        "current_difficulty": 1070.0,
        "topic_tags": ["SELECT", "ORDER BY", "LIMIT"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q009",
        "module_id": "CH01",
        "content": "Find students not from IF department",
        "target_query": "SELECT * FROM mahasiswa WHERE jurusan != 'IF'",
        "initial_difficulty": 1030.0,
        "current_difficulty": 1030.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q010",
        "module_id": "CH01",
        "content": "Select student names and GPA for students with GPA above 3.0",
        "target_query": "SELECT nama, ipk FROM mahasiswa WHERE ipk > 3.0",
        "initial_difficulty": 1060.0,
        "current_difficulty": 1060.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q011",
        "module_id": "CH01",
        "content": "Find students from 2022 angkatan with GPA below 3.0",
        "target_query": "SELECT * FROM mahasiswa WHERE angkatan = 2022 AND ipk < 3.0",
        "initial_difficulty": 1090.0,
        "current_difficulty": 1090.0,
        "topic_tags": ["SELECT", "WHERE", "AND"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q012",
        "module_id": "CH01",
        "content": "Select distinct departments from students table",
        "target_query": "SELECT DISTINCT jurusan FROM mahasiswa",
        "initial_difficulty": 1130.0,
        "current_difficulty": 1130.0,
        "topic_tags": ["SELECT", "DISTINCT"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q013",
        "module_id": "CH01",
        "content": "Find students whose names start with 'A'",
        "target_query": "SELECT * FROM mahasiswa WHERE nama LIKE 'A%'",
        "initial_difficulty": 1110.0,
        "current_difficulty": 1110.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q014",
        "module_id": "CH01",
        "content": "Count students in each department",
        "target_query": "SELECT jurusan, COUNT(*) FROM mahasiswa GROUP BY jurusan",
        "initial_difficulty": 1180.0,
        "current_difficulty": 1180.0,
        "topic_tags": ["SELECT", "COUNT", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q015",
        "module_id": "CH01",
        "content": "Select students with GPA greater than or equal to 3.75",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk >= 3.75",
        "initial_difficulty": 1040.0,
        "current_difficulty": 1040.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    
    # CH02 - Aggregation (Difficulty: 1200-1600) - 15 questions
    {
        "question_id": "CH02-Q001",
        "module_id": "CH02",
        "content": "Group students by angkatan and count each",
        "target_query": "SELECT angkatan, COUNT(*) FROM mahasiswa GROUP BY angkatan",
        "initial_difficulty": 1250.0,
        "current_difficulty": 1250.0,
        "topic_tags": ["GROUP BY", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q002",
        "module_id": "CH02",
        "content": "Find average GPA per angkatan",
        "target_query": "SELECT angkatan, AVG(ipk) FROM mahasiswa GROUP BY angkatan",
        "initial_difficulty": 1300.0,
        "current_difficulty": 1300.0,
        "topic_tags": ["GROUP BY", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q003",
        "module_id": "CH02",
        "content": "Find angkatan with more than 5 students",
        "target_query": "SELECT angkatan, COUNT(*) FROM mahasiswa GROUP BY angkatan HAVING COUNT(*) > 5",
        "initial_difficulty": 1450.0,
        "current_difficulty": 1450.0,
        "topic_tags": ["GROUP BY", "HAVING", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q004",
        "module_id": "CH02",
        "content": "Get maximum and minimum GPA",
        "target_query": "SELECT MAX(ipk), MIN(ipk) FROM mahasiswa",
        "initial_difficulty": 1220.0,
        "current_difficulty": 1220.0,
        "topic_tags": ["MAX", "MIN"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q005",
        "module_id": "CH02",
        "content": "Sum total credits per student from FRS table",
        "target_query": "SELECT nim, SUM(sks) FROM frs GROUP BY nim",
        "initial_difficulty": 1350.0,
        "current_difficulty": 1350.0,
        "topic_tags": ["GROUP BY", "SUM"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q006",
        "module_id": "CH02",
        "content": "Find average credits per angkatan",
        "target_query": "SELECT m.angkatan, AVG(f.sks) FROM mahasiswa m JOIN frs f ON m.nim = f.nim GROUP BY m.angkatan",
        "initial_difficulty": 1420.0,
        "current_difficulty": 1420.0,
        "topic_tags": ["GROUP BY", "AVG", "JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q007",
        "module_id": "CH02",
        "content": "Count students per department with GPA above average",
        "target_query": "SELECT jurusan, COUNT(*) FROM mahasiswa WHERE ipk > (SELECT AVG(ipk) FROM mahasiswa) GROUP BY jurusan",
        "initial_difficulty": 1480.0,
        "current_difficulty": 1480.0,
        "topic_tags": ["GROUP BY", "COUNT", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q008",
        "module_id": "CH02",
        "content": "Find departments with average GPA above 3.5",
        "target_query": "SELECT jurusan, AVG(ipk) FROM mahasiswa GROUP BY jurusan HAVING AVG(ipk) > 3.5",
        "initial_difficulty": 1380.0,
        "current_difficulty": 1380.0,
        "topic_tags": ["GROUP BY", "HAVING", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q009",
        "module_id": "CH02",
        "content": "Count total courses taken by each student",
        "target_query": "SELECT nim, COUNT(*) FROM frs GROUP BY nim",
        "initial_difficulty": 1270.0,
        "current_difficulty": 1270.0,
        "topic_tags": ["GROUP BY", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q010",
        "module_id": "CH02",
        "content": "Find students taking more than 3 courses",
        "target_query": "SELECT nim, COUNT(*) FROM frs GROUP BY nim HAVING COUNT(*) > 3",
        "initial_difficulty": 1400.0,
        "current_difficulty": 1400.0,
        "topic_tags": ["GROUP BY", "HAVING", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q011",
        "module_id": "CH02",
        "content": "Calculate total SKS per department",
        "target_query": "SELECT m.jurusan, SUM(f.sks) FROM mahasiswa m JOIN frs f ON m.nim = f.nim GROUP BY m.jurusan",
        "initial_difficulty": 1430.0,
        "current_difficulty": 1430.0,
        "topic_tags": ["GROUP BY", "SUM", "JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q012",
        "module_id": "CH02",
        "content": "Find angkatan with highest average GPA",
        "target_query": "SELECT angkatan, AVG(ipk) as avg_gpa FROM mahasiswa GROUP BY angkatan ORDER BY avg_gpa DESC LIMIT 1",
        "initial_difficulty": 1460.0,
        "current_difficulty": 1460.0,
        "topic_tags": ["GROUP BY", "AVG", "ORDER BY", "LIMIT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q013",
        "module_id": "CH02",
        "content": "Count courses per semester for each student",
        "target_query": "SELECT nim, semester, COUNT(*) FROM frs GROUP BY nim, semester",
        "initial_difficulty": 1320.0,
        "current_difficulty": 1320.0,
        "topic_tags": ["GROUP BY", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q014",
        "module_id": "CH02",
        "content": "Find students with total SKS above 10",
        "target_query": "SELECT nim, SUM(sks) as total_sks FROM frs GROUP BY nim HAVING SUM(sks) > 10",
        "initial_difficulty": 1370.0,
        "current_difficulty": 1370.0,
        "topic_tags": ["GROUP BY", "HAVING", "SUM"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q015",
        "module_id": "CH02",
        "content": "Calculate average SKS per course for each student",
        "target_query": "SELECT nim, AVG(sks) FROM frs GROUP BY nim",
        "initial_difficulty": 1280.0,
        "current_difficulty": 1280.0,
        "topic_tags": ["GROUP BY", "AVG"],
        "is_active": True,
    },
    
    # CH03 - Advanced Querying (Difficulty: 1400-1800) - 15 questions
    {
        "question_id": "CH03-Q001",
        "module_id": "CH03",
        "content": "Join mahasiswa with frs to get student courses",
        "target_query": "SELECT m.nama, f.kode_mk FROM mahasiswa m JOIN frs f ON m.nim = f.nim",
        "initial_difficulty": 1450.0,
        "current_difficulty": 1450.0,
        "topic_tags": ["JOIN", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q002",
        "module_id": "CH03",
        "content": "Find students who haven't enrolled in any courses",
        "target_query": "SELECT m.* FROM mahasiswa m LEFT JOIN frs f ON m.nim = f.nim WHERE f.nim IS NULL",
        "initial_difficulty": 1550.0,
        "current_difficulty": 1550.0,
        "topic_tags": ["JOIN", "LEFT JOIN", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q003",
        "module_id": "CH03",
        "content": "Use subquery to find students above average GPA",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk > (SELECT AVG(ipk) FROM mahasiswa)",
        "initial_difficulty": 1600.0,
        "current_difficulty": 1600.0,
        "topic_tags": ["SUBQUERY", "SELECT", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q004",
        "module_id": "CH03",
        "content": "Use CTE to get angkatan statistics",
        "target_query": "WITH stats AS (SELECT angkatan, COUNT(*) as cnt FROM mahasiswa GROUP BY angkatan) SELECT * FROM stats WHERE cnt > 5",
        "initial_difficulty": 1650.0,
        "current_difficulty": 1650.0,
        "topic_tags": ["CTE", "WITH", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q005",
        "module_id": "CH03",
        "content": "Three-table join: mahasiswa, frs, matakuliah",
        "target_query": "SELECT m.nama, mk.nama_mk FROM mahasiswa m JOIN frs f ON m.nim = f.nim JOIN matakuliah mk ON f.kode_mk = mk.kode_mk",
        "initial_difficulty": 1500.0,
        "current_difficulty": 1500.0,
        "topic_tags": ["JOIN", "MULTI-JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q006",
        "module_id": "CH03",
        "content": "Find students taking courses with SKS above average",
        "target_query": "SELECT DISTINCT m.nama FROM mahasiswa m JOIN frs f ON m.nim = f.nim WHERE f.sks > (SELECT AVG(sks) FROM frs)",
        "initial_difficulty": 1580.0,
        "current_difficulty": 1580.0,
        "topic_tags": ["JOIN", "SUBQUERY", "DISTINCT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q007",
        "module_id": "CH03",
        "content": "Use correlated subquery to find top student per department",
        "target_query": "SELECT * FROM mahasiswa m1 WHERE ipk = (SELECT MAX(ipk) FROM mahasiswa m2 WHERE m2.jurusan = m1.jurusan)",
        "initial_difficulty": 1700.0,
        "current_difficulty": 1700.0,
        "topic_tags": ["SUBQUERY", "CORRELATED"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q008",
        "module_id": "CH03",
        "content": "Find students with GPA above department average",
        "target_query": "SELECT * FROM mahasiswa m1 WHERE ipk > (SELECT AVG(ipk) FROM mahasiswa m2 WHERE m2.jurusan = m1.jurusan)",
        "initial_difficulty": 1620.0,
        "current_difficulty": 1620.0,
        "topic_tags": ["SUBQUERY", "CORRELATED"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q009",
        "module_id": "CH03",
        "content": "Use EXISTS to find students enrolled in specific courses",
        "target_query": "SELECT * FROM mahasiswa m WHERE EXISTS (SELECT 1 FROM frs f WHERE f.nim = m.nim AND f.kode_mk = 'IF2240')",
        "initial_difficulty": 1680.0,
        "current_difficulty": 1680.0,
        "topic_tags": ["EXISTS", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q010",
        "module_id": "CH03",
        "content": "Find students not taking any courses in current semester",
        "target_query": "SELECT * FROM mahasiswa m WHERE NOT EXISTS (SELECT 1 FROM frs f WHERE f.nim = m.nim)",
        "initial_difficulty": 1560.0,
        "current_difficulty": 1560.0,
        "topic_tags": ["NOT EXISTS", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q011",
        "module_id": "CH03",
        "content": "Use window function to rank students by GPA",
        "target_query": "SELECT nama, ipk, RANK() OVER (ORDER BY ipk DESC) as ranking FROM mahasiswa",
        "initial_difficulty": 1720.0,
        "current_difficulty": 1720.0,
        "topic_tags": ["WINDOW", "RANK"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q012",
        "module_id": "CH03",
        "content": "Use window function to calculate GPA difference from average",
        "target_query": "SELECT nama, ipk, ipk - AVG(ipk) OVER () as diff_from_avg FROM mahasiswa",
        "initial_difficulty": 1750.0,
        "current_difficulty": 1750.0,
        "topic_tags": ["WINDOW", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q013",
        "module_id": "CH03",
        "content": "Find students with GPA above median using window function",
        "target_query": "SELECT * FROM (SELECT *, PERCENTILE_CONT(0.5) OVER () as median_gpa FROM mahasiswa) ranked WHERE ipk > median_gpa",
        "initial_difficulty": 1780.0,
        "current_difficulty": 1780.0,
        "topic_tags": ["WINDOW", "PERCENTILE_CONT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q014",
        "module_id": "CH03",
        "content": "Use multiple CTEs for complex analysis",
        "target_query": "WITH dept_avg AS (SELECT jurusan, AVG(ipk) as avg_gpa FROM mahasiswa GROUP BY jurusan), student_rank AS (SELECT *, RANK() OVER (PARTITION BY jurusan ORDER BY ipk DESC) as rank FROM mahasiswa) SELECT sr.nama, sr.jurusan, sr.ipk, da.avg_gpa FROM student_rank sr JOIN dept_avg da ON sr.jurusan = da.jurusan WHERE sr.rank = 1",
        "initial_difficulty": 1800.0,
        "current_difficulty": 1800.0,
        "topic_tags": ["CTE", "WINDOW", "JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q015",
        "module_id": "CH03",
        "content": "Find students with GPA above 75th percentile",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk > (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ipk) FROM mahasiswa)",
        "initial_difficulty": 1740.0,
        "current_difficulty": 1740.0,
        "topic_tags": ["PERCENTILE_CONT", "SUBQUERY"],
        "is_active": True,
    },
]


async def seed_database():
    async with AsyncSessionLocal() as session:
        try:
            print("Starting SQL questions database seeding...")
            
            # Seed Modules
            print("Seeding modules...")
            for module_data in MODULES_DATA:
                result = await session.execute(
                    text("SELECT 1 FROM modules WHERE module_id = :module_id"),
                    {"module_id": module_data["module_id"]}
                )
                if result.fetchone():
                    print(f"  Module {module_data['module_id']} already exists")
                    continue
                
                module = Module(**module_data)
                session.add(module)
                print(f"  Created module {module_data['module_id']}")
            
            await session.commit()
            
            # Seed Questions
            print("Seeding questions...")
            for question_data in QUESTIONS_DATA:
                result = await session.execute(
                    text("SELECT 1 FROM questions WHERE question_id = :question_id"),
                    {"question_id": question_data["question_id"]}
                )
                if result.fetchone():
                    print(f"  Question {question_data['question_id']} already exists")
                    continue
                
                question = Question(**question_data)
                session.add(question)
                print(f"  Created question {question_data['question_id']} (D={question_data['current_difficulty']})")
            
            await session.commit()
            
            # Summary
            print("\n" + "=" * 50)
            print("SQL QUESTIONS SEEDING COMPLETED")
            print("=" * 50)
            print(f"Modules: {len(MODULES_DATA)}")
            print(f"Questions: {len(QUESTIONS_DATA)}")
            print(f"CH01 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH01'])}")
            print(f"CH02 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH02'])}")
            print(f"CH03 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH03'])}")
            print(f"Difficulty Range: 1000 - 1800 (Elo Scale)")
            print("=" * 50)
            
        except Exception as e:
            await session.rollback()
            print(f"\nSeeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
