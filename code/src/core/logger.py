import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "J_AI") -> logging.Logger:
    logger = logging.getLogger(name)

    # avoid duplicate handlers if setup_logger is called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir = os.getenv("JAI_LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "j_ai.log")

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
