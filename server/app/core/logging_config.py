"""
Logging Configuration Module
Technical Specifications v2 - Section 6.6, 8.1

Dual logging system:
1. System Logs (/app/logs/syslogs/) - Application events, errors, security
2. Assessment Logs (/app/logs/asslogs/) - Student assessment activities (flat file backup)
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Enables easy parsing for log analysis tools.
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
        
        # Add extra fields if present
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
        
        # Add exception info if present
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
    Setup dual logging system with auto-rotation.
    
    Args:
        log_dir: Base log directory
        syslog_dir: System logs directory
        asslog_dir: Assessment logs directory
        max_bytes: Max file size before rotation (default 10MB)
        backup_count: Number of backup files to keep
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Tuple of (system_logger, assessment_logger)
    """
    
    # Create directories
    Path(syslog_dir).mkdir(parents=True, exist_ok=True)
    Path(asslog_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for log filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ===========================================
    # SYSTEM LOGGER
    # ===========================================
    system_logger = logging.getLogger("equilibria.system")
    system_logger.setLevel(getattr(logging, log_level.upper()))
    
    # System log file with rotation
    syslog_file = Path(syslog_dir) / f"syslog_{timestamp}.json"
    syslog_handler = RotatingFileHandler(
        syslog_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    syslog_handler.setFormatter(JSONFormatter())
    syslog_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler for development
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
    
    # Assessment log file with rotation
    asslog_file = Path(asslog_dir) / f"asslog_{timestamp}.json"
    asslog_handler = RotatingFileHandler(
        asslog_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    asslog_handler.setFormatter(JSONFormatter())
    asslog_handler.setLevel(getattr(logging, log_level.upper()))
    
    assessment_logger.addHandler(asslog_handler)
    assessment_logger.propagate = False
    
    # Log initialization
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
    Get logger instances. Initialize if not already done.
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
    Helper function to log assessment events to both DB and flat file.
    Technical Specifications v2 - Section 6.6
    
    Args:
        user_id: User UUID
        session_id: Session UUID
        question_id: Question identifier
        theta_before: Theta value before update
        theta_after: Theta value after update
        is_correct: Whether answer was correct
        execution_time_ms: Time taken to solve
        event_type: Type of assessment event
        **kwargs: Additional fields to log
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