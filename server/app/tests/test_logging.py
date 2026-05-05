import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.logging_config import get_loggers
    print("Attempting to get loggers...")
    sys_logger, ass_logger = get_loggers()
    print("Loggers initialized successfully.")
    sys_logger.info("Test log message")
except Exception as e:
    print(f"Error initializing loggers: {e}")
    import traceback
    traceback.print_exc()
