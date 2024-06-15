# logging_config.py
from loguru import logger
from ygg_rss_proxy.settings import settings
import sys
import logging
import inspect
import re
import stackprinter


class SecretFilter:
    def __init__(self, patterns):
        self._patterns = patterns

    def __call__(self, record):
        record["message"] = self.redact(record["message"])
        if "stack" in record["extra"]:
            record["extra"]["stack"] = self.redact(record["extra"]["stack"])
        return record

    def redact(self, message):
        for pattern in self._patterns:
            message = re.sub(pattern, "**<REDACTED>**", message)
        return message


patterns = [
    r"passkey=[^&\s]+",
    r"'value': '([^']+)'",
    r"value=\'[^\']+\'",
    r"cf_clearance=[^;\s]+",
    r"ygg_=[^;\s]+",
]

logger.remove()


def format(record):
    format_ = "{time} {level} {function} {message}\n"
    pats = [
        r"passkey=[^&\s]+",
        r"'value': '([^']+)'",
        r"value=\'[^\']+\'",
        r"cf_clearance=[^;\s]+",
        r"ygg_=[^;\s]+",
        r"[A-Za-z0-9]+\' \[GET\] of ygg_rss_proxy\.app>",
        r"session:[A-Za-z0-9_-]+",
        r"(\{'session_data':\s*b'|<Session data b'|serialized_session_data\s*=\s*b')[\s\S]*?\.(?=\s)",
    ]

    if record["exception"] is not None:
        stack = stackprinter.format(
            record["exception"],
            suppressed_vars=[r".*ygg_playload.*", r".*query_params.*"],
        )
        for pat in pats:
            stack = re.sub(pat, "**<REDACTED>**", stack)
        record["extra"]["stack"] = stack
        format_ += "{extra[stack]}\n"
    return format_


logger.add(
    sys.stdout,
    format=format,
    level=settings.log_level.value,
    colorize=True,
    filter=SecretFilter(patterns),
)

logger.add(
    settings.log_path,
    format=format,
    level="DEBUG",
    rotation="2 MB",
    retention="5 days",
    compression="zip",
    enqueue=True,
    filter=SecretFilter(patterns),
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
