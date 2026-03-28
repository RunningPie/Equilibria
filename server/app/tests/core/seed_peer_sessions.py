"""
Peer Session Test Data Generator

Creates 2 peer session entries for testing collaboration endpoints:
- Entry 1: User1 as requester, User2 as reviewer
- Entry 2: User1 as reviewer, User2 as requester

Usage:
    cd server
    python -m app.tests.core.seed_peer_sessions <user1_id> <user2_id>

Example:
    python -m app.tests.core.seed_peer_sessions 550e8400-e29b-41d4-a716-446655440000 660e8400-e29b-41d4-a716-446655440001
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.db.models import User, PeerSession, Question
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_user(session: AsyncSession, user_id: str) -> User:
    """Fetch user by ID."""
    result = await session.execute(
        select(User).where(User.user_id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    return user


async def get_any_question(session: AsyncSession) -> Question:
    """Fetch any question from the database for testing."""
    result = await session.execute(
        select(Question).limit(1)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise ValueError("No questions found in database")
    return question


async def create_peer_sessions(session: AsyncSession, user1: User, user2: User, question: Question):
    """Create 2 peer session entries for the user pair."""
    
    print("\n" + "=" * 60)
    print("PEER SESSION TEST DATA GENERATOR")
    print("=" * 60)
    print(f"\nUser 1: {user1.nim} (ID: {user1.user_id})")
    print(f"User 2: {user2.nim} (ID: {user2.user_id})")
    print(f"Question: {question.question_id}")
    print("=" * 60)
    
    # Entry 1: User1 as requester, User2 as reviewer
    session1 = PeerSession(
        requester_id=user1.user_id,
        reviewer_id=user2.user_id,
        question_id=question.question_id,
        requester_query="SELECT * FROM test_table WHERE id = 1",
        review_content="",
        system_score=0.0,
        is_helpful=None,
        final_score=0.0,
        status="PENDING_REVIEW"
    )
    session.add(session1)
    await session.flush()
    
    print("\n--- Entry 1: User1 as Requester, User2 as Reviewer ---")
    print(f"  Session ID: {session1.session_id}")
    print(f"  Requester: {user1.nim}")
    print(f"  Reviewer: {user2.nim}")
    print(f"  Status: {session1.status}")
    print(f"  -> User2 should see this in GET /collaboration/inbox")
    print(f"  -> User1 should see this in GET /collaboration/requests")
    
    # Entry 2: User1 as reviewer, User2 as requester
    session2 = PeerSession(
        requester_id=user2.user_id,
        reviewer_id=user1.user_id,
        question_id=question.question_id,
        requester_query="SELECT COUNT(*) FROM users",
        review_content="",
        system_score=0.0,
        is_helpful=None,
        final_score=0.0,
        status="PENDING_REVIEW"
    )
    session.add(session2)
    await session.flush()
    
    print("\n--- Entry 2: User1 as Reviewer, User2 as Requester ---")
    print(f"  Session ID: {session2.session_id}")
    print(f"  Requester: {user2.nim}")
    print(f"  Reviewer: {user1.nim}")
    print(f"  Status: {session2.status}")
    print(f"  -> User1 should see this in GET /collaboration/inbox")
    print(f"  -> User2 should see this in GET /collaboration/requests")
    
    await session.commit()
    
    # Summary
    print("\n" + "=" * 60)
    print("PEER SESSIONS CREATED SUCCESSFULLY")
    print("=" * 60)
    print("\nTest Instructions:")
    print("1. As User2: GET /api/v1/collaboration/inbox")
    print("   - Should see session 1 (where User2 is reviewer)")
    print("\n2. As User1: GET /api/v1/collaboration/inbox")
    print("   - Should see session 2 (where User1 is reviewer)")
    print("\n3. As User2: POST /api/v1/collaboration/inbox/{session1_id}/submit")
    print("   - Submit review feedback for session 1")
    print("   - Triggers NLP scoring (calculate_system_score)")
    print("\n4. As User1: GET /api/v1/collaboration/requests")
    print("   - Should see session 1 with review_content")
    print("\n5. As User1: POST /api/v1/collaboration/requests/{session1_id}/rate")
    print("   - Rate the feedback (thumbs up/down)")
    print("   - Triggers Social Elo update (theta_social)")
    print("\n6. Repeat steps 3-5 swapping User1/User2 for session 2")
    print("=" * 60)
    
    return session1, session2


async def main():
    if len(sys.argv) != 3:
        print(__doc__)
        print("\nError: Two user IDs are required")
        sys.exit(1)
    
    user1_id = sys.argv[1]
    user2_id = sys.argv[2]
    
    # Validate UUID format
    try:
        UUID(user1_id)
        UUID(user2_id)
    except ValueError as e:
        print(f"Error: Invalid UUID format: {e}")
        sys.exit(1)
    
    async with AsyncSessionLocal() as session:
        try:
            user1 = await get_user(session, user1_id)
            user2 = await get_user(session, user2_id)
            question = await get_any_question(session)
            
            session1, session2 = await create_peer_sessions(session, user1, user2, question)
            
            print(f"\nTotal sessions created: 2")
            print(f"Session IDs:")
            print(f"  - Session 1: {session1.session_id}")
            print(f"  - Session 2: {session2.session_id}")
            
        except ValueError as e:
            print(f"\nError: {e}")
            sys.exit(1)
        except Exception as e:
            await session.rollback()
            print(f"\nUnexpected error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
