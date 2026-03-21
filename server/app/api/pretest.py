from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError
import random
from datetime import datetime

from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from app.schemas.pretest import PreTestQuestion, PreTestResult, PreTestAnswerSubmit, PreTestSessionResponse
from app.db.session import get_db
from app.schemas.jsend import jsend_success, jsend_fail

from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.logging_config import get_loggers
from app.db.models import User
from app.db.models import Question
from app.db.models.module import Module
from app.db.models.user_module_progress import UserModuleProgress
from app.db.models.pretest_session import PreTestSession
from app.core.sandbox_executor import SandboxExecutionError, compare_query_results
from app.core.question_selector import select_pretest_question
from app.core.elo_engine import calculate_initial_theta
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(
    prefix="/pretest",
    tags=["Pretest"]
)

logger = get_loggers()[0]

@router.post(
    "/start",
    response_model=PreTestSessionResponse,
    summary="Start a pretest session"
)
async def start_pretest(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
)-> JSONResponse:
    try:
        # Check if user has completed pretest
        user = await db.execute(select(User).where(User.user_id == current_user.user_id))
        user = user.scalar_one_or_none()
        if user.has_completed_pretest:
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="User has already completed pretest"
            )
        
        # Cek apakah ada session yang belum selesai
        pretest_session = await db.execute(select(PreTestSession).where(PreTestSession.user_id == current_user.user_id).where(PreTestSession.completed_at.is_(None)))
        pretest_session = pretest_session.scalar_one_or_none()
        if pretest_session:
            # return existing pretest session
            return jsend_success(
                code=status.HTTP_200_OK,
                message="Pretest session already started",
                data=PreTestSessionResponse(
                    session_id=pretest_session.session_id,
                    current_question_index=pretest_session.current_question_index,
                    total_questions=5,
                    started_at=pretest_session.started_at,
                    completed_at=pretest_session.completed_at,
                    is_completed=pretest_session.completed_at is not None
                )
            )
        
        # Create new pretest session
        new_pretest_session = PreTestSession(
            user_id=current_user.user_id,
            current_question_index=0,
            total_questions=5,
            answers={},
            started_at=datetime.now()
        )
        db.add(new_pretest_session)
        await db.commit()
        return jsend_success(
            code=status.HTTP_201_CREATED,
            message="Pretest started",
            data=PreTestSessionResponse.model_validate(new_pretest_session)
        )
    except Exception as e:
        logger.error(f"Error starting pretest: {e}")
        return jsend_fail(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error"
        )

@router.get(
    "/question/current",
    response_model=PreTestQuestion,
    status_code=HTTP_200_OK,
    summary="Get current question"
)
async def get_current_question(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
)-> JSONResponse:
    try:
        # Get current question
        pretest_session = await db.execute(select(PreTestSession).where(PreTestSession.user_id == current_user.user_id).where(PreTestSession.completed_at.is_(None)))
        pretest_session = pretest_session.scalar_one_or_none()
        if not pretest_session:
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="Pretest session not found"
            )
        
        # cek apakah sudah selesai
        if pretest_session.current_question_index >= pretest_session.total_questions:
            return jsend_fail(
                code=status.HTTP_400_BAD_REQUEST,
                message="Pretest session already completed"
            )
        
        # ambil soal yang sudah dijawab
        answered_ids = list(pretest_session.answers.keys())
        
        # Gunakan question selector yang sudah dioptimasi
        selected_question = await select_pretest_question(
            current_theta=pretest_session.current_theta,
            question_index=pretest_session.current_question_index,
            answered_ids=answered_ids,
            db=db
        )
        
        if not selected_question:
            return jsend_fail(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="No available questions for pretest"
            )
        
        return jsend_success(
            code=status.HTTP_200_OK,
            message="Current question",
            data=PreTestQuestion(
                question_id=selected_question.question_id,
                content=selected_question.content,
                question_number=pretest_session.current_question_index +1,
                total_questions=5,
                topic_tags=selected_question.topic_tags
            )
        )
    except Exception as e:
        logger.error(f"Error getting current question: {e}")
        return jsend_fail(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error"
        )

@router.post(
    "/submit",
    response_model=PreTestResult,
    status_code=HTTP_200_OK,
    summary="Submit an answer",
    description="Endpoint for users to submit pretest question answers. Also used for submitting the final answer to obtain initial rating"
)
async def submit_pretest_answer(
    payload: PreTestAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    try:
        # 1. Ambil session yg aktif saat ini
        session_result = await db.execute(
            select(PreTestSession).where(
                PreTestSession.user_id == current_user.user_id,
                PreTestSession.completed_at.is_(None)
            )
        )
        
        pretest_session = session_result.scalar_one_or_none()
        
        if not pretest_session:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No Active Pretest Session Found"
            )
        
        # 2. Validasi urutan soal
        if pretest_session.current_question_index != payload.question_number-1:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="Out of order submission"
            )
        
        # 3. simpan jawaban ke JSONB
        question = await db.execute(
            select(Question).where(Question.question_id == payload.question_id)
        )
        question = question.scalar_one_or_none()
        
        if not question:
            return jsend_fail(
                code = HTTP_404_NOT_FOUND,
                message = "Question not found"
            )
        
        try:
            is_correct = await compare_query_results(
                user_query=payload.user_query,
                target_query=question.target_query
            )
        except SandboxExecutionError as e:
            logger.warning(f"Sandbox execution failed: {e}")
            is_correct = False
        
              
        current_answers = pretest_session.answers or {}
        current_answers[payload.question_id] = is_correct
        flag_modified(pretest_session, 'answers')
        
        # 4. cek apakah ini soal terakhir
        is_completed = (pretest_session.current_question_index + 1) >= pretest_session.total_questions
        
        if is_completed:
            # Kalkulasi theta init
            correct_count = sum(1 for v in current_answers.values() if v)
            initial_theta = calculate_initial_theta(correct_count)
            
            # update session
            pretest_session.current_theta = initial_theta
            pretest_session.completed_at = datetime.now()
            
            # Update profil pengguna
            user = await db.execute(
                select(User)
                .where(User.user_id == current_user.user_id)
            )
            user = user.scalar_one()
            user.theta_individu = initial_theta
            user.has_completed_pretest = True
            
            modules_result = await db.execute(select(Module.module_id))
            all_module_ids = [mid for (mid,) in modules_result.all()]
            
            progress_result = await db.execute(
                select(UserModuleProgress.module_id).where(
                    UserModuleProgress.user_id == current_user.user_id
                )
            )
            existing_module_ids = {mid for (mid,) in progress_result.all()}

            missing_module_ids = [mid for mid in all_module_ids if mid not in existing_module_ids]
            for module_id in missing_module_ids:
                db.add(
                    UserModuleProgress(
                        user_id=current_user.user_id,
                        module_id=module_id,
                        is_completed=False,
                    )
                )
            
            message = "Pretest Completed. Init Theta Calculated"
            result_data = PreTestResult(
                session_id = pretest_session.session_id,
                theta_initial=initial_theta,
                has_completed_pretest=True,
                total_correct=correct_count,
                total_questions=5,
                redirect="dashboard"
            )
            
        else:
            # belum selesai jadi increm indx aja
            pretest_session.current_question_index += 1
            message = "Answer submitted. Next question"
            result_data = PreTestResult(
                session_id = pretest_session.session_id,
                theta_initial=None,
                total_correct=sum(1 for v in current_answers.values() if v),
                total_questions=5,
                has_completed_pretest=False,
                redirect=None
            )
        
        await db.commit()
        
        return jsend_success(
            code=HTTP_200_OK,
            message=message,
            data=result_data
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error submitting pretest answer: {e}")
        return jsend_fail(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error"
        )