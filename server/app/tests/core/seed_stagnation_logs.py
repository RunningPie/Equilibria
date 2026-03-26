import sys
import uuid
import asyncio
import numpy as np
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.db.session import DatabaseSession
from app.db.models.assessment_log import AssessmentLog
from app.db.models.question import Question


def generate_theta_deltas(mode: str) -> list[float]:
    """
    Generate 5 theta deltas based on the test mode.
    
    Args:
        mode: 'test_stagnation' or 'test_active'
        
    Returns:
        List of 5 theta delta values (theta_after - theta_before)
    """
    if mode == 'test_stagnation':
        # Low variance deltas (< 165 variance)
        # These values have variance ~2.5 (very low)
        return [12.0, 15.0, 13.0, 14.0, 11.0]  # variance ≈ 2.0
    elif mode == 'test_active':
        # High variance deltas (>= 165 variance)
        # These values have variance ~800 (high)
        return [20.0, 80.0, 30.0, 100.0, 50.0]  # variance ≈ 800
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'test_stagnation' or 'test_active'")


def calculate_variance(deltas: list[float]) -> float:
    """Calculate population variance of deltas."""
    return float(np.var(deltas))


async def get_or_create_session_id(db: AsyncSession, user_id: UUID) -> UUID:
    """Get an existing session ID or create a new one for testing."""
    from app.db.models.assessment_session import AssessmentSession
    
    # Try to find existing session for this user
    result = await db.execute(
        select(AssessmentSession).where(
            AssessmentSession.user_id == user_id
        ).limit(1)
    )
    session = result.scalar_one_or_none()
    
    if session:
        return session.session_id
    
    # Create a new session if none exists
    new_session = AssessmentSession(
        user_id=user_id,
        module_id="CH01",
        status="ACTIVE"
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session.session_id


async def get_available_question_ids(db: AsyncSession, limit: int = 5) -> list[str]:
    """Get list of available question IDs from the database."""
    result = await db.execute(
        select(Question.question_id).limit(limit)
    )
    questions = result.scalars().all()
    
    if len(questions) < limit:
        # If not enough questions, reuse some
        questions = list(questions)
        while len(questions) < limit:
            questions.append(questions[len(questions) % len(questions)] if questions else "CH01-001")
    
    return questions[:limit]


async def seed_assessment_logs(user_id: str, mode: str):
    """
    Seed 5 assessment logs into the database.
    
    Args:
        user_id: UUID string of the user
        mode: 'test_stagnation' or 'test_active'
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        print(f"Error: Invalid UUID format: {user_id}")
        sys.exit(1)
    
    # Generate theta deltas
    theta_deltas = generate_theta_deltas(mode)
    variance = calculate_variance(theta_deltas)
    
    print(f"Mode: {mode}")
    print(f"Theta deltas: {theta_deltas}")
    print(f"Variance: {variance:.2f}")
    print(f"Expected stagnation detection: {variance < 165}")
    print("-" * 50)
    
    # Get session factory
    session_factory = DatabaseSession.get_session_factory()
    
    async with session_factory() as db:
        try:
            # Get or create a session ID
            session_id = await get_or_create_session_id(db, user_uuid)
            print(f"Using session: {session_id}")
            
            # Get available question IDs
            question_ids = await get_available_question_ids(db, limit=5)
            print(f"Using questions: {question_ids}")
            
            # Base theta value (starting point)
            base_theta = 1300.0
            current_theta = base_theta
            
            # Create timestamps (recent, going backwards)
            base_time = datetime.utcnow()
            
            for i, delta in enumerate(theta_deltas):
                theta_before = current_theta
                theta_after = current_theta + delta
                
                log = AssessmentLog(
                    session_id=session_id,
                    user_id=user_uuid,
                    question_id=question_ids[i],
                    user_query=f"SELECT * FROM test_table WHERE id = {i}",
                    is_correct=True,
                    attempt_number=1,
                    is_final_attempt=True,
                    theta_before=theta_before,
                    theta_after=theta_after,
                    difficulty_before=1250.0,
                    difficulty_after=1245.0,
                    execution_time_ms=1500 + (i * 100),
                    timestamp=base_time - timedelta(minutes=i)  # Most recent first
                )
                
                db.add(log)
                current_theta = theta_after
                
                print(f"Log {i+1}: theta_before={theta_before:.1f}, theta_after={theta_after:.1f}, delta={delta:.1f}")
            
            await db.commit()
            print("-" * 50)
            print(f"Successfully created 5 assessment logs for user {user_id}")
            print(f"Final theta: {current_theta:.1f} (started at {base_theta:.1f})")
            
        except Exception as e:
            await db.rollback()
            print(f"Error seeding logs: {e}")
            raise


def main():
    if len(sys.argv) != 3:
        print("Usage: python seed_stagnation_logs.py <user_id> <mode>")
        print("  mode: 'test_stagnation' or 'test_active'")
        sys.exit(1)
    
    user_id = sys.argv[1]
    mode = sys.argv[2]
    
    if mode not in ['test_stagnation', 'test_active']:
        print(f"Error: Invalid mode '{mode}'. Use 'test_stagnation' or 'test_active'")
        sys.exit(1)
    
    asyncio.run(seed_assessment_logs(user_id, mode))


if __name__ == "__main__":
    main()
