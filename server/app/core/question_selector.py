"""
Question Selection Strategy - Tech Specs v4.2 Section 6.2

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
    Item Selection Strategy per Tech Specs v4.2 Section 6.2.
    
    Args:
        user_theta: Rating theta pengguna saat ini
        module_id: ID modul (CH01, CH02, dll)
        served_question_ids: Daftar ID soal yang sudah di-serve di session ini
        db: Database session
        
    Returns:
        Question yang dipilih atau None jika tidak ada soal tersedia
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
    
    # Ambil top 5 dengan distance terkecil
    top_5_questions = [item[0] for item in questions_with_distance[:5]]
    
    # Random pick 1 dari top 5
    selected_question = random.choice(top_5_questions)
    
    return selected_question


async def select_pretest_question(
    current_theta: float,
    question_index: int,
    answered_ids: List[str],
    db: AsyncSession
) -> Optional[Question]:
    """
    Pemilihan soal untuk pretest.
    Menggunakan current_theta untuk semua soal (tidak ada difficulty 0 khusus).
    
    Args:
        current_theta: Rating theta saat ini untuk pretest
        question_index: Indeks soal saat ini (0-based) - tidak digunakan untuk selection
        answered_ids: Daftar ID soal yang sudah dijawab
        db: Database session
        
    Returns:
        Question yang dipilih atau None jika tidak ada soal tersedia
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
    
    # Ambil top 5 paling dekat, lalu random 1
    top_5 = questions_sorted[:5]
    if not top_5:
        return None
        
    selected_question = random.choice(top_5)
    return selected_question
