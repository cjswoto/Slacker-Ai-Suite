# utils/logger.py
import os
import logging
from logging.handlers import RotatingFileHandler

# Configuration
LOG_DIR      = "logs"
LOG_FILENAME = "pipeline.log"
MAX_BYTES    = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

def get_logger(name: str = None) -> logging.Logger:
    """
    Returns a logger that writes both to console and to a rotating file.
    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name or __name__)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
        formatter = logging.Formatter(fmt)

        # Rotating file handler
        fh = RotatingFileHandler(
            filename=os.path.join(LOG_DIR, LOG_FILENAME),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
