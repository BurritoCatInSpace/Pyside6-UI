from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
import warnings
# Try to import from platforms first, fallback to ui app constants
try:
    from platforms.constants import LOGGING_ENABLED, LOG_TO_FILE
except ImportError:
    try:
        # If running from ui directory, try parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from platforms.constants import LOGGING_ENABLED, LOG_TO_FILE
    except ImportError:
        from app.constants import LOGGING_ENABLED, LOG_TO_FILE


SAVE_LOGS_TO_FILE = LOG_TO_FILE
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
MAX_LOG_FILES = 5


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "threadName"):
            record.threadName = "MainThread"
        if not hasattr(record, "process"):
            record.process = os.getpid()
        if record.exc_info:
            record.exc_text = "".join(traceback.format_exception(*record.exc_info))
        else:
            record.exc_text = ""
        return super().format(record)


def _configure_handlers(root_logger: logging.Logger) -> None:
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = CustomFormatter(
        "%(asctime)s - %(levelname)s - [%(threadName)s] - %(name)s - %(message)s"
        "%(exc_text)s"
    )

    if SAVE_LOGS_TO_FILE:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(
            log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file, maxBytes=MAX_LOG_SIZE, backupCount=MAX_LOG_FILES, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def setup_logging() -> logging.Logger:
    """Configure logging with rotation and proper error handling.

    Matches the behavior previously implemented in main.py.
    """
    try:
        if not LOGGING_ENABLED:
            # Minimal no-op configuration to avoid noisy handlers
            logging.getLogger().handlers.clear()
            logging.getLogger().addHandler(logging.NullHandler())
            logger = logging.getLogger(__name__)
            logger.disabled = True
            return logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        _configure_handlers(root_logger)

        # Configure Python's built-in warnings
        logging.captureWarnings(True)

        def handle_exception(exc_type, exc_value, exc_traceback):  # type: ignore[no-redef]
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            root_logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            root_logger.error(
                "Exception Type: %s\nException Value: %s\nTraceback:\n%s",
                exc_type.__name__,
                str(exc_value),
                "".join(traceback.format_tb(exc_traceback)),
            )

        sys.excepthook = handle_exception

        def handle_warning(message, category, filename, lineno, file=None, line=None):
            root_logger.warning(
                f"Warning: {category.__name__}: {message}",
                extra={"filename": filename, "lineno": lineno, "line": line},
            )

        warnings.showwarning = handle_warning  # type: ignore[assignment]

        logger = logging.getLogger(__name__)
        logger.info("Logging configured successfully")
        return logger
    except Exception as e:  # pragma: no cover - fallback path
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s%(exc_info)s")
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to configure logging: {str(e)}")
        return logger


