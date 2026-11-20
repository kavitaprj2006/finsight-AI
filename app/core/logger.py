"""
FinSight AI - Central Logging Configuration
"""
import logging
import os
import sys

def setup_logger(name: str = "finsight") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()
