import enum
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """Settings for the application"""

    # ygg.re
    ygg_user: str = "user"
    ygg_pass: str = "pass"
    ygg_url: str = "https://www.ygg.re"

    # RSS PROXY
    rss_host: str = "localhost"
    rss_port: int = 8080
    rss_shema: str = "http"

    # FLARESOLVERR
    flaresolverr_host: str = "localhost"
    flaresolverr_shema: str = "http"
    flaresolverr_port: int = 8191

    # GUNICORN
    gunicorn_workers: int = 4
    gunicorn_port: int = 8080
    gunicorn_binder: str = "0.0.0.0"
    gunicorn_timeout: int = 120

    # LOGGING
    log_level: LogLevel = LogLevel.INFO
    log_path: str = "/app/config/logs/rss-proxy.log"

    # FLASK SESSIONS
    secret_key: str = "superkey_that_can_be_changed"
    db_path: str = "/app/config/rss-proxy.db"

    # User-Agent
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # DEVELOPMENT
    debug: bool = True
    dev_host: str = "0.0.0.0"
    dev_port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env", secrets_dir="/run/secrets", env_file_encoding="utf-8"
    )


try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Configuration validation error: {e}")
