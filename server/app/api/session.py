"""
Assessment Session API - Tech Specs v4.2 Section 6.2

Implementasi POST /session/start, GET /session/{id}/question, 
dan endpoint terkait untuk individual mode practice.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4

from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, 
    HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
)

from app.schemas.session import (
    SessionStartRequest, SessionStartResult, QuestionResponse,
    SessionStatus, SubmitRequest, SubmitResult, NextResult
)
from app.schemas.jsend import JSendResponse, jsend_success, jsend_fail, jsend_error
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.logging_config import get_loggers, log_assessment_event
from app.core.question_selector import select_next_question
from app.core.sandbox_executor import compare_query_results
from app.core.elo_engine import (
    calculate_success_rate, get_k_factor, update_elo_ratings,
    detect_stagnation, BASE_RATING
)
from app.db.models import (
    User, Module, Question, AssessmentSession, 
    AssessmentLog, UserModuleProgress
)

router = APIRouter(
    prefix="/session",
    tags=["Assessment Session"]
)

system_logger, assessment_logger = get_loggers()


async def check_and_unlock_modules(user: User, db: AsyncSession) -> None:
    """
    Check dan unlock modul-modul yang bisa diakses user berdasarkan theta.
    Dipanggil setelah Elo update.
    """
    try:
        # Get semua modul yang belum unlocked
        result = await db.execute(
            select(Module).where(Module.module_id != "CH01")  # CH01 selalu unlocked
        )
        modules = result.scalars().all()
        
        for module in modules:
            # Check apakah user sudah memiliki progress untuk modul ini
            progress_result = await db.execute(
                select(UserModuleProgress).where(
                    UserModuleProgress.user_id == user.user_id,
                    UserModuleProgress.module_id == module.module_id
                )
            )
            existing_progress = progress_result.scalar_one_or_none()
            
            if not existing_progress:
                # Check unlock condition
                if user.theta_individu >= module.unlock_theta_threshold:
                    # Unlock modul
                    new_progress = UserModuleProgress(
                        user_id=user.user_id,
                        module_id=module.module_id,
                        is_unlocked=True,
                        is_completed=False
                    )
                    db.add(new_progress)
                    
                    system_logger.info(
                        f"Module unlocked: user={user.user_id}, module={module.module_id}, theta={user.theta_individu}",
                        extra={"event_type": "MODULE_UNLOCK", "module_id": module.module_id}
                    )
        
        await db.commit()
        
    except Exception as e:
        system_logger.error(
            f"Error checking module unlocks: {str(e)}",
            extra={"event_type": "MODULE_UNLOCK_ERROR", "user_id": str(user.user_id)}
        )


@router.post(
    "/start",
    response_model=JSendResponse[SessionStartResult],
    status_code=status.HTTP_201_CREATED,
    summary="Start assessment session",
    description="Memulai session latihan baru untuk modul tertentu"
)
async def start_session(
    session_request: SessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Memulai assessment session baru dengan conflict resolution.
    
    Conflict Resolution Flow:
    - Tidak ada session ACTIVE → buat baru (201)
    - Ada session ACTIVE di modul sama → return existing (200) 
    - Ada session ACTIVE di modul berbeda → return 409 + active session info
    """
    try:
        # Cek apakah user sudah memiliki session aktif
        existing_session = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        active_session = existing_session.scalar_one_or_none()
        
        if active_session:
            if active_session.module_id == session_request.module_id:
                # Idempotent resume - return existing session
                session_response = SessionStartResult(
                    session_id=active_session.session_id,
                    module_id=active_session.module_id,
                    user_theta=current_user.theta_individu,  # Use current user theta
                    status=active_session.status,
                    started_at=active_session.started_at
                )
                return jsend_success(
                    code=HTTP_200_OK,
                    message="Existing session resumed",
                    data=session_response
                )
            else:
                # Conflict - active session in different module
                return jsend_fail(
                    code=status.HTTP_409_CONFLICT,
                    message=f"Kamu masih memiliki sesi aktif di {active_session.module_id}. Akhiri sesi tersebut untuk memulai sesi baru.",
                    data={
                        "active_session": {
                            "session_id": str(active_session.session_id),
                            "module_id": active_session.module_id,
                            "started_at": active_session.started_at.isoformat()
                        }
                    }
                )
        
        # Validasi modul
        module_result = await db.execute(
            select(Module).where(Module.module_id == session_request.module_id)
        )
        module = module_result.scalar_one_or_none()
        if not module:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message=f"Module {session_request.module_id} not found"
            )
        
        # Cek apakah modul unlocked untuk user
        if session_request.module_id != "CH01":
            # Check unlock threshold
            module_result = await db.execute(
                select(Module.unlock_theta_threshold)
                .where(Module.module_id == session_request.module_id)
            )
            module_threshold = module_result.scalar_one_or_none()
            
            if module_threshold and current_user.theta_individu < module_threshold:
                return jsend_fail(
                    code=HTTP_403_FORBIDDEN,
                    message=f"Module {session_request.module_id} locked. Need theta >= {module_threshold}"
                )
        
        # Buat session baru
        new_session = AssessmentSession(
            session_id=uuid4(),
            user_id=current_user.user_id,
            module_id=session_request.module_id,
            status="ACTIVE"
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        # Update response with theta values from user (not stored in session)
        session_response = SessionStartResult(
            session_id=new_session.session_id,
            module_id=new_session.module_id,
            user_theta=current_user.theta_individu,  # Use current user theta
            status=new_session.status,
            started_at=new_session.started_at
        )
        
        system_logger.info(
            f"Session started: user={current_user.user_id}, module={session_request.module_id}, session={new_session.session_id}",
            extra={"event_type": "SESSION_START", "session_id": str(new_session.session_id)}
        )
        
        return jsend_success(
            code=HTTP_201_CREATED,
            message="Session started successfully",
            data=session_response
        )
        
    except Exception as e:
        system_logger.error(
            f"Error starting session: {str(e)}",
            extra={"event_type": "SESSION_START_ERROR"}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error starting session"
        )


@router.get(
    "/active",
    response_model=JSendResponse[SessionStatus | None],
    summary="Get active session",
    description="Mengembalikan session ACTIVE milik user saat ini atau null"
)
async def get_active_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Mendapatkan session aktif user saat ini."""
    try:
        # Cari session aktif
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_success(
                code=HTTP_200_OK,
                message="No active session",
                data=None
            )
        
        # Hitung jumlah soal yang sudah di-serve dan selesai
        questions_served = len(session.question_ids_served or [])
        
        # Hitung questions completed dengan query ke assessment_logs
        completed_result = await db.execute(
            text("SELECT COUNT(DISTINCT question_id) FROM assessment_logs WHERE session_id = :sid AND is_final_attempt = TRUE"),
            {"sid": session.session_id}
        )
        questions_completed = completed_result.scalar() or 0
        
        session_status = SessionStatus(
            session_id=session.session_id,
            module_id=session.module_id,
            status=session.status,
            user_theta_start=current_user.theta_individu,  # Use current user theta as start
            user_theta_current=current_user.theta_individu,  # Use current user theta
            questions_served=questions_served,
            questions_completed=questions_completed,
            started_at=session.started_at,
            ended_at=session.ended_at,
            current_question_id=session.current_question_id
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Active session found",
            data=session_status
        )
        
    except Exception as e:
        system_logger.error(
            f"Error getting active session: {str(e)}",
            extra={"event_type": "ACTIVE_SESSION_ERROR"}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving active session"
        )


@router.post(
    "/{session_id}/end",
    response_model=JSendResponse[dict],
    summary="End session manually",
    description="Mengakhiri session secara manual (COMPLETED)"
)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Mengakhiri session secara manual."""
    try:
        # Cari session
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Active session not found"
            )
        
        # Update session status
        session.status = "COMPLETED"
        session.ended_at = datetime.utcnow()
        
        await db.commit()
        
        system_logger.info(
            f"Session ended manually: session={session_id}",
            extra={"event_type": "SESSION_END_MANUAL", "session_id": session_id}
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Session ended successfully",
            data={"session_id": session_id, "status": "COMPLETED"}
        )
        
    except Exception as e:
        system_logger.error(
            f"Error ending session: {str(e)}",
            extra={"event_type": "SESSION_END_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error ending session"
        )


@router.get(
    "/{session_id}",
    response_model=JSendResponse[SessionStatus],
    summary="Get session status",
    description="Mendapatkan status session saat ini"
)
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Mendapatkan status lengkap session."""
    try:
        # Cari session
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == current_user.user_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Session not found"
            )
        
        # Hitung jumlah soal yang sudah di-serve dan selesai
        questions_served = len(session.question_ids_served or [])
        
        # Hitung questions completed dengan query ke assessment_logs
        completed_result = await db.execute(
            text("SELECT COUNT(DISTINCT question_id) FROM assessment_logs WHERE session_id = :sid AND is_final_attempt = TRUE"),
            {"sid": session.session_id}
        )
        questions_completed = completed_result.scalar() or 0
        
        session_status = SessionStatus(
            session_id=session.session_id,
            module_id=session.module_id,
            status=session.status,
            user_theta_start=current_user.theta_individu,  # Use current user theta as start
            user_theta_current=current_user.theta_individu,  # Use current user theta
            questions_served=questions_served,
            questions_completed=questions_completed,
            started_at=session.started_at,
            ended_at=session.ended_at,
            current_question_id=session.current_question_id
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Session status retrieved successfully",
            data=session_status
        )
        
    except Exception as e:
        system_logger.error(
            f"Error getting session status: {str(e)}",
            extra={"event_type": "SESSION_STATUS_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving session status"
        )


@router.get(
    "/{session_id}/question",
    response_model=JSendResponse[QuestionResponse],
    summary="Get current question",
    description="Mendapatkan soal saat ini. Jika tidak ada soal aktif, pilih soal baru."
)
async def get_current_question(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Mendapatkan soal saat ini atau memilih soal baru jika belum ada.
    
    Algoritma:
    1. Check if there is already an active question in this session
    2. If yes, return the current question (read operation)
    3. If no, select a new question and set it as current (write operation only when necessary)
    """
    try:
        # Cari session
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Active session not found"
            )
        
        # Check if there is already an active question in this session
        if session.current_question_id is not None:
            # User is still working on this question (e.g., page refresh)
            # Return the current question without modifying served_ids
            question_result = await db.execute(
                select(Question).where(Question.question_id == session.current_question_id)
            )
            current_question = question_result.scalar_one_or_none()
            
            if not current_question:
                # Question not found, clear the invalid reference
                session.current_question_id = None
                session.current_question_attempt_count = 0
                await db.commit()
                # Fall through to select new question
            else:
                question_response = QuestionResponse(
                    session_id=session.session_id,
                    question_id=current_question.question_id,
                    module_id=current_question.module_id,
                    content=current_question.content,
                    current_difficulty=current_question.current_difficulty,
                    attempt_count=session.current_question_attempt_count + 1,
                    max_attempts=3
                )
                
                system_logger.info(
                    f"Current question retrieved: session={session_id}, question={current_question.question_id}, attempts={session.current_question_attempt_count}",
                    extra={"event_type": "CURRENT_QUESTION_RETRIEVED", "session_id": session_id, "question_id": current_question.question_id}
                )
                
                return jsend_success(
                    code=HTTP_200_OK,
                    message="Current question retrieved successfully",
                    data=question_response
                )
        
        # If we reach here, we need to select a NEW question
        # (Either session start OR previous question was finalized via /next)
        served_question_ids = session.question_ids_served or []
        selected_question = await select_next_question(
            user_theta=current_user.theta_individu,
            module_id=session.module_id,
            served_question_ids=served_question_ids,
            db=db
        )
        
        if not selected_question:
            # Tidak ada soal tersedia, selesaikan session
            session.status = "COMPLETED"
            session.ended_at = datetime.utcnow()
            await db.commit()
            
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No more questions available. Session completed."
            )
        
        # Update session to track this as the ACTIVE question
        # But DO NOT add to served_ids yet! This happens only in /next
        session.current_question_id = selected_question.question_id
        session.current_question_attempt_count = 0
        
        await db.commit()
        await db.refresh(session)
        
        question_response = QuestionResponse(
                session_id=session.session_id,
                question_id=selected_question.question_id,
                module_id=selected_question.module_id,
                content=selected_question.content,
                current_difficulty=selected_question.current_difficulty,
                attempt_count=session.current_question_attempt_count + 1,
                max_attempts=3
            )
        
        system_logger.info(
            f"New question selected: session={session_id}, question={selected_question.question_id}",
            extra={"event_type": "NEW_QUESTION_SELECTED", "session_id": session_id, "question_id": selected_question.question_id}
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="New question selected successfully",
            data=question_response
        )
        
    except Exception as e:
        system_logger.error(
            f"Error getting current question: {str(e)}",
            extra={"event_type": "GET_CURRENT_QUESTION_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error retrieving current question"
        )


@router.post(
    "/{session_id}/submit",
    response_model=JSendResponse[SubmitResult],
    summary="Submit answer",
    description="Submit jawaban user dan update Elo rating"
)
async def submit_answer(
    session_id: str,
    submit_data: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Submit jawaban user.
    
    Flow:
    1. Validasi question_id = current_question_id
    2. Eksekusi sandbox untuk check correctness
    3. Log attempt ke assessment_logs
    4. Update session state
    5. Update Elo rating jika final attempt
    """
    try:
        # Cari session
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Active session not found"
            )
        
        # Validasi question
        if submit_data.question_id != session.current_question_id:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="Question ID does not match current question"
            )
        
        # Ambil data question
        question_result = await db.execute(
            select(Question).where(Question.question_id == submit_data.question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Question not found"
            )
        
        # Eksekusi sandbox
        try:
            is_correct = await compare_query_results(
                submit_data.user_query, 
                question.target_query
            )
        except Exception as sandbox_error:
            system_logger.error(
                f"Sandbox execution error: {str(sandbox_error)}",
                extra={"event_type": "SANDBOX_ERROR", "session_id": session_id}
            )
            return jsend_fail(
                code=HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error executing query in sandbox"
            )
        
        # Update attempt count
        session.current_question_attempt_count += 1
        attempt_number = session.current_question_attempt_count
        
        # Tentukan apakah ini final attempt
        is_final = is_correct or (attempt_number >= 3)
        
        # Log attempt
        assessment_log = AssessmentLog(
            session_id=session.session_id,
            user_id=current_user.user_id,
            question_id=submit_data.question_id,
            user_query=submit_data.user_query,
            is_correct=is_correct,
            attempt_number=attempt_number,
            is_final_attempt=is_final,
            execution_time_ms=submit_data.execution_time_ms
        )
        
        db.add(assessment_log)
        
        # Update user dan session jika final attempt
        theta_before = None
        theta_after = None
        
        if is_final:
            # Implementasi Elo update
            theta_before = current_user.theta_individu
            
            # Hitung success rate menggunakan Vesin Eq. 3
            success_rate = calculate_success_rate(
                successful_attempts=1 if is_correct else 0,
                overall_attempts=attempt_number,
                correct_tests=1 if is_correct else 0,
                performed_tests=1,
                time_used_ms=submit_data.execution_time_ms,
                time_limit_ms=300000  # 5 menit default
            )
            
            # Get K-factor
            current_user_total_attempts = current_user.total_attempts
            k_factor = get_k_factor(current_user_total_attempts)
            
            # Update Elo rating
            new_theta, new_difficulty = update_elo_ratings(
                student_rating=current_user.theta_individu,
                question_difficulty=question.current_difficulty,
                success_rate=success_rate,
                k_factor=k_factor
            )
            
            theta_after = new_theta
            
            # Update user (session doesn't store theta)
            current_user.theta_individu = new_theta
            current_user.total_attempts += 1
            current_user.k_factor = get_k_factor(current_user.total_attempts)
            
            # Update question difficulty
            question.current_difficulty = new_difficulty
            
            # Update assessment log dengan theta values
            assessment_log.theta_before = theta_before
            assessment_log.theta_after = theta_after
            assessment_log.difficulty_before = question.current_difficulty
            assessment_log.difficulty_after = new_difficulty
            
            # Question sudah ditandai completed lewat assessment_log is_final_attempt
            # Tidak perlu tracking completed_question_ids di session
            
            # Reset current question
            session.current_question_id = None
            session.current_question_attempt_count = 0
            
            # Check dan unlock modul baru
            await check_and_unlock_modules(current_user, db)
        
        await db.commit()
        
        # Cek apakah masih ada soal tersedia
        next_question_available = True
        if is_final:
            served_ids = session.question_ids_served or []
            next_question = await select_next_question(
                user_theta=current_user.theta_individu,  # Use current user theta
                module_id=session.module_id,
                served_question_ids=served_ids,
                db=db
            )
            next_question_available = next_question is not None
        
        # Generate feedback
        feedback = "Jawaban benar!" if is_correct else "Jawaban salah. Silakan lanjut ke soal berikutnya!"
        if not is_final:
            feedback += f" (Attempt {attempt_number}/3)"
        
        submit_result = SubmitResult(
            is_correct=is_correct,
            is_final_attempt=is_final,
            attempt_number=attempt_number,
            feedback=feedback,
            theta_before=theta_before,
            theta_after=theta_after,
            next_question_available=next_question_available
        )
        
        # Log assessment event using helper function
        log_assessment_event(
            user_id=str(current_user.user_id),
            session_id=session_id,
            question_id=submit_data.question_id,
            theta_before=theta_before,
            theta_after=theta_after,
            is_correct=is_correct,
            execution_time_ms=submit_data.execution_time_ms,
            event_type="ANSWER_SUBMITTED",
            attempt_number=attempt_number,
            is_final_attempt=is_final
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Answer submitted successfully",
            data=submit_result
        )
        
    except Exception as e:
        system_logger.error(
            f"Error submitting answer: {str(e)}",
            extra={"event_type": "SUBMIT_ANSWER_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error submitting answer"
        )


@router.post(
    "/{session_id}/next",
    response_model=JSendResponse[NextResult],
    summary="Finalize current question and get next question",
    description="Menghitung Elo rating untuk soal saat ini (berdasarkan semua attempt) dan mendapatkan soal berikutnya"
)
async def get_next_question_endpoint(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Finalisasi soal saat ini dan dapatkan soal berikutnya.
    
    Flow:
    1. Validasi session ACTIVE milik user
    2. Pastikan ada attempt pada soal saat ini (tidak boleh skip tanpa attempt)
    3. Ambil semua attempt untuk soal ini dari assessment_logs
    4. Hitung W (success rate) menggunakan Vesin Eq. 3
    5. Update Elo rating untuk user dan question
    6. Reset current_question_id (tandai soal lama sebagai completed)
    7. Dapatkan soal baru dan update session
    """
    try:
        # Cari session
        result = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Active session not found"
            )
        
        # Validasi: harus ada attempt pada soal saat ini
        if not session.current_question_id:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No current question to finalize. Please get a question first."
            )
        
        if session.current_question_attempt_count == 0:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="Cannot finalize question without attempting it first."
            )
        
        # Ambil semua attempt untuk soal ini
        attempts_result = await db.execute(
            select(AssessmentLog).where(
                AssessmentLog.session_id == session.session_id,
                AssessmentLog.question_id == session.current_question_id
            ).order_by(AssessmentLog.attempt_number.asc())
        )
        attempts = attempts_result.scalars().all()
        
        if not attempts:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No attempts found for current question."
            )
        
        # Get question data
        question_result = await db.execute(
            select(Question).where(Question.question_id == session.current_question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Current question not found."
            )
        
        # Hitung success rate (W) menggunakan Vesin Eq. 3
        successful_attempts = sum(1 for attempt in attempts if attempt.is_correct)
        total_attempts = len(attempts)
        final_attempt = attempts[-1]  # Use final attempt for timing
        
        success_rate = calculate_success_rate(
            successful_attempts=successful_attempts,
            overall_attempts=total_attempts,
            correct_tests=1 if final_attempt.is_correct else 0,
            performed_tests=1,
            time_used_ms=final_attempt.execution_time_ms or 300000,
            time_limit_ms=300000
        )
        
        # Update Elo rating
        theta_before = current_user.theta_individu
        k_factor = get_k_factor(current_user.total_attempts)
        
        new_theta, new_difficulty = update_elo_ratings(
            student_rating=current_user.theta_individu,
            question_difficulty=question.current_difficulty,
            success_rate=success_rate,
            k_factor=k_factor
        )
        
        # Update user and question
        current_user.theta_individu = new_theta
        current_user.total_attempts += 1
        current_user.k_factor = get_k_factor(current_user.total_attempts)
        question.current_difficulty = new_difficulty
        
        # Update final attempt log dengan theta values
        final_attempt.theta_before = theta_before
        final_attempt.theta_after = new_theta
        final_attempt.difficulty_before = question.current_difficulty
        final_attempt.difficulty_after = new_difficulty
        final_attempt.is_final_attempt = True
        
        # Reset current question (tandai sebagai completed)
        session.current_question_id = None
        session.current_question_attempt_count = 0
        
        # Check dan unlock modul baru
        await check_and_unlock_modules(current_user, db)
        
        # Stagnation Detection - called after each /next endpoint
        stagnation_detected = False
        try:
            # Get last 5 final attempts for this user and session
            last_5_logs_result = await db.execute(
                select(AssessmentLog).where(
                    AssessmentLog.user_id == current_user.user_id,
                    AssessmentLog.session_id == session.session_id,
                    AssessmentLog.is_final_attempt == True
                ).order_by(AssessmentLog.timestamp.desc()).limit(5)
            )
            last_5_logs = last_5_logs_result.scalars().all()
            
            # Calculate theta deltas
            theta_deltas = []
            for log in last_5_logs:
                if log.theta_before is not None and log.theta_after is not None:
                    theta_deltas.append(log.theta_after - log.theta_before)
            
            # Check for stagnation
            stagnation_detected = detect_stagnation(theta_deltas)
            
            if stagnation_detected:
                system_logger.info(
                    f"Stagnation detected: user={current_user.user_id}, session={session_id}",
                    extra={"event_type": "STAGNATION_DETECTED", "session_id": session_id}
                )
                # TODO: Implement peer review matching logic as per technical specs
                # For now, just log the detection
                
        except Exception as e:
            system_logger.error(
                f"Error in stagnation detection: {str(e)}",
                extra={"event_type": "STAGNATION_DETECTION_ERROR", "session_id": session_id}
            )
        
        # Log assessment event for question finalization
        log_assessment_event(
            user_id=str(current_user.user_id),
            session_id=session_id,
            question_id=question.question_id,
            theta_before=theta_before,
            theta_after=new_theta,
            is_correct=final_attempt.is_correct,
            execution_time_ms=final_attempt.execution_time_ms or 0,
            event_type="QUESTION_FINALIZED",
            total_attempts=total_attempts,
            success_rate=success_rate
        )
        
        await db.commit()
        
        # Dapatkan soal berikutnya
        served_question_ids = session.question_ids_served or []
        selected_question = await select_next_question(
            user_theta=current_user.theta_individu,
            module_id=session.module_id,
            served_question_ids=served_question_ids,
            db=db
        )
        
        if not selected_question:
            # Tidak ada soal tersedia, selesaikan session
            session.status = "COMPLETED"
            session.ended_at = datetime.utcnow()
            await db.commit()
            
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No more questions available. Session completed."
            )
        
        # Update session dengan soal baru
        current_served = list(session.question_ids_served) if session.question_ids_served else []
        current_served.append(selected_question.question_id)
        session.question_ids_served = current_served
        session.current_question_id = selected_question.question_id
        session.current_question_attempt_count = 0
        
        await db.commit()
        await db.refresh(session)
        
        next_result = NextResult(
            session_id=session.session_id,
            question_id=selected_question.question_id,
            module_id=selected_question.module_id,
            content=selected_question.content,
            current_difficulty=selected_question.current_difficulty,
            attempt_count=1,  # Always start from 1 for new question
            max_attempts=3,
            theta_before=theta_before,
            theta_after=new_theta,
            previous_question_id=question.question_id,
            theta_change=new_theta - theta_before,
            stagnation_detected=stagnation_detected
        )
        
        system_logger.info(
            f"Question finalized and next served: session={session_id}, prev_question={question.question_id}, next_question={selected_question.question_id}, theta_change={new_theta - theta_before:+.1f}",
            extra={"event_type": "QUESTION_FINALIZED_NEXT", "session_id": session_id, "prev_question_id": question.question_id, "next_question_id": selected_question.question_id}
        )
        
        return jsend_success(
            code=HTTP_200_OK,
            message="Question finalized and next question retrieved successfully",
            data=next_result
        )
        
    except Exception as e:
        system_logger.error(
            f"Error finalizing question and getting next: {str(e)}",
            extra={"event_type": "FINALIZE_NEXT_ERROR", "session_id": session_id}
        )
        return jsend_error(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected error finalizing question and getting next"
        )
