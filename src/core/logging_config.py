import logging
from typing import Dict


class ColorFormatter(logging.Formatter):
    """
    Logging formatter that wraps messages with ANSI colors per level.
    """

    RESET = "\033[0m"
    COLORS: Dict[int, str] = {
        logging.DEBUG: "\033[32m",   # green
        logging.INFO: "\033[32m",    # green
        logging.WARNING: "\033[33m", # yellow
        logging.ERROR: "\033[31m",   # red
        logging.CRITICAL: "\033[31m",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Colorize only the level name while keeping the rest untouched.
        """
        original_level = record.levelname
        color = self.COLORS.get(record.levelno)
        if color:
            record.levelname = f"{color}{original_level}{self.RESET}"
        try:
            message = super().format(record)
        finally:
            record.levelname = original_level
        return message


def setup_logging() -> None:
    """
    Configure logging with colored output for different levels.
    """
    formatter = ColorFormatter(
        fmt="%(asctime)s,%(msecs)03d | %(levelname)-8s | %(name)s | %(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # replace existing handlers to avoid duplicate outputs
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
