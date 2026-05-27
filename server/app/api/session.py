"""
API Sesi Asesmen - Implementasi practice mode individu, pembaruan rating ELO, serta deteksi stagnansi pembelajaran
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import text
from datetime import datetime, timezone
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
    detect_stagnation, check_fallback_trigger, BASE_RATING
)
from app.core.peer_matching import find_heterogeneous_peer, create_peer_session
from app.db.models import (
    User, Module, Question, AssessmentSession, 
    AssessmentLog, UserModuleProgress, PeerSession
)

router = APIRouter(
    prefix="/session",
    tags=["Assessment Session"]
)

system_logger, assessment_logger = get_loggers()


async def check_and_unlock_modules(user: User, db: AsyncSession) -> None:
    """
    Cek dan unlock modul-modul yang bisa diakses user berdasarkan theta.
    Dipanggil setelah Elo update.
    """
    try:
        # Ambil semua modul yang belum terbuka (unlocked)
        result = await db.execute(
            select(Module).where(Module.module_id != "CH01")  # CH01 selalu terbuka (unlocked)
        )
        modules = result.scalars().all()
        
        system_logger.info(
            f"Checking module unlocks: user={user.user_id}, theta={user.theta_individu}, modules_count={len(modules)}",
            extra={"event_type": "MODULE_UNLOCK_CHECK_START", "user_id": str(user.user_id), "theta": user.theta_individu}
        )
        
        for module in modules:
            # Periksa apakah pengguna sudah memiliki progres untuk modul ini
            progress_result = await db.execute(
                select(UserModuleProgress).where(
                    UserModuleProgress.user_id == user.user_id,
                    UserModuleProgress.module_id == module.module_id
                )
            )
            existing_progress = progress_result.scalar_one_or_none()
            
            system_logger.info(
                f"Module {module.module_id}: threshold={module.unlock_theta_threshold}, existing_progress={existing_progress is not None}",
                extra={"event_type": "MODULE_UNLOCK_CHECK", "module_id": module.module_id, "has_progress": existing_progress is not None}
            )
            
            unlocked_now = False
            
            if not existing_progress:
                # Periksa syarat pembukaan (unlock) modul
                if user.theta_individu >= module.unlock_theta_threshold:
                    new_progress = UserModuleProgress(
                        user_id=user.user_id,
                        module_id=module.module_id,
                        is_unlocked=True,
                        is_completed=False
                    )
                    db.add(new_progress)
                    unlocked_now = True
                    
                    system_logger.info(
                        f"Modul unlocked: user={user.user_id}, module={module.module_id}, theta={user.theta_individu}",
                        extra={"event_type": "MODULE_UNLOCK", "module_id": module.module_id}
                    )
                else:
                    system_logger.info(
                        f"Module {module.module_id} not unlocked: theta {user.theta_individu} < threshold {module.unlock_theta_threshold}",
                        extra={"event_type": "MODULE_UNLOCK_SKIP", "module_id": module.module_id}
                    )
            else:
                # Progres sudah ada tetapi mungkin masih terkunci - buka jika threshold terpenuhi
                if not existing_progress.is_unlocked and user.theta_individu >= module.unlock_theta_threshold:
                    existing_progress.is_unlocked = True
                    db.add(existing_progress)
                    unlocked_now = True
                    
                    system_logger.info(
                        f"Modul unlocked (existing): user={user.user_id}, module={module.module_id}, theta={user.theta_individu}",
                        extra={"event_type": "MODULE_UNLOCK", "module_id": module.module_id}
                    )
                else:
                    system_logger.info(
                        f"Module {module.module_id} skipped: already unlocked or threshold not met",
                        extra={"event_type": "MODULE_UNLOCK_SKIP_EXISTS", "module_id": module.module_id}
                    )
            
            # Tandai modul sebelumnya sebagai selesai saat membuka modul baru
            if unlocked_now and module.order_index > 1:
                prev_module_result = await db.execute(
                    select(Module).where(Module.order_index == module.order_index - 1)
                )
                prev_module = prev_module_result.scalar_one_or_none()
                
                if prev_module:
                    prev_progress_result = await db.execute(
                        select(UserModuleProgress).where(
                            UserModuleProgress.user_id == user.user_id,
                            UserModuleProgress.module_id == prev_module.module_id
                        )
                    )
                    prev_progress = prev_progress_result.scalar_one_or_none()
                    
                    if prev_progress and not prev_progress.is_completed:
                        prev_progress.is_completed = True
                        prev_progress.completed_at = datetime.now(timezone.utc)
                        db.add(prev_progress)
                        
                        system_logger.info(
                            f"Module completed: user={user.user_id}, module={prev_module.module_id}",
                            extra={"event_type": "MODULE_COMPLETED", "module_id": prev_module.module_id}
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
    Mulai assessment session baru dengan conflict resolution.
    
    Conflict Resolution Flow:
    - Tidak ada session ACTIVE → buat baru (201)
    - Ada session ACTIVE di modul sama → return existing (200) 
    - Ada session ACTIVE di modul berbeda → return 409 + info session aktif
    """
    try:
        # Periksa apakah pengguna sudah memiliki sesi aktif
        existing_session = await db.execute(
            select(AssessmentSession)
            .where(AssessmentSession.user_id == current_user.user_id)
            .where(AssessmentSession.status == "ACTIVE")
        )
        active_session = existing_session.scalar_one_or_none()
        
        if active_session:
            if active_session.module_id == session_request.module_id:
                # Resume idempotent - kembalikan sesi yang sudah ada
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
                # Konflik - ada sesi aktif di modul berbeda
                return jsend_fail(
                    code=status.HTTP_409_CONFLICT,
                    message=f"Kamu masih memiliki sesi aktif di {active_session.module_id}. Akhiri sesi tersebut untuk memulai sesi baru.",
                    # data={
                    #     "active_session": {
                    #         "session_id": str(active_session.session_id),
                    #         "module_id": active_session.module_id,
                    #         "started_at": active_session.started_at.isoformat()
                    #     }
                    # }
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
            # Periksa apakah modul sudah terbuka lewat UserModuleProgress
            progress_result = await db.execute(
                select(UserModuleProgress.is_unlocked)
                .where(UserModuleProgress.user_id == current_user.user_id)
                .where(UserModuleProgress.module_id == session_request.module_id)
            )
            is_unlocked = progress_result.scalar_one_or_none()

            # Jika belum terbuka, periksa batas threshold theta
            if not is_unlocked:
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
            status="ACTIVE",
            current_question_start_time=datetime.now(timezone.utc)  # Mulai hitung waktu
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        # Perbarui respons dengan nilai theta dari pengguna (tidak disimpan di sesi)
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
        # Cari sesi aktif
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
        
        # Hitung jumlah soal yang disajikan (served) dan selesai
        questions_served = len(session.question_ids_served or [])
        
        # Hitung jumlah soal selesai dengan query ke assessment_logs
        completed_result = await db.execute(
            text("SELECT COUNT(DISTINCT question_id) FROM assessment_logs WHERE session_id = :sid AND is_final_attempt = TRUE"),
            {"sid": session.session_id}
        )
        questions_completed = completed_result.scalar() or 0
        
        session_status = SessionStatus(
            session_id=session.session_id,
            module_id=session.module_id,
            status=session.status,
            user_theta_start=current_user.theta_individu,  # Gunakan rating theta pengguna saat ini sebagai awal
            user_theta_current=current_user.theta_individu,  # Gunakan rating theta pengguna saat ini
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
        # Cari sesi
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
        
        # Perbarui status sesi
        session.status = "COMPLETED"
        session.ended_at = datetime.now(timezone.utc)
        
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
        # Cari sesi
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
        
        # Hitung jumlah soal yang disajikan dan selesai
        questions_served = len(session.question_ids_served or [])
        
        # Hitung jumlah soal selesai dengan query ke assessment_logs
        completed_result = await db.execute(
            text("SELECT COUNT(DISTINCT question_id) FROM assessment_logs WHERE session_id = :sid AND is_final_attempt = TRUE"),
            {"sid": session.session_id}
        )
        questions_completed = completed_result.scalar() or 0
        
        session_status = SessionStatus(
            session_id=session.session_id,
            module_id=session.module_id,
            status=session.status,
            user_theta_start=current_user.theta_individu,  # Gunakan rating theta pengguna saat ini sebagai awal
            user_theta_current=current_user.theta_individu,  # Gunakan rating theta pengguna saat ini
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
    1. Cek apakah sudah ada soal aktif di session ini
    2. Kalau ya, return soal saat ini (operasi read)
    3. Kalau tidak, pilih soal baru dan set sebagai current (operasi write hanya kalau perlu)
    """
    try:
        # Cari sesi
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
        
        # Cek apakah sudah ada soal aktif di session ini
        if session.current_question_id is not None:
            # Pengguna masih mengerjakan soal ini (misalnya karena memuat ulang halaman)
            # Saring soal yang aktif dan belum disajikan
            question_result = await db.execute(
                select(Question).where(Question.question_id == session.current_question_id)
            )
            current_question = question_result.scalar_one_or_none()
            
            if not current_question:
                # Soal tidak ditemukan, hapus referensi yang tidak valid
                session.current_question_id = None
                session.current_question_attempt_count = 0
                await db.commit()
                # Lanjutkan untuk memilih soal baru
            else:
                question_response = QuestionResponse(
                    session_id=session.session_id,
                    question_id=current_question.question_id,
                    module_id=current_question.module_id,
                    content=current_question.content,
                    current_difficulty=current_question.current_difficulty,
                    attempt_count=session.current_question_attempt_count + 1,
                    max_attempts=3,
                    topic_tags=current_question.topic_tags
                )
                
                system_logger.info(
                    f"Soal saat ini diperoleh: session={session_id}, soal={current_question.question_id}, percobaan={session.current_question_attempt_count}",
                    extra={"event_type": "SOAL_SATU_DIPEROLEH", "session_id": session_id, "soal_id": current_question.question_id}
                )
                
                return jsend_success(
                    code=HTTP_200_OK,
                    message="Soal saat ini diperoleh dengan sukses",
                    data=question_response
                )
        
        # Kalau sampai sini, perlu pilih soal BARU
        # (Entah session baru ATAU soal sebelumnya sudah difinalisasi via /next)
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
            session.ended_at = datetime.now(timezone.utc)
            await db.commit()
            
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="Tidak ada soal tersedia lagi. Session selesai."
            )
        
        # Perbarui sesi dengan soal baru
        session.current_question_id = selected_question.question_id
        session.current_question_attempt_count = 0
        session.current_question_start_time = datetime.now(timezone.utc)  # Catat waktu mulai
        
        # Tambahkan ke served_ids agar tidak dipilih lagi pada /next atau pengecekan submit_answer
        current_served = list(session.question_ids_served) if session.question_ids_served else []
        if selected_question.question_id not in current_served:
            current_served.append(selected_question.question_id)
            session.question_ids_served = current_served
        
        await db.commit()
        await db.refresh(session)
        
        question_response = QuestionResponse(
                session_id=session.session_id,
                question_id=selected_question.question_id,
                module_id=selected_question.module_id,
                content=selected_question.content,
                current_difficulty=selected_question.current_difficulty,
                attempt_count=session.current_question_attempt_count + 1,
                max_attempts=3,
                topic_tags=selected_question.topic_tags
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
    description="Submit jawaban user. Finalisasi dan Elo update ditunda ke /next endpoint."
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
    2. Eksekusi sandbox untuk cek correctness
    3. Log attempt ke assessment_logs
    4. Update session attempt count
    5. Finalisasi (Elo update) ditunda ke /next endpoint agar user lihat feedback dulu
    """
    try:
        # Cari sesi
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
        
        # Validasi soal
        if submit_data.question_id != session.current_question_id:
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="Question ID does not match current question"
            )
        
        # Ambil data soal
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
        user_query_result = None
        error_message = None
        try:
            comparison_result = await compare_query_results(
                submit_data.user_query,
                question.target_query
            )
            is_correct = comparison_result["is_correct"]
            user_query_result = comparison_result["user_result"]
            error_message = comparison_result["error"]
        except Exception as sandbox_error:
            system_logger.error(
                f"Sandbox execution error: {str(sandbox_error)}",
                extra={"event_type": "SANDBOX_ERROR", "session_id": session_id}
            )
            return jsend_fail(
                code=HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error executing query in sandbox"
            )
        
        # Perbarui jumlah percobaan
        session.current_question_attempt_count += 1
        session.total_session_attempts += 1
        attempt_number = session.current_question_attempt_count
        
        # Hitung waktu berpikir (ms)
        thinking_time_ms = 0
        if session.current_question_start_time:
            delta = datetime.now(timezone.utc) - session.current_question_start_time
            thinking_time_ms = int(delta.total_seconds() * 1000)

        # Tentukan apakah ini percobaan terakhir (final attempt)
        is_final = is_correct or (attempt_number >= 3)
        
        # Catat log percobaan
        assessment_log = AssessmentLog(
            session_id=session.session_id,
            user_id=current_user.user_id,
            question_id=submit_data.question_id,
            user_query=submit_data.user_query,
            is_correct=is_correct,
            attempt_number=attempt_number,
            is_final_attempt=is_final,
            execution_time_ms=thinking_time_ms  # Simpan waktu mikir
        )
        
        db.add(assessment_log)
        
        # Finalisasi (update rating Elo) ditunda ke endpoint /next
        # Alur kode tunggal untuk deteksi stagnansi di endpoint /next
        
        # Periksa apakah masih ada soal tersedia (untuk informasi pengguna)
        next_question_available = True
        if is_final:
            served_ids = session.question_ids_served or []
            next_question = await select_next_question(
                user_theta=current_user.theta_individu,
                module_id=session.module_id,
                served_question_ids=served_ids,
                db=db
            )
            next_question_available = next_question is not None
        
        # Susun feedback
        if is_correct:
            feedback = "Jawaban benar!"
        elif not is_final:
            feedback = "Jawaban salah. Silakan coba lagi!"
        else:
            feedback = "Jawaban salah. Silakan lanjut ke soal berikutnya!"
        if not is_final:
            feedback += f" (Attempt {attempt_number}/3)"
        
        # Susun data hasil query jika tersedia
        query_result_data = None
        if user_query_result:
            from app.schemas.session import QueryResultData
            query_result_data = QueryResultData(
                rows=user_query_result["rows"],
                row_count=user_query_result["row_count"]
            )

        submit_result = SubmitResult(
            is_correct=is_correct,
            is_final_attempt=is_final,
            attempt_number=attempt_number,
            feedback=feedback,
            theta_before=None,  # Akan diisi di /next endpoint
            theta_after=None,   # Akan diisi di /next endpoint
            next_question_available=next_question_available,
            user_query_result=query_result_data,
            error_message=error_message
        )
        
        # Catat event asesmen menggunakan fungsi pembantu
        log_assessment_event(
            user_id=str(current_user.user_id),
            session_id=session_id,
            question_id=submit_data.question_id,
            theta_before=None,  # Akan diisi di /next endpoint
            theta_after=None,   # Akan diisi di /next endpoint
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
    
    Alur:
    1. Validasi sesi ACTIVE milik pengguna
    2. Pastikan ada percobaan pada soal saat ini (tidak boleh skip tanpa percobaan)
    3. Ambil seluruh percobaan untuk soal ini dari assessment_logs
    4. Hitung W (tingkat keberhasilan) menggunakan Persamaan Vesin 3
    5. Perbarui rating Elo untuk pengguna dan soal
    6. Reset current_question_id (tandai soal lama sebagai selesai)
    7. Ambil soal baru dan perbarui sesi
    """
    try:
        # Cari sesi
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
        
        # Validasi: harus ada percobaan pada soal saat ini
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
        
        # Ambil seluruh percobaan untuk soal ini
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
        
        # Ambil data soal
        question_result = await db.execute(
            select(Question).where(Question.question_id == session.current_question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question:
            return jsend_fail(
                code=HTTP_404_NOT_FOUND,
                message="Current question not found."
            )
        
        # Hitung tingkat keberhasilan (W) menggunakan Persamaan Vesin 3
        successful_attempts = sum(1 for attempt in attempts if attempt.is_correct)
        total_attempts = len(attempts)
        final_attempt = attempts[-1]  # Gunakan percobaan terakhir untuk pencatatan waktu
        
        success_rate = calculate_success_rate(
            successful_attempts=successful_attempts,
            overall_attempts=total_attempts,
            correct_tests=1 if final_attempt.is_correct else 0,
            performed_tests=1,
            time_used_ms=final_attempt.execution_time_ms or 300000,
            time_limit_ms=300000
        )
        
        # Perbarui rating Elo
        theta_before = current_user.theta_individu
        diff_before = question.current_difficulty  # Simpan tingkat kesulitan sebelum diperbarui
        k_factor = get_k_factor(session.total_session_attempts)
        
        new_theta, new_difficulty = update_elo_ratings(
            student_rating=current_user.theta_individu,
            question_difficulty=question.current_difficulty,
            success_rate=success_rate,
            k_factor=k_factor
        )
        
        # Perbarui pengguna dan soal
        current_user.theta_individu = new_theta
        current_user.total_attempts += 1
        current_user.k_factor = k_factor
        question.current_difficulty = new_difficulty
        
        # Perbarui log percobaan terakhir dengan nilai rating theta
        final_attempt.theta_before = theta_before
        final_attempt.theta_after = new_theta
        final_attempt.difficulty_before = diff_before
        final_attempt.difficulty_after = new_difficulty
        final_attempt.is_final_attempt = True
        
        # Reset soal aktif saat ini (tandai sebagai selesai)
        session.current_question_id = None
        session.current_question_attempt_count = 0
        
        # Periksa dan buka modul baru jika memenuhi syarat
        await check_and_unlock_modules(current_user, db)
        
        # Periksa jika modul berikutnya baru terbuka - jika ya, akhiri sesi
        current_module_result = await db.execute(
            select(Module).where(Module.module_id == session.module_id)
        )
        current_module = current_module_result.scalar_one_or_none()
        
        next_module_unlocked = False
        next_module = None
        if current_module and current_module.module_id != "CH03":
            next_module_result = await db.execute(
                select(Module).where(Module.order_index == current_module.order_index + 1)
            )
            next_module = next_module_result.scalar_one_or_none()
            if next_module:
                next_progress_result = await db.execute(
                    select(UserModuleProgress).where(
                        UserModuleProgress.user_id == current_user.user_id,
                        UserModuleProgress.module_id == next_module.module_id
                    )
                )
                next_progress = next_progress_result.scalar_one_or_none()
                if next_progress and next_progress.is_unlocked:
                    next_module_unlocked = True
                    
        if next_module_unlocked:
            # Akhiri sesi karena pengguna sudah membuka modul bab berikutnya
            session.status = "COMPLETED"
            session.ended_at = datetime.now(timezone.utc)
            await db.commit()
            
            system_logger.info(
                f"Session ended due to chapter unlock: user={current_user.user_id}, "
                f"session={session_id}, module={session.module_id}, "
                f"next_module={next_module.module_id}",
                extra={
                    "event_type": "SESSION_END_CHAPTER_UNLOCK",
                    "session_id": session_id,
                    "module_id": session.module_id,
                    "next_module_id": next_module.module_id
                }
            )
            
            return jsend_success(
                code=HTTP_200_OK,
                message=f"Congratulations! You have unlocked {next_module.module_id}. Session completed.",
                data={
                    "session_id": session_id,
                    "question_id": None,
                    "module_id": session.module_id,
                    "content": None,
                    "current_difficulty": None,
                    "attempt_count": 0,
                    "max_attempts": 3,
                    "theta_before": theta_before,
                    "theta_after": new_theta,
                    "previous_question_id": question.question_id,
                    "theta_change": new_theta - theta_before,
                    "stagnation_detected": False,
                    "peer_session_created": False,
                    "questions_served": len(session.question_ids_served or []),
                    "total_questions_available": 0,
                    "max_questions_reached": False,
                    "next_chapter_unlocked": True,
                    "unlocked_module": next_module.module_id
                }
            )
        
        # Stagnation Detection and Peer Matching - called after each /next endpoint
        stagnation_detected = False
        peer_session_created = False
        stagnation_source = None  # 'VARIANCE', 'FALLBACK', atau None
        
        try:
            # === LOGIKA DETEKSI STAGNASI SESUAI SPESIFIKASI TEKNIS v4 Section 6.3 ===
            
            # Langkah 1: Deteksi berbasis variansi (utama) - berlaku untuk semua grup
            variance_stagnation = await detect_stagnation(
                user_id=current_user.user_id,
                current_module_id=session.module_id,
                db=db
            )
            
            if variance_stagnation:
                stagnation_detected = True
                stagnation_source = 'VARIANCE'
            
            # Langkah 2: Pemicu cadangan (secondary) - hanya jika deteksi variansi tidak aktif
            # dan hanya untuk Grup A
            if not stagnation_detected and current_user.group_assignment == 'A':
                # Query 8 percobaan terakhir di modul ini (via join dengan AssessmentSession)
                recent_logs_result = await db.execute(
                    select(AssessmentLog)
                    .join(AssessmentSession, AssessmentLog.session_id == AssessmentSession.session_id)
                    .where(
                        AssessmentLog.user_id == current_user.user_id,
                        AssessmentSession.module_id == session.module_id,
                        AssessmentLog.is_final_attempt == True
                    )
                    .order_by(AssessmentLog.timestamp.desc())
                    .limit(8)
                )
                recent_logs = recent_logs_result.scalars().all()
                wrong_count = sum(1 for log in recent_logs if not log.is_correct)
                
                # Periksa status pembukaan modul berikutnya
                is_next_unlocked = True  # Default ke True
                if current_module and current_module.module_id != "CH03":
                    next_module_result = await db.execute(
                        select(Module).where(
                            Module.order_index == current_module.order_index + 1
                        )
                    )
                    next_module = next_module_result.scalar_one_or_none()
                    if next_module:
                        is_next_unlocked = (
                            current_user.theta_individu >= next_module.unlock_theta_threshold
                        )
                
                # Periksa pemicu cadangan
                fallback_triggered = check_fallback_trigger(
                    group_assignment=current_user.group_assignment,
                    current_module_id=session.module_id,
                    is_next_module_unlocked=is_next_unlocked,
                    recent_logs=recent_logs
                )
                
                if fallback_triggered:
                    stagnation_detected = True
                    stagnation_source = 'FALLBACK'
                    system_logger.info(
                        f"Stagnation fallback trigger activated: user={current_user.user_id}, "
                        f"session={session_id}, wrong_count={wrong_count}/8",
                        extra={"event_type": "STAGNATION_FALLBACK_TRIGGER", "session_id": session_id}
                    )
            
            # Langkah 3: Tangani stagnansi berdasarkan pembagian grup
            if stagnation_detected:
                # Update flag di log
                final_attempt.stagnation_detected = True

                # Update flag di user
                current_user.stagnation_ever_detected = True

                if current_user.group_assignment == 'A' and not final_attempt.is_correct:
                    # Grup A: Picu intervensi peer matching KALO jawaban salah
                    # Kalo jawaban bener mah nggak perlu peer session
                    event_type = (
                        "STAGNATION_DETECTED"
                        if stagnation_source == 'VARIANCE'
                        else "STAGNATION_FALLBACK_TRIGGER"
                    )
                    system_logger.info(
                        f"Stagnation detected for Group A: user={current_user.user_id}, "
                        f"session={session_id}, source={stagnation_source}",
                        extra={"event_type": event_type, "session_id": session_id}
                    )

                    # Cari temen buat review (peer heterogen)
                    peer = await find_heterogeneous_peer(current_user, db)

                    if peer:
                        # Buat sesi review antar user
                        await create_peer_session(
                            requester=current_user,
                            reviewer=peer,
                            question_id=question.question_id,
                            requester_query=final_attempt.user_query,
                            db=db
                        )
                        peer_session_created = True
                        
                        assessment_logger.info(
                            f"Peer session created for stagnation: "
                            f"requester={current_user.user_id}, reviewer={peer.user_id}, "
                            f"question={question.question_id}",
                            extra={
                                "event_type": "PEER_MATCH_SUCCESS",
                                "requester_id": str(current_user.user_id),
                                "reviewer_id": str(peer.user_id),
                                "question_id": question.question_id,
                                "session_id": session_id,
                                "stagnation_source": stagnation_source
                            }
                        )
                    else:
                        peer_session_created = False
                        assessment_logger.warning(
                            f"No peer available for stagnated user: {current_user.user_id}",
                            extra={
                                "event_type": "PEER_MATCH_FAIL",
                                "requester_id": str(current_user.user_id),
                                "session_id": session_id
                            }
                        )
                        
                else:  # Grup B
                    # Grup B: Catat stagnansi tetapi tidak memicu intervensi
                    assessment_logger.info(
                        f"Stagnation detected for Group B (no intervention): "
                        f"user={current_user.user_id}, session={session_id}, "
                        f"source={stagnation_source}",
                        extra={
                            "event_type": "STAGNATION_DETECTED_NO_INTERVENTION",
                            "requester_id": str(current_user.user_id),
                            "session_id": session_id,
                            "source": stagnation_source
                        }
                    )
                    # Tidak ada peer session yang dibuat untuk Grup B
                    peer_session_created = False
                    
        except Exception as e:
            system_logger.error(
                f"Error in stagnation detection/peer matching: {str(e)}",
                extra={"event_type": "STAGNATION_DETECTION_ERROR", "session_id": session_id}
            )
        
        # Catat event asesmen untuk finalisasi soal
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
        
        # Ambil soal berikutnya
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
            session.ended_at = datetime.now(timezone.utc)
            await db.commit()
            
            return jsend_fail(
                code=HTTP_400_BAD_REQUEST,
                message="No more questions available. Session completed."
            )
        
        # Perbarui sesi dengan soal baru
        current_served = list(session.question_ids_served) if session.question_ids_served else []
        current_served.append(selected_question.question_id)
        session.question_ids_served = current_served
        session.current_question_id = selected_question.question_id
        session.current_question_attempt_count = 0
        session.current_question_start_time = datetime.now(timezone.utc)  # Reset penghitung waktu untuk soal baru
        
        # Hitung jumlah soal yang disajikan dan total yang tersedia
        questions_served = len(current_served)
        
        # Ambil total jumlah soal yang tersedia di modul ini
        total_questions_result = await db.execute(
            select(Question).where(Question.module_id == session.module_id)
        )
        total_questions_available = len(total_questions_result.scalars().all())
        
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
            stagnation_detected=stagnation_detected,
            peer_session_created=peer_session_created,
            questions_served=questions_served,
            total_questions_available=total_questions_available
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
