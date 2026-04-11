import math
import numpy
from typing import Tuple

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AssessmentLog

# === Konstanta sesuai Vesin et al. (2022) - Tech Specs v4.2 ===
BASE_RATING = 1300.0  # Rating awal semua siswa
RATING_MIN = 0
RATING_MAX = 2000.0  
K_FACTORS = {
    'novice': 30,    # 0-9 attempts
    'intermediate': 20,  # 10-24 attempts
    'advanced': 15,  # 25-49 attempts
    'expert': 10     # 50+ attempts
}
TIME_DISCRIMINATION = 1e-6 # parameter ai di rumus
DEFAULT_TIME_LIMIT = 300000  # di = 5 menit dalam milidetik

def calculate_initial_theta(correct_count: int, total_questions: int = 5) -> float:
    """
    Kalibrasi pre-test untuk skala [0, 2000] dengan baseline 1300
    Memetakan 0-5 benar ke rentang [1100, 1500] di sekitar baseline 1300
    
    Input:
        correct_count: jumlah jawaban benar (0-5)
        total_questions: total pertanyaan di pretest (default 5)
    Output:
        rating theta awal [1100, 1500]
    """
    base_rating = 1300.0
    baseline_correct = 2.5
    multiplier = 80.0
    
    adjustment = (correct_count - baseline_correct) * multiplier
    theta = base_rating + adjustment
    
    return max(1100, min(1500, theta))

def calculate_expected_score(student_rating: float, question_difficulty: float)->float:
    '''
    Vesin et al. (2022)
    Probabilitas siswa berhasil menjawab soal
    '''
    
    rating_diff = student_rating - question_difficulty
    return 1.0 / (1.0 + math.pow(10, rating_diff / 400.0))

def get_k_factor(total_attempts: int)->int:
    '''
    Spesifikasi 6.2: K-Factor decay
    Faktor pengali untuk perubahan rating,
    lebih sensitif di awal dan lebih stabil di akhir (konvergensi)
    '''
    if total_attempts < 10:
        return K_FACTORS['novice']
    elif total_attempts < 25:
        return K_FACTORS['intermediate']
    elif total_attempts < 50:
        return K_FACTORS['advanced']
    else:
        return K_FACTORS['expert']

def calculate_success_rate(
    successful_attempts: int,  # Ai: successful attempts (0 atau 1 di prototype)
    overall_attempts: int,     # A: total attempts (1, 2, atau 3)
    correct_tests: int,        # Tc: unit tests passed - di-map ke binary sandbox result
    performed_tests: int,      # Tp: unit tests performed - selalu 1 di prototype
    time_used_ms: int,         # ti: waktu yang dipakai
    time_limit_ms: int = DEFAULT_TIME_LIMIT,
    discrimination: float = TIME_DISCRIMINATION
) -> float:
    """
    Implementasi penuh Vesin Eq. 3 dengan penyederhanaan rasio tes biner.
    
    Untuk prototipe: test_ratio = Tc/Tp akan selalu 1.0 (benar) atau 0.0 (salah)
    karena sandbox SQL hanya menghasilkan hasil pass/fail biner.
    
    Input:
        successful_attempts: Ai (0 atau 1 di prototipe)
        overall_attempts: A (1, 2, atau 3)
        correct_tests: Tc (1 jika benar, 0 jika salah)
        performed_tests: Tp (selalu 1 di prototipe)
        time_used_ms: ti dalam milidetik
        time_limit_ms: di dalam milidetik (default 5 menit)
        discrimination: parameter ai (default 0.001)
    
    Output:
        Success rate W ∈ [0.0, 2.0]
    """
    # Lindungi dari pembagian dengan nol
    if overall_attempts == 0 or performed_tests == 0:
        return 0.0
    
    # Rasio attempt: Ai / A
    # Gradasi yang mungkin: {1.0, 0.5, 0.33, 0.0}
    attempt_ratio = successful_attempts / overall_attempts
    
    # Rasio tes: Tc / Tp
    # Di prototipe: 1.0 jika benar, 0.0 jika salah (hasil biner sandbox)
    # Ini adalah penyederhanaan dari pendekatan unit testing Vesin
    test_ratio = correct_tests / performed_tests
    
    # Komponen waktu: ai * (di - ti), dibatasi di 0
    time_component = discrimination * (time_limit_ms - time_used_ms)
    time_component = max(0.0, time_component)
    
    # Vesin Eq. 3: W = (Ai/A) * (Tc/Tp) * (1 + ai*di - ai*ti)
    W = attempt_ratio * test_ratio * (1.0 + time_component)
    
    # Batasi ke rentang yang wajar [0.0, 2.0]
    return max(0.0, min(2.0, W))

def update_elo_ratings(
    student_rating: float,
    question_difficulty: float,
    success_rate: float,
    k_factor: int
) -> tuple[float, float]:

    # Hitung skor yang diharapkan
    expected_score = calculate_expected_score(student_rating, question_difficulty)
    
    # Ri = Ri−1 + K · (W − We)
    new_student_rating = student_rating + k_factor * (success_rate - expected_score)
    
    # Dj = Dj−1 + K · (We − W)
    new_question_difficulty = question_difficulty + k_factor * (expected_score - success_rate)
    
    # Batasi ke rentang yang masuk akal
    new_student_rating = max(RATING_MIN, min(RATING_MAX, new_student_rating))
    new_question_difficulty = max(RATING_MIN, min(RATING_MAX, new_question_difficulty))
    
    return new_student_rating, new_question_difficulty

async def detect_stagnation(
    user_id: str,
    current_module_id: str,
    db: AsyncSession
) -> bool:
    """
    Spesifikasi 6.3: Stagnation Detection (ε = 165)

    Dipanggil setelah setiap `/next`.
    Mengambil 5 final attempt terakhir lintas sesi (konvergensi bersifat global).

    Args:
        user_id: ID user untuk query assessment_logs
        current_module_id: ID modul saat ini (skip jika CH03)
        db: AsyncSession untuk query database

    Returns:
        bool: True jika variance < 165 (stagnation detected), False otherwise
    """
    # Tidak ada stagnation jika user sudah di chapter tertinggi
    # Konvergensi di CH03 adalah tujuan, bukan masalah
    if current_module_id == "CH03":
        return False

    # Ambil 5 final attempt terakhir lintas sesi (konvergensi bersifat global)
    result = await db.execute(
        select(AssessmentLog)
        .where(AssessmentLog.user_id == user_id)
        .where(AssessmentLog.is_final_attempt == True)
        .order_by(AssessmentLog.timestamp.desc())
        .limit(5)
    )
    last_5_logs = result.scalars().all()

    if len(last_5_logs) < 5:
        return False  # Belum cukup data untuk deteksi

    # Calculate theta deltas
    deltas = [
        log.theta_after - log.theta_before
        for log in last_5_logs
        if log.theta_before is not None and log.theta_after is not None
    ]

    if len(deltas) < 5:
        return False

    variance = numpy.var(deltas)  # population variance
    return variance < 165  # ε = 165

def check_fallback_trigger(
    group_assignment: str,
    current_module_id: str,
    is_next_module_unlocked: bool,
    recent_logs: list
) -> bool:
    """
    Spesifikasi 6.3: Fallback Trigger (Safety Net untuk Lab Study)
    
    Trigger berbasis rasio jawaban salah (>50% dari N=8) untuk memastikan
    intervensi terpicu ketika user mengalami kesulitan berkelanjutan.
    
    Logika: Ambil 8 final attempt terakhir di chapter ini. Jika lebih dari
    separuhnya (>4) salah DAN chapter berikutnya belum unlock, trigger stagnation.

    Args:
        group_assignment: 'A' atau 'B' - hanya aktif untuk Grup A
        current_module_id: ID modul saat ini (skip jika CH03)
        is_next_module_unlocked: True jika chapter berikutnya sudah unlocked
        recent_logs: List AssessmentLog (8 terakhir, sudah di-order desc)

    Returns:
        bool: True jika fallback trigger terpenuhi (>4 salah dari 8), False otherwise
    """
    # Hanya aktif untuk Grup A
    if group_assignment != 'A':
        return False
    
    # Skip jika user sudah di chapter tertinggi (CH03)
    if current_module_id == "CH03":
        return False
    
    # Skip jika chapter berikutnya sudah unlocked
    if is_next_module_unlocked:
        return False
    
    # Periksa apakah sudah ada minimal 8 attempt
    if len(recent_logs) < 8:
        return False
    
    # Hitung jumlah jawaban salah
    wrong_count = sum(1 for log in recent_logs if not log.is_correct)
    
    # Trigger jika lebih dari separuh (>4) salah
    return wrong_count > 4