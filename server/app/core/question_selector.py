"""
Strategi Pemilihan Soal
Algoritma pemilihan soal adaptif untuk pretest dan chapter sessions.
Digunakan bersama oleh PreTest dan Assessment Session APIs.
"""

import random
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Question


async def select_next_question(
    user_theta: float,
    module_id: str,
    served_question_ids: List[str],
    db: AsyncSession
) -> Optional[Question]:
    """
    Item Selection Strategy
    """
    # Filter soal yang aktif dan belum di-serve
    result = await db.execute(
        select(Question)
        .where(Question.module_id == module_id)
        .where(Question.is_active == True)
        .where(Question.question_id.notin_(served_question_ids))
    )
    questions = result.scalars().all()
    
    # Jika tidak ada soal tersedia, trigger session end
    if not questions:
        return None
    
    # Hitung distance untuk setiap soal
    questions_with_distance = []
    for question in questions:
        distance = abs(question.current_difficulty - user_theta)
        questions_with_distance.append((question, distance))
    
    # Sort berdasarkan distance (terkecil pertama)
    questions_with_distance.sort(key=lambda x: x[1])
    
    # Ambil top 2 dengan distance terkecil
    top_2_questions = [item[0] for item in questions_with_distance[:2]]
    
    # Random pick 1 dari top 2
    selected_question = random.choice(top_2_questions)
    
    return selected_question


async def select_pretest_question(
    current_theta: float,
    question_index: int,
    answered_ids: List[str],
    db: AsyncSession
) -> Optional[Question]:
    """
    Pemilihan soal untuk pretest.
    Menggunakan current_theta untuk semua soal
    """
    # Filter soal CH01 yang belum dijawab
    result = await db.execute(
        select(Question)
        .where(Question.question_id.notin_(answered_ids))
        .where(Question.is_active == True)
        .where(Question.module_id == "CH01")
    )
    questions = result.scalars().all()
    
    if not questions:
        return None
    
    # Gunakan current_theta untuk semua soal pretest
    target_difficulty = current_theta
    
    # Gunakan algoritma distance yang sama
    questions_sorted = sorted(questions, key=lambda x: abs(x.current_difficulty - target_difficulty))
    
    # Ambil top 2 paling dekat, lalu random 1
    top_2_questions = questions_sorted[:2]
    if not top_2_questions:
        return None
        
    selected_question = random.choice(top_2_questions)
    return selected_question
