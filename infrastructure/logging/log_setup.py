# infrastructure/logging/log_setup.py
from loguru import logger

def setup_console_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=level)
