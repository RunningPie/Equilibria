# Plan: Elo Engine and Timing System Improvements

## Objective
Address negative theta updates for correct answers by fixing inverted Elo probability logic, implementing accurate "Thinking Time" tracking, and aligning K-Factor thresholds with technical specifications.

## Key Files & Context
- `app/core/elo_engine.py`: Contains Elo calculation logic ($W_e$ and $W$).
- `app/db/models/assessment_session.py`: Database model for sessions.
- `app/api/session.py`: API endpoints where timing and updates occur.
- `app/schemas/session.py`: Request/Response schemas.

## Proposed Changes

### 1. Database Schema
- **File:** `app/db/models/assessment_session.py`
- **Change:** Add `current_question_start_time: Mapped[DateTime]` (nullable) to track when a question is first served to the student.
- **Migration:** Create a new Alembic migration for this field.

### 2. Elo Engine Logic
- **File:** `app/core/elo_engine.py`
- **Fix Inverted Probability:** Change the exponent in `calculate_expected_score` from `(rating - difficulty)` to `(difficulty - rating)`. This aligns with standard Elo and the paper's textual description: "higher rating = higher expectancy".
- **K-Factor Thresholds:** Update `get_k_factor` thresholds to align with the technical specifications:
    - Novice: 0-9 finalized questions (K=30)
    - Intermediate: 10-24 finalized questions (K=20)
    - Advanced: 25-49 finalized questions (K=15)
    - Expert: 50+ finalized questions (K=10)
- **Success Rate Formula:** Ensure `calculate_success_rate` treats the time component as a multiplicative factor if possible, or refine the bonus calculation to be more balanced.

### 3. API & Timing Implementation
- **File:** `app/api/session.py`
- **Start/Next Question:** In `start_session` and `get_next_question_endpoint`, set `session.current_question_start_time = func.now()` whenever a new question is assigned to `session.current_question_id`.
- **Submit Answer:**
    - Calculate total elapsed time (Thinking Time) since `session.current_question_start_time`.
    - Update `AssessmentLog.execution_time_ms` with this total duration.
- **Finalization:** Capture `difficulty_before` *before* the rating update modifies the question record to ensure accurate logging.

### 4. Verification & Testing
- **Elo Unit Tests:** Fix `app/tests/core/test_elo_engine.py` to match the corrected logic (it currently expects the inverted behavior in some places).
- **Integration Test:** Add a test case for 2nd/3rd attempt successes to ensure theta updates are logical (weak students solving hard questions should gain points).
- **Manual Verification:** Verify `execution_time_ms` in logs actually reflects user interaction time.
