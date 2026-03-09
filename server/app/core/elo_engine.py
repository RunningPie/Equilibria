import math
from typing import Tuple

# === Constants per Vesin et al. (2022) ===
BASE_RATING = 1000.0  # Rating awal semua siswa
RATING_MIN = 0
RATING_MAX = 10000.0
K_FACTORS = {
    'novice': 30,    # 0-9 attempts
    'intermediate': 20,  # 10-24 attempts
    'advanced': 15,  # 25-49 attempts
    'expert': 10     # 50+ attempts
}
TIME_DISCRIMINATION = 0.001  # parameter ai di rumus
DEFAULT_TIME_LIMIT = 300000  # di = 5 minutes in milliseconds

def calculate_initial_theta(correct_count: int, total_questions: int = 5) -> float:
    """
    Kalibrasi pre-test
    0-5 betul menjadi rating 500-1500
    
    Input:
        correct_count: betulnya berapa (0-5)
        total_questions: total pertanyaan di pretest (default 5)
    Output:
        rating awal
    """
    base_rating = BASE_RATING  # 1000
    baseline_correct = total_questions / 2.0  # 2.5
    multiplier = 160.0  # Max ±400 from base (500-1500 range)
    
    adjustment = (correct_count - baseline_correct) * multiplier
    theta = base_rating + adjustment
    
    return max(500, min(1500, theta))

def calculate_expected_score(student_rating: float, question_difficulty: float)->float:
    '''
    Vesin et al. (2022)
    Probabilitas siswa berhasil menjawab soal
    '''
    
    rating_diff = student_rating - question_difficulty
    return 1.0 / (1.0 + math.pow(10, rating_diff / 400.0))

def get_k_factor(total_attempts: int)->int:
    '''
    Spek 6.2: K-Factor decay
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
    successful_attempts: int,
    overall_attempts: int,
    correct_tests: int,
    performed_tests: int,
    time_used_ms: int,
    time_limit_ms: int = DEFAULT_TIME_LIMIT,
    discrimination: float = TIME_DISCRIMINATION
) -> float:
    # Guardrail pembagian 0
    if overall_attempts == 0 or performed_tests == 0:
        return 0.0
    
    attempt_ratio = (successful_attempts + overall_attempts) / (2.0 * overall_attempts)
    
    test_ratio = correct_tests / performed_tests
    
    # Time component (ai * di - ai * ti)
    # Dibatasi di 0 karena waktu ga bisa negatif
    time_component = discrimination * (time_limit_ms - time_used_ms)
    time_component = max(0.0, time_component)
    
    # Combined success rate
    W = attempt_ratio * test_ratio * (1.0 + time_component)
    
    # Clamp to reasonable range [0.0, 2.0]
    return max(0.0, min(2.0, W))


def update_elo_ratings(
    student_rating: float,
    question_difficulty: float,
    success_rate: float,
    k_factor: int
) -> tuple[float, float]:

    
    expected_score = calculate_expected_score(student_rating, question_difficulty)
    
    # Ri = Ri−1 + K · (W − We)
    new_student_rating = student_rating + k_factor * (success_rate - expected_score)
    
    # Dj = Dj−1 + K · (We − W)
    new_question_difficulty = question_difficulty + k_factor * (expected_score - success_rate)
    
    # Clamp ke rentang yg masuk akal
    new_student_rating = max(RATING_MIN, min(RATING_MAX, new_student_rating))
    new_question_difficulty = max(RATING_MIN, min(RATING_MAX, new_question_difficulty))
    
    return new_student_rating, new_question_difficulty