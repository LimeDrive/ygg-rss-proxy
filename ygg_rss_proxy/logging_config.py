# logging_config.py
from loguru import logger
from ygg_rss_proxy.settings import settings
import sys
import logging
import inspect

logger.remove()
logger.add(
    sys.stdout,
    format="{time} {level} {message}",
    level=settings.log_level.value,
    colorize=True,
)

logger.add(
    settings.log_path,
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="5 MB",
    retention="5 days",
    compression="zip",
    enqueue=True,
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("flask").setLevel(logging.DEBUG)
logging.getLogger("gunicorn").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)
