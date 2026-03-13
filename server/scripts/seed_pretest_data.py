# server/scripts/seed_pretest.py
"""
Pretest Seeding Script
Creates modules, questions, and test user for pretest endpoint testing.
Usage: python -m scripts.seed_pretest
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from uuid import UUID

from app.db.base import Base
from app.db.models.module import Module
from app.db.models.question import Question
from app.db.models.user_module_progress import UserModuleProgress
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


MODULES_DATA = [
    {
        "module_id": "CH01",
        "title": "Basic Selection",
        "description": "SELECT, WHERE, and basic filtering operations",
        "difficulty_min": 500.0,
        "difficulty_max": 800.0,
        "content_html": "<h1>Basic Selection</h1><p>Learn SELECT and WHERE clauses...</p>",
    },
    {
        "module_id": "CH02",
        "title": "Aggregation",
        "description": "GROUP BY, HAVING, and aggregate functions",
        "difficulty_min": 800.0,
        "difficulty_max": 1200.0,
        "content_html": "<h1>Aggregation</h1><p>Learn GROUP BY and aggregate functions...</p>",
    },
    {
        "module_id": "CH03",
        "title": "Advanced Querying",
        "description": "JOINs, Subqueries, and CTEs",
        "difficulty_min": 1200.0,
        "difficulty_max": 1500.0,
        "content_html": "<h1>Advanced Querying</h1><p>Learn JOINs and subqueries...</p>",
    },
]


QUESTIONS_DATA = [
    # CH01 - Basic Selection (Difficulty: 500-800)
    {
        "question_id": "CH01-Q001",
        "module_id": "CH01",
        "content": "Select all students with GPA greater than 3.5",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk > 3.5",
        "initial_difficulty": 600.0,
        "current_difficulty": 600.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q002",
        "module_id": "CH01",
        "content": "Select student names from semester 5",
        "target_query": "SELECT nama FROM mahasiswa WHERE semester = 5",
        "initial_difficulty": 550.0,
        "current_difficulty": 550.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q003",
        "module_id": "CH01",
        "content": "Find students with IPK between 3.0 and 4.0",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk BETWEEN 3.0 AND 4.0",
        "initial_difficulty": 650.0,
        "current_difficulty": 650.0,
        "topic_tags": ["SELECT", "WHERE", "BETWEEN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q004",
        "module_id": "CH01",
        "content": "Select students named Ahmad",
        "target_query": "SELECT * FROM mahasiswa WHERE nama = 'Ahmad'",
        "initial_difficulty": 500.0,
        "current_difficulty": 500.0,
        "topic_tags": ["SELECT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q005",
        "module_id": "CH01",
        "content": "Count total students in database",
        "target_query": "SELECT COUNT(*) FROM mahasiswa",
        "initial_difficulty": 700.0,
        "current_difficulty": 700.0,
        "topic_tags": ["SELECT", "COUNT"],
        "is_active": True,
    },
    
    # CH02 - Aggregation (Difficulty: 800-1200)
    {
        "question_id": "CH02-Q001",
        "module_id": "CH02",
        "content": "Group students by semester and count each",
        "target_query": "SELECT semester, COUNT(*) FROM mahasiswa GROUP BY semester",
        "initial_difficulty": 900.0,
        "current_difficulty": 900.0,
        "topic_tags": ["GROUP BY", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q002",
        "module_id": "CH02",
        "content": "Find average GPA per semester",
        "target_query": "SELECT semester, AVG(ipk) FROM mahasiswa GROUP BY semester",
        "initial_difficulty": 950.0,
        "current_difficulty": 950.0,
        "topic_tags": ["GROUP BY", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q003",
        "module_id": "CH02",
        "content": "Find semesters with more than 10 students",
        "target_query": "SELECT semester, COUNT(*) FROM mahasiswa GROUP BY semester HAVING COUNT(*) > 10",
        "initial_difficulty": 1100.0,
        "current_difficulty": 1100.0,
        "topic_tags": ["GROUP BY", "HAVING", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q004",
        "module_id": "CH02",
        "content": "Get maximum and minimum GPA",
        "target_query": "SELECT MAX(ipk), MIN(ipk) FROM mahasiswa",
        "initial_difficulty": 850.0,
        "current_difficulty": 850.0,
        "topic_tags": ["MAX", "MIN"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q005",
        "module_id": "CH02",
        "content": "Sum total credits per student",
        "target_query": "SELECT nim, SUM(sks) FROM frs GROUP BY nim",
        "initial_difficulty": 1000.0,
        "current_difficulty": 1000.0,
        "topic_tags": ["GROUP BY", "SUM"],
        "is_active": True,
    },
    
    # CH03 - Advanced Querying (Difficulty: 1200-1500)
    {
        "question_id": "CH03-Q001",
        "module_id": "CH03",
        "content": "Join mahasiswa with frs to get student courses",
        "target_query": "SELECT m.nama, f.kode_matkul FROM mahasiswa m JOIN frs f ON m.nim = f.nim",
        "initial_difficulty": 1300.0,
        "current_difficulty": 1300.0,
        "topic_tags": ["JOIN", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q002",
        "module_id": "CH03",
        "content": "Find students who haven't enrolled in any courses",
        "target_query": "SELECT m.* FROM mahasiswa m LEFT JOIN frs f ON m.nim = f.nim WHERE f.nim IS NULL",
        "initial_difficulty": 1400.0,
        "current_difficulty": 1400.0,
        "topic_tags": ["JOIN", "LEFT JOIN", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q003",
        "module_id": "CH03",
        "content": "Use subquery to find students above average GPA",
        "target_query": "SELECT * FROM mahasiswa WHERE ipk > (SELECT AVG(ipk) FROM mahasiswa)",
        "initial_difficulty": 1450.0,
        "current_difficulty": 1450.0,
        "topic_tags": ["SUBQUERY", "SELECT", "AVG"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q004",
        "module_id": "CH03",
        "content": "Use CTE to get semester statistics",
        "target_query": "WITH stats AS (SELECT semester, COUNT(*) as cnt FROM mahasiswa GROUP BY semester) SELECT * FROM stats WHERE cnt > 5",
        "initial_difficulty": 1500.0,
        "current_difficulty": 1500.0,
        "topic_tags": ["CTE", "WITH", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q005",
        "module_id": "CH03",
        "content": "Three-table join: mahasiswa, frs, matakuliah",
        "target_query": "SELECT m.nama, mk.nama_matkul FROM mahasiswa m JOIN frs f ON m.nim = f.nim JOIN matakuliah mk ON f.kode_matkul = mk.kode_matkul",
        "initial_difficulty": 1350.0,
        "current_difficulty": 1350.0,
        "topic_tags": ["JOIN", "MULTI-JOIN"],
        "is_active": True,
    },
]


# TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


async def seed_database():
    async with AsyncSessionLocal() as session:
        try:
            print("Starting database seeding...")
            
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
            
            # Seed User Module Progress (CH01 unlocked for test user)
            # print("Seeding user module progress...")
            # progress = UserModuleProgress(
            #     user_id=UUID(TEST_USER_ID),
            #     module_id="CH01",
            #     is_completed=False,
            # )
            # session.add(progress)
            # print(f"  CH01 unlocked for test user")
            
            await session.commit()
            
            # Summary
            print("\n" + "=" * 50)
            print("SEEDING COMPLETED")
            print("=" * 50)
            print(f"Modules: {len(MODULES_DATA)}")
            print(f"Questions: {len(QUESTIONS_DATA)}")
            print(f"Difficulty Range: 500 - 1500 (Elo Scale)")
            print("=" * 50)
            print("\nTest Pretest Flow:")
            print("  1. POST /api/v1/pretest/start")
            print("  2. GET /api/v1/pretest/question/current")
            print("  3. POST /api/v1/pretest/submit (x5)")
            print("=" * 50)
            
        except Exception as e:
            await session.rollback()
            print(f"\nSeeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())