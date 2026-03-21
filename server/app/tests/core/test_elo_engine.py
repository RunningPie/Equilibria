"""
Unit Tests untuk ELO Engine - Kepatuhan Tech Specs v4.2

Tes memverifikasi:
1. Skala rating [0, 2000] dengan baseline 1300
2. Vesin Eq. 1 & 2 (Pembaruan Rating)
3. Vesin Eq. 4 (Skor yang Diharapkan)
4. Vesin Eq. 3 yang Disederhanakan (Success Rate Biner)
5. Logika K-Factor decay
6. Perubahan theta logis (naik saat menang, turun saat kalah)
"""

import pytest
import math
from app.core.elo_engine import (
    calculate_initial_theta,
    calculate_expected_score,
    calculate_success_rate,
    get_k_factor,
    update_elo_ratings,
    BASE_RATING,
    RATING_MIN,
    RATING_MAX
)


class TestInitialThetaCalculation:
    """Tes kalibrasi pre-test untuk skala [0, 2000] dengan baseline 1300"""
    
    def test_perfect_score(self):
        """5/5 benar seharusnya dipetakan ke rentang atas (1500)"""
        theta = calculate_initial_theta(5, 5)
        assert theta == 1500.0, f"Diharapkan 1500.0, didapat {theta}"
    
    def test_zero_score(self):
        """0/5 benar seharusnya dipetakan ke rentang bawah (1100)"""
        theta = calculate_initial_theta(0, 5)
        assert theta == 1100.0, f"Diharapkan 1100.0, didapat {theta}"
    
    def test_average_score(self):
        """2.5/5 benar seharusnya dipetakan ke baseline (1300)"""
        theta = calculate_initial_theta(2.5, 5)
        assert theta == 1300.0, f"Diharapkan 1300.0, didapat {theta}"
    
    def test_score_boundaries(self):
        """Tes berbagai skor tetap dalam rentang [1100, 1500]"""
        for correct in range(6):
            theta = calculate_initial_theta(correct, 5)
            assert 1100 <= theta <= 1500, f"Skor {correct} memberikan theta {theta} di luar rentang"


class TestExpectedScoreCalculation:
    """Test Vesin Eq. 4: Expected score calculation"""
    
    def test_equal_rating_difficulty(self):
        """Equal rating and difficulty should give 0.5 probability"""
        prob = calculate_expected_score(1300.0, 1300.0)
        assert abs(prob - 0.5) < 0.001, f"Expected ~0.5, got {prob}"
    
    def test_higher_rating_than_difficulty(self):
        """Higher rating should give >0.5 probability"""
        prob = calculate_expected_score(1500.0, 1100.0)
        assert prob > 0.5, f"Expected >0.5, got {prob}"
        assert prob < 1.0, f"Expected <1.0, got {prob}"
    
    def test_lower_rating_than_difficulty(self):
        """Lower rating should give <0.5 probability"""
        prob = calculate_expected_score(1100.0, 1500.0)
        assert prob < 0.5, f"Expected <0.5, got {prob}"
        assert prob > 0.0, f"Expected >0.0, got {prob}"
    
    def test_extreme_difference(self):
        """Test extreme rating differences"""
        # Very high rating vs very low difficulty
        prob = calculate_expected_score(1900.0, 100.0)
        assert prob > 0.9, f"Expected >0.9, got {prob}"
        
        # Very low rating vs very high difficulty  
        prob = calculate_expected_score(100.0, 1900.0)
        assert prob < 0.1, f"Expected <0.1, got {prob}"


class TestSuccessRateCalculation:
    """Test Vesin Eq. 3 with binary test ratio simplification"""
    
    def test_correct_answer_single_attempt(self):
        """Correct answer with 1 attempt should give high success rate"""
        rate = calculate_success_rate(
            successful_attempts=1,  # Ai = 1
            overall_attempts=1,     # A = 1
            correct_tests=1,         # Tc = 1 (correct)
            performed_tests=1,      # Tp = 1
            time_used_ms=60000,      # ti = 1 minute
            time_limit_ms=300000     # di = 5 minutes
        )
        # Should be > 1.0 due to time bonus and perfect attempt ratio
        assert rate > 1.0, f"Expected > 1.0 for perfect answer, got {rate}"
        assert rate <= 2.0, f"Expected ≤ 2.0, got {rate}"
    
    def test_wrong_answer_single_attempt(self):
        """Wrong answer should give 0.0 success rate"""
        rate = calculate_success_rate(
            successful_attempts=0,  # Ai = 0
            overall_attempts=1,     # A = 1
            correct_tests=0,         # Tc = 0 (wrong)
            performed_tests=1,      # Tp = 1
            time_used_ms=60000,      # ti = 1 minute
            time_limit_ms=300000     # di = 5 minutes
        )
        assert rate == 0.0, f"Expected 0.0 for wrong answer, got {rate}"
    
    def test_correct_answer_multiple_attempts(self):
        """Correct answer after multiple attempts should give lower success rate"""
        # Correct on 3rd attempt
        rate = calculate_success_rate(
            successful_attempts=1,  # Ai = 1 (only 1 successful)
            overall_attempts=3,     # A = 3 (total 3 attempts)
            correct_tests=1,         # Tc = 1 (correct)
            performed_tests=1,      # Tp = 1
            time_used_ms=180000,     # ti = 3 minutes
            time_limit_ms=300000     # di = 5 minutes
        )
        # Should be lower than single attempt due to attempt ratio penalty
        assert 0.0 < rate < 1.0, f"Expected between 0.0 and 1.0 for 3 attempts, got {rate}"
    
    def test_time_bonus_effect(self):
        """Faster completion should give higher success rate"""
        # Fast answer
        rate_fast = calculate_success_rate(
            successful_attempts=1, overall_attempts=1,
            correct_tests=1, performed_tests=1,
            time_used_ms=30000,      # 30 seconds
            time_limit_ms=300000
        )
        
        # Slow answer  
        rate_slow = calculate_success_rate(
            successful_attempts=1, overall_attempts=1,
            correct_tests=1, performed_tests=1,
            time_used_ms=240000,     # 4 minutes
            time_limit_ms=300000
        )
        
        assert rate_fast > rate_slow, f"Fast answer should have higher rate: {rate_fast} vs {rate_slow}"
    
    def test_success_rate_bounds(self):
        """Success rate should stay within [0.0, 2.0] bounds"""
        # Test extreme fast case
        rate = calculate_success_rate(
            successful_attempts=1, overall_attempts=1,
            correct_tests=1, performed_tests=1,
            time_used_ms=0,           # Instant
            time_limit_ms=300000
        )
        assert rate <= 2.0, f"Rate should not exceed 2.0, got {rate}"
        
        # Test wrong answer
        rate = calculate_success_rate(
            successful_attempts=0, overall_attempts=1,
            correct_tests=0, performed_tests=1,
            time_used_ms=300000,
            time_limit_ms=300000
        )
        assert rate >= 0.0, f"Rate should not be negative, got {rate}"


class TestKFactorDecay:
    """Test K-Factor decay logic per Vesin thresholds - tracks finalized questions only"""
    
    def test_novice_k_factor(self):
        """0-9 finalized questions should use K=30"""
        for finalized_questions in range(0, 10):
            k = get_k_factor(finalized_questions)
            assert k == 30, f"Finalized questions {finalized_questions}: expected K=30, got {k}"
    
    def test_intermediate_k_factor(self):
        """10-24 finalized questions should use K=20"""
        for finalized_questions in range(10, 25):
            k = get_k_factor(finalized_questions)
            assert k == 20, f"Finalized questions {finalized_questions}: expected K=20, got {k}"
    
    def test_advanced_k_factor(self):
        """25-49 finalized questions should use K=15"""
        for finalized_questions in range(25, 50):
            k = get_k_factor(finalized_questions)
            assert k == 15, f"Finalized questions {finalized_questions}: expected K=15, got {k}"
    
    def test_expert_k_factor(self):
        """50+ finalized questions should use K=10"""
        for finalized_questions in range(50, 100):
            k = get_k_factor(finalized_questions)
            assert k == 10, f"Finalized questions {finalized_questions}: expected K=10, got {k}"


class TestEloRatingUpdates:
    """Test Vesin Eq. 1 & 2: Rating update formulas for both student and question difficulty"""
    
    def test_correct_answer_increases_theta(self):
        """Correct answer should increase student theta and decrease question difficulty"""
        student_theta = 1300.0
        question_difficulty = 1300.0
        k_factor = 30
        
        new_student, new_difficulty = update_elo_ratings(
            student_theta, question_difficulty, 1.0, k_factor
        )
        
        assert new_student > student_theta, f"Student theta should increase: {student_theta} -> {new_student}"
        assert new_difficulty < question_difficulty, f"Difficulty should decrease: {question_difficulty} -> {new_difficulty}"
        
        # Verify the magnitude of changes are equal (zero-sum property)
        student_change = new_student - student_theta
        difficulty_change = question_difficulty - new_difficulty
        assert abs(student_change - difficulty_change) < 0.001, \
            f"Changes should be equal: student +{student_change:.3f}, difficulty -{difficulty_change:.3f}"
    
    def test_wrong_answer_decreases_theta(self):
        """Wrong answer should decrease student theta and increase question difficulty"""
        student_theta = 1300.0
        question_difficulty = 1300.0
        k_factor = 30
        
        new_student, new_difficulty = update_elo_ratings(
            student_theta, question_difficulty, 0.0, k_factor
        )
        
        assert new_student < student_theta, f"Student theta should decrease: {student_theta} -> {new_student}"
        assert new_difficulty > question_difficulty, f"Difficulty should increase: {question_difficulty} -> {new_difficulty}"
        
        # Verify the magnitude of changes are equal (zero-sum property)
        student_change = student_theta - new_student
        difficulty_change = new_difficulty - question_difficulty
        assert abs(student_change - difficulty_change) < 0.001, \
            f"Changes should be equal: student -{student_change:.3f}, difficulty +{difficulty_change:.3f}"
    
    def test_question_difficulty_adaptation(self):
        """Test question difficulty adapts based on student performance"""
        # Easy question (low difficulty) answered correctly by strong student
        new_student, new_difficulty = update_elo_ratings(1500.0, 1000.0, 1.0, 30)
        assert new_difficulty > 1000.0, f"Easy question should get harder when strong student answers correctly: {1000.0} -> {new_difficulty}"
        
        # Hard question (high difficulty) answered incorrectly by weak student  
        new_student, new_difficulty = update_elo_ratings(1100.0, 1600.0, 0.0, 30)
        assert new_difficulty < 1600.0, f"Hard question should get easier when weak student answers incorrectly: {1600.0} -> {new_difficulty}"
        
        # Medium difficulty answered by equal rating should have minimal change
        new_student, new_difficulty = update_elo_ratings(1300.0, 1300.0, 0.5, 30)
        assert abs(new_difficulty - 1300.0) < 50.0, f"Equal performance should cause minimal difficulty change: {1300.0} -> {new_difficulty}"
    
    def test_rating_bounds(self):
        """Updated ratings should stay within [0, 2000] bounds"""
        # Test upper bound
        new_student, new_difficulty = update_elo_ratings(1900.0, 100.0, 1.0, 30)
        assert new_student <= RATING_MAX, f"Student theta {new_student} exceeds max {RATING_MAX}"
        assert new_difficulty <= RATING_MAX, f"Difficulty {new_difficulty} exceeds max {RATING_MAX}"
        
        # Test lower bound
        new_student, new_difficulty = update_elo_ratings(100.0, 1900.0, 0.0, 30)
        assert new_student >= RATING_MIN, f"Student theta {new_student} below min {RATING_MIN}"
        assert new_difficulty >= RATING_MIN, f"Difficulty {new_difficulty} below min {RATING_MIN}"
    
    def test_zero_sum_property(self):
        """Elo updates should be zero-sum (student gain = question loss)"""
        student_theta = 1300.0
        question_difficulty = 1300.0
        k_factor = 30
        
        new_student, new_difficulty = update_elo_ratings(
            student_theta, question_difficulty, 1.0, k_factor
        )
        
        student_change = new_student - student_theta
        difficulty_change = new_difficulty - question_difficulty
        
        # Should be approximately equal and opposite
        assert abs(student_change + difficulty_change) < 0.001, \
            f"Zero-sum violated: student change {student_change}, difficulty change {difficulty_change}"


class TestSimulation10Questions:
    """Simulate 10 questions to verify logical theta progression"""
    
    def test_mixed_performance_simulation(self):
        """Simulate mixed correct/incorrect answers with multi-attempt scenarios"""
        theta = BASE_RATING  # Start at 1300
        difficulty = 1300.0
        finalized_questions = 0
        
        # Question scenarios: (correct?, total_attempts, time_used_ms)
        questions = [
            (True, 1, 60000),    # Q1: Correct, 1 attempt, 1 min
            (False, 2, 120000),  # Q2: Wrong, 2 attempts, 2 min  
            (True, 1, 45000),    # Q3: Correct, 1 attempt, 45 sec
            (True, 3, 180000),   # Q4: Correct, 3 attempts, 3 min
            (False, 1, 90000),   # Q5: Wrong, 1 attempt, 1.5 min
            (True, 1, 30000),    # Q6: Correct, 1 attempt, 30 sec
            (False, 2, 150000),  # Q7: Wrong, 2 attempts, 2.5 min
            (True, 1, 60000),    # Q8: Correct, 1 attempt, 1 min
            (True, 1, 75000),    # Q9: Correct, 1 attempt, 1.25 min
            (True, 2, 120000),   # Q10: Correct, 2 attempts, 2 min
        ]
        
        thetas = [theta]
        
        for i, (is_correct, total_attempts, time_used) in enumerate(questions):
            # Only increment finalized questions count (not total submissions)
            finalized_questions += 1
            k_factor = get_k_factor(finalized_questions)
            
            # Calculate success rate using full Vesin Eq. 3
            success_rate = calculate_success_rate(
                successful_attempts=1 if is_correct else 0,  # Ai
                overall_attempts=total_attempts,              # A
                correct_tests=1 if is_correct else 0,         # Tc (binary)
                performed_tests=1,                             # Tp (always 1)
                time_used_ms=time_used,
                time_limit_ms=300000
            )
            
            theta, difficulty = update_elo_ratings(
                theta, difficulty, success_rate, k_factor
            )
            thetas.append(theta)
        
        # Verify logical progression
        # Should end higher than start since more correct (7) than wrong (3)
        final_theta = thetas[-1]
        assert final_theta > BASE_RATING, \
            f"Final theta {final_theta} should be > start {BASE_RATING} with 7/10 correct"
        
        # Verify all thetas stay within bounds
        for t in thetas:
            assert RATING_MIN <= t <= RATING_MAX, f"Theta {t} outside bounds [{RATING_MIN}, {RATING_MAX}]"
    
    def test_all_correct_simulation(self):
        """Simulate all correct answers - should show steady increase"""
        theta = BASE_RATING
        difficulty = 1300.0
        finalized_questions = 0
        
        for i in range(10):
            attempts = 1  # All correct on first try
            finalized_questions += 1  # Increment finalized questions count
            k_factor = get_k_factor(finalized_questions)
            
            success_rate = calculate_success_rate(
                successful_attempts=1,
                overall_attempts=attempts,
                correct_tests=1,
                performed_tests=1,
                time_used_ms=60000,  # 1 minute each
                time_limit_ms=300000
            )
            
            theta, difficulty = update_elo_ratings(
                theta, difficulty, success_rate, k_factor
            )
        
        # Should be significantly higher than start
        assert theta > BASE_RATING + 100, \
            f"All correct should increase theta significantly: {BASE_RATING} -> {theta}"
    
    def test_all_wrong_simulation(self):
        """Simulate all wrong answers - should show steady decrease"""
        theta = BASE_RATING
        difficulty = 1300.0
        finalized_questions = 0
        
        for i in range(10):
            attempts = 1  # Wrong on first try
            finalized_questions += 1  # Increment finalized questions count
            k_factor = get_k_factor(finalized_questions)
            
            success_rate = calculate_success_rate(
                successful_attempts=0,
                overall_attempts=attempts,
                correct_tests=0,
                performed_tests=1,
                time_used_ms=120000,  # 2 minutes each
                time_limit_ms=300000
            )
            
            theta, difficulty = update_elo_ratings(
                theta, difficulty, success_rate, k_factor
            )
        
        # Should be significantly lower than start
        assert theta < BASE_RATING - 100, \
            f"All wrong should decrease theta significantly: {BASE_RATING} -> {theta}"


if __name__ == "__main__":
    # Run quick simulation test
    print("Running ELO Engine Simulation (10 questions)...")
    
    theta = BASE_RATING
    difficulty = 1300.0
    finalized_questions = 0
    
    print(f"Starting theta: {theta}")
    
    # Mixed performance scenarios
    questions = [
        (True, 1, 60000),    # Q1: Correct, 1 attempt, 1 min
        (False, 2, 120000),  # Q2: Wrong, 2 attempts, 2 min  
        (True, 1, 45000),    # Q3: Correct, 1 attempt, 45 sec
        (True, 3, 180000),   # Q4: Correct, 3 attempts, 3 min
        (False, 1, 90000),   # Q5: Wrong, 1 attempt, 1.5 min
        (True, 1, 30000),    # Q6: Correct, 1 attempt, 30 sec
        (False, 2, 150000),  # Q7: Wrong, 2 attempts, 2.5 min
        (True, 1, 60000),    # Q8: Correct, 1 attempt, 1 min
        (True, 1, 75000),    # Q9: Correct, 1 attempt, 1.25 min
        (True, 2, 120000),   # Q10: Correct, 2 attempts, 2 min
    ]
    
    for i, (is_correct, attempts, time_used) in enumerate(questions, 1):
        finalized_questions += 1  # Increment finalized questions count
        k_factor = get_k_factor(finalized_questions)
        
        success_rate = calculate_success_rate(
            successful_attempts=1 if is_correct else 0,
            overall_attempts=attempts,
            correct_tests=1 if is_correct else 0,
            performed_tests=1,
            time_used_ms=time_used,
            time_limit_ms=300000
        )
        
        theta, difficulty = update_elo_ratings(
            theta, difficulty, success_rate, k_factor
        )
        
        result = "✓" if is_correct else "✗"
        print(f"Q{i}: {result} (A{attempts}) | Theta: {theta:.1f} | W: {success_rate:.3f} | K: {k_factor}")
    
    print(f"Final theta: {theta:.1f} (Change: {theta - BASE_RATING:+.1f})")
    print("✅ ELO Engine tests completed!")
