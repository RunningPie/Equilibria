"""
Peer Matching Test User Generator

Creates 4 test users around a target user to test peer matching criteria:
- 2 users WITHIN criteria (|θ_diff| >= 0.5 * σ) - should be selected as peers
- 2 users OUTSIDE criteria (|θ_diff| < 0.5 * σ) - should NOT be selected

Usage:
    cd server
    python -m app.tests.core.seed_peer_matching_users <target_user_id>

Example:
    python -m app.tests.core.seed_peer_matching_users 550e8400-e29b-41d4-a716-446655440000
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func as sql_func
import numpy

from app.db.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Cohen's d threshold from peer matching logic
COHEN_D_THRESHOLD = 0.5
FALLBACK_POPULATION_STD = 100.0


def generate_unique_nim(base_nim: str, index: int) -> str:
    """Generate unique NIM by appending index."""
    return f"{base_nim}{index:03d}"


async def calculate_population_std(session: AsyncSession) -> float:
    """Calculate population std of theta_individu across ACTIVE users."""
    result = await session.execute(
        select(User.theta_individu).where(User.status == "ACTIVE")
    )
    thetas = [row[0] for row in result.all()]
    
    if len(thetas) < 2:
        return FALLBACK_POPULATION_STD
    
    population_std = numpy.std(thetas, ddof=0)
    return float(population_std) if population_std > 0 else FALLBACK_POPULATION_STD


async def get_target_user(session: AsyncSession, user_id: str) -> User:
    """Fetch target user by ID."""
    result = await session.execute(
        select(User).where(User.user_id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"Target user with ID {user_id} not found")
    return user


async def create_test_users(session: AsyncSession, target_user: User):
    """Create 4 test users: 2 within criteria, 2 outside criteria."""
    
    # Calculate population std and min difference
    population_std = await calculate_population_std(session)
    min_difference = COHEN_D_THRESHOLD * population_std
    
    target_theta = target_user.theta_individu
    base_nim = f"TEST{target_user.nim[-4:] if len(target_user.nim) >= 4 else '0000'}"
    
    print(f"\nTarget User: {target_user.nim} (θ={target_theta:.2f})")
    print(f"Population σ: {population_std:.2f}")
    print(f"Min |θ_diff| for peer matching: {min_difference:.2f} (Cohen's d >= 0.5)")
    print("=" * 60)
    
    # Define theta offsets for test users
    # OUTSIDE criteria: small theta difference (< min_difference)
    # These users are too similar to target and should NOT be selected
    outside_offsets = [
        min_difference * 0.3,   # Very similar (30% of threshold)
        min_difference * 0.7,   # Somewhat similar (70% of threshold)
    ]
    
    # WITHIN criteria: large theta difference (>= min_difference)
    # These users are heterogeneous and SHOULD be selected
    within_offsets = [
        min_difference * 1.2,   # Heterogeneous (120% of threshold)
        min_difference * 2.0,   # Very heterogeneous (200% of threshold)
    ]
    
    created_users = []
    user_counter = 1
    
    # Create users OUTSIDE criteria (should NOT be selected as peers)
    print("\n--- Creating users OUTSIDE peer matching criteria ---")
    for i, offset in enumerate(outside_offsets):
        # Alternate between higher and lower theta
        sign = 1 if i % 2 == 0 else -1
        theta = target_theta + (sign * offset)
        
        # Clamp to valid range [0, 2000]
        theta = max(0.0, min(2000.0, theta))
        
        nim = generate_unique_nim(base_nim, user_counter)
        user = User(
            nim=nim,
            full_name=f"Test Peer Outside {i+1}",
            password_hash=get_password_hash("testpassword123"),
            theta_individu=theta,
            theta_social=1300.0,
            k_factor=30,
            total_attempts=0,
            status="ACTIVE",
            has_completed_pretest=True
        )
        session.add(user)
        await session.flush()
        
        theta_diff = abs(theta - target_theta)
        cohen_d = theta_diff / population_std
        
        print(f"  [{user_counter}] {nim}: θ={theta:.2f}, |Δθ|={theta_diff:.2f}, Cohen's d={cohen_d:.2f}")
        print(f"       -> TOO SIMILAR (should NOT be selected)")
        created_users.append(user)
        user_counter += 1
    
    # Create users WITHIN criteria (should be selected as peers)
    print("\n--- Creating users WITHIN peer matching criteria ---")
    for i, offset in enumerate(within_offsets):
        # Alternate between higher and lower theta
        sign = -1 if i % 2 == 0 else 1
        theta = target_theta + (sign * offset)
        
        # Clamp to valid range [0, 2000]
        theta = max(0.0, min(2000.0, theta))
        
        nim = generate_unique_nim(base_nim, user_counter)
        user = User(
            nim=nim,
            full_name=f"Test Peer Within {i+1}",
            password_hash=get_password_hash("testpassword123"),
            theta_individu=theta,
            theta_social=1300.0,
            k_factor=30,
            total_attempts=0,
            status="ACTIVE",
            has_completed_pretest=True
        )
        session.add(user)
        await session.flush()
        
        theta_diff = abs(theta - target_theta)
        cohen_d = theta_diff / population_std
        
        print(f"  [{user_counter}] {nim}: θ={theta:.2f}, |Δθ|={theta_diff:.2f}, Cohen's d={cohen_d:.2f}")
        print(f"       -> HETEROGENEOUS (CAN be selected)")
        created_users.append(user)
        user_counter += 1
    
    await session.commit()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST USERS CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Target User: {target_user.nim} (θ={target_theta:.2f})")
    print(f"\nUsers that should NOT be selected (too similar):")
    for u in created_users[:2]:
        diff = abs(u.theta_individu - target_theta)
        print(f"  - {u.nim}: θ={u.theta_individu:.2f}, |Δθ|={diff:.2f}")
    print(f"\nUsers that CAN be selected (heterogeneous):")
    for u in created_users[2:]:
        diff = abs(u.theta_individu - target_theta)
        print(f"  - {u.nim}: θ={u.theta_individu:.2f}, |Δθ|={diff:.2f}")
    print("\n" + "=" * 60)
    print("Test Instructions:")
    print("1. Trigger stagnation detection for the target user")
    print("2. Verify that peer session is created with one of the")
    print("   'CAN be selected' users (never the 'should NOT' users)")
    print("=" * 60)
    
    return created_users


async def main():
    if len(sys.argv) != 2:
        print(__doc__)
        print("\nError: Target user ID is required")
        sys.exit(1)
    
    target_user_id = sys.argv[1]
    
    try:
        UUID(target_user_id)  # Validate UUID format
    except ValueError:
        print(f"Error: Invalid UUID format: {target_user_id}")
        sys.exit(1)
    
    async with AsyncSessionLocal() as session:
        try:
            print("=" * 60)
            print("PEER MATCHING TEST USER GENERATOR")
            print("=" * 60)
            
            target_user = await get_target_user(session, target_user_id)
            created = await create_test_users(session, target_user)
            
            print(f"\nTotal users created: {len(created)}")
            
        except ValueError as e:
            print(f"\nError: {e}")
            sys.exit(1)
        except Exception as e:
            await session.rollback()
            print(f"\nUnexpected error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
