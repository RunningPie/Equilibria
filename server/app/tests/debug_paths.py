import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
print(f"LOG_DIR: {settings.LOG_DIR}")
print(f"SYSLOG_DIR: {settings.SYSLOG_DIR}")
print(f"ASSLOG_DIR: {settings.ASSLOG_DIR}")

from app.core.logging_config import setup_logging
sys_logger, ass_logger = setup_logging()

# Check handlers
for handler in sys_logger.handlers:
    if hasattr(handler, 'baseFilename'):
        print(f"System Log File: {handler.baseFilename}")
