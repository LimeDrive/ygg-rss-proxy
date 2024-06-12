# logging_config.py
from loguru import logger
from ygg_rss_proxy.settings import settings
import sys
import logging
import inspect
import json
import re

def obfuscate_sensitive_info(message):
    # Hide the passkey in the URL
    message = re.sub(r'passkey=[^&]+', 'passkey=********', message)
    # Hide the ygg_ cookie value
    message = re.sub(r'ygg_=[^;]+', 'ygg_=********', message)
    message = re.sub(r"'value': '([^']+)'", "'value': '********'", message)
    # Parse the message as JSON
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return message

    # Obfuscate the password and ID
    if 'pass' in data:
        data['pass'] = '********'
    if 'id' in data:
        data['id'] = '********'

    # Return the obfuscated message
    return json.dumps(data)

logger.remove()
logger.add(
    sys.stdout,
    format="{time} {level} {function} {message}",
    level=settings.log_level.value,
    colorize=True,
    filter=lambda record: obfuscate_sensitive_info(record["message"])
)

logger.add(
    settings.log_path,
    format="{time} {level} {function} {message}",
    level="DEBUG",
    rotation="5 MB",
    retention="5 days",
    compression="zip",
    enqueue=True,
    filter=lambda record: obfuscate_sensitive_info(record["message"])
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
