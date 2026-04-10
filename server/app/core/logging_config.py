"""
Modul Konfigurasi Logging
Spesifikasi Teknis v2 - Bagian 6.6, 8.1

Sistem dual logging:
1. System Logs (/app/logs/syslogs/) - Event aplikasi, error, security
2. Assessment Logs (/app/logs/asslogs/) - Aktivitas assessment siswa (backup flat file)
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from typing import Optional


def _get_log_file_path(log_dir: Path, prefix: str, max_bytes: int, max_age_days: int = 1) -> Path:
    """
    Find an existing log file to reuse if it meets criteria:
    - File size < max_bytes
    - File age < max_age_days
    Otherwise create a new file with current timestamp.
    """
    now = datetime.now()
    current_date = now.date()
    
    # Look for existing log files matching pattern: {prefix}_YYYYMMDD_HHMMSS.json
    pattern = f"{prefix}_*.json"
    existing_files = sorted(log_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for file_path in existing_files:
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size >= max_bytes:
                continue
            
            # Check file age (parse from filename or use mtime)
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            file_date = file_mtime.date()
            age_days = (current_date - file_date).days
            
            if age_days < max_age_days:
                return file_path
        except (OSError, ValueError):
            continue
    
    # No suitable file found, create new one
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return log_dir / f"{prefix}_{timestamp}.json"


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter untuk structured logging.
    Memudahkan parsing untuk log analysis tools.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Tambahkan extra fields kalau ada
        if hasattr(record, 'user_id'):
            log_data['user_id'] = str(record.user_id)
        if hasattr(record, 'session_id'):
            log_data['session_id'] = str(record.session_id)
        if hasattr(record, 'question_id'):
            log_data['question_id'] = record.question_id
        if hasattr(record, 'theta_before'):
            log_data['theta_before'] = record.theta_before
        if hasattr(record, 'theta_after'):
            log_data['theta_after'] = record.theta_after
        if hasattr(record, 'is_correct'):
            log_data['is_correct'] = record.is_correct
        if hasattr(record, 'execution_time_ms'):
            log_data['execution_time_ms'] = record.execution_time_ms
        if hasattr(record, 'event_type'):
            log_data['event_type'] = record.event_type
        
        # Tambahkan exception info kalau ada
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(
    log_dir: str = "/app/logs",
    syslog_dir: str = "/app/logs/syslogs",
    asslog_dir: str = "/app/logs/asslogs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: str = "INFO"
) -> tuple[logging.Logger, logging.Logger]:
    """
    Setup sistem dual logging dengan auto-rotation.
    
    Args:
        log_dir: Base log directory
        syslog_dir: System logs directory
        asslog_dir: Assessment logs directory
        max_bytes: Max file size sebelum rotation (default 10MB)
        backup_count: Jumlah backup files yang disimpan
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Tuple of (system_logger, assessment_logger)
    """
    
    # Buat directories
    syslog_path = Path(syslog_dir)
    asslog_path = Path(asslog_dir)
    syslog_path.mkdir(parents=True, exist_ok=True)
    asslog_path.mkdir(parents=True, exist_ok=True)
    
    # Get or create log file paths (reuse if <10MB and <1 day old)
    syslog_file = _get_log_file_path(syslog_path, "syslog", max_bytes, max_age_days=1)
    asslog_file = _get_log_file_path(asslog_path, "asslog", max_bytes, max_age_days=1)
    
    # ===========================================
    # SYSTEM LOGGER
    # ===========================================
    system_logger = logging.getLogger("equilibria.system")
    system_logger.setLevel(getattr(logging, log_level.upper()))
    
    # System log file dengan rotation
    syslog_handler = RotatingFileHandler(
        syslog_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    syslog_handler.setFormatter(JSONFormatter())
    syslog_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler untuk development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    system_logger.addHandler(syslog_handler)
    system_logger.addHandler(console_handler)
    system_logger.propagate = False
    
    # ===========================================
    # ASSESSMENT LOGGER
    # ===========================================
    assessment_logger = logging.getLogger("equilibria.assessment")
    assessment_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Assessment log file dengan rotation
    asslog_handler = RotatingFileHandler(
        asslog_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    asslog_handler.setFormatter(JSONFormatter())
    asslog_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler untuk assessment logs (so they appear in stdout)
    ass_console_handler = logging.StreamHandler(sys.stdout)
    ass_console_handler.setFormatter(JSONFormatter())
    ass_console_handler.setLevel(getattr(logging, log_level.upper()))
    
    assessment_logger.addHandler(asslog_handler)
    assessment_logger.addHandler(ass_console_handler)
    assessment_logger.propagate = False
    
    # Log inisialisasi
    system_logger.info(
        "Logging system initialized",
        extra={
            "event_type": "SYSTEM_INIT",
            "syslog_file": str(syslog_file),
            "asslog_file": str(asslog_file),
            "max_bytes": max_bytes,
            "backup_count": backup_count
        }
    )
    
    return system_logger, assessment_logger


# Global logger instances (initialized on import)
system_logger: Optional[logging.Logger] = None
assessment_logger: Optional[logging.Logger] = None


def get_loggers() -> tuple[logging.Logger, logging.Logger]:
    """
    Get logger instances. Inisialisasi kalau belum dilakukan.
    """
    global system_logger, assessment_logger
    
    if system_logger is None or assessment_logger is None:
        system_logger, assessment_logger = setup_logging()
    
    return system_logger, assessment_logger


def log_assessment_event(
    user_id: str,
    session_id: str,
    question_id: str,
    theta_before: float,
    theta_after: float,
    is_correct: bool,
    execution_time_ms: int,
    event_type: str = "ASSESSMENT_SUBMIT",
    **kwargs
):
    """
    Helper function untuk log assessment events ke DB dan flat file.
    Spesifikasi Teknis v2 - Bagian 6.6
    
    Args:
        user_id: User UUID
        session_id: Session UUID
        question_id: Question identifier
        theta_before: Theta value sebelum update
        theta_after: Theta value setelah update
        is_correct: Apakah jawaban benar
        execution_time_ms: Waktu yang dihabiskan untuk solve
        event_type: Tipe assessment event
        **kwargs: Additional fields untuk log
    """
    global assessment_logger
    
    if assessment_logger is None:
        _, assessment_logger = get_loggers()
    
    assessment_logger.info(
        f"Assessment event: {event_type}",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "question_id": question_id,
            "theta_before": theta_before,
            "theta_after": theta_after,
            "is_correct": is_correct,
            "execution_time_ms": execution_time_ms,
            "event_type": event_type,
            **kwargs
        }
    )