import os
from ygg_rss_proxy.settings import settings
from ygg_rss_proxy.app import app
from ygg_rss_proxy.logging_config import logger
from ygg_rss_proxy.run_gunicorn import GunicornApp

options = {
    "bind": f"{settings.gunicorn_binder}:{settings.gunicorn_port}",
    "workers": settings.gunicorn_workers,
    "preload_app": True,
}

logger.info("----------------------------------------------------------")
logger.info("Checking directories...")
logger.info("----------------------------------------------------------")

directories = ["/app/config", os.path.dirname(settings.db_path), os.path.dirname(settings.log_path)]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory {directory}.")
    else:
        logger.info(f"Directory {directory} already exists.")

logger.info("----------------------------------------------------------")
logger.info(
    f"Starting ygg_rss_proxy on {settings.rss_shema}://{settings.rss_host}:{settings.rss_port}"
)
logger.info("----------------------------------------------------------")

GunicornApp(app, options).run()
