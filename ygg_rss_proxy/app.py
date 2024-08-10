from flask import Flask, request, jsonify, Response
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from timeout_decorator import TimeoutError
from ygg_rss_proxy.rss import get_rss_feed, replace_torrent_links
from ygg_rss_proxy.settings import settings
from ygg_rss_proxy.logging_config import logger
from ygg_rss_proxy.torrent import dwl_torrent
from ygg_rss_proxy.session_manager import (
    save_session,
    get_session,
    new_session,
    init_session,
)

# Custom exceptions
class RSSProxyError(Exception):
    """Base exception for RSS proxy errors"""

class RSSFeedRetrievalError(RSSProxyError):
    """Exception raised when RSS feed retrieval fails"""

class TorrentRetrievalError(RSSProxyError):
    """Exception raised when torrent file retrieval fails"""

app = Flask(__name__)

# Flask and SQLAlchemy configuration
app.config.update(
    SESSION_TYPE="sqlalchemy",
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{settings.db_path}",
    SESSION_SQLALCHEMY_TABLE="sessions",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_KEY_PREFIX="session:",
    SECRET_KEY=settings.secret_key,
    SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"timeout": settings.db_timeout}}
)

db = SQLAlchemy(app)
app.config["SESSION_SQLALCHEMY"] = db
Session(app)

@app.before_request
def before_request():
    logger.info("Initializing session before request")
    try:
        init_session()
    except Exception as e:
        logger.error(f"Failed to initialize session: {str(e)}")
        return jsonify({"error": "Failed to initialize session"}), 500

@app.route("/rss", methods=["GET"])
def proxy_rss():
    logger.info("Received request for RSS feed")
    query_params = request.query_string.decode("utf-8")
    logger.debug(f"Query parameters: {query_params}")

    try:
        ygg_session = get_session()
        response = get_rss_feed(query_params, requests_session=ygg_session)
        
        if response.status_code in [401, 403, 307, 301]:
            logger.warning(f"Received status code {response.status_code}, attempting re-authentication")
            ygg_session = new_session()
            response = get_rss_feed(query_params, requests_session=ygg_session)
        
        if response.status_code == 200:
            logger.info("Successfully retrieved RSS feed")
            save_session(ygg_session)
            modified_rss = replace_torrent_links(response.content)
            return Response(modified_rss, content_type="application/xml; charset=utf-8")
        else:
            logger.error(f"Failed to retrieve RSS feed. Status code: {response.status_code}")
            raise RSSFeedRetrievalError(f"Failed to retrieve RSS feed. Status code: {response.status_code}")

    except TimeoutError as e:
        logger.error(f"Timeout error while retrieving RSS feed: {str(e)}")
        return jsonify({"error": "Request timed out"}), 504
    except RSSFeedRetrievalError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in proxy_rss: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/torrent", methods=["GET"])
def proxy_torrent():
    logger.info("Received request for torrent file")
    query_params = request.query_string.decode("utf-8")
    logger.debug(f"Query parameters: {query_params}")

    try:
        ygg_session = get_session()
        response = dwl_torrent(query_params, requests_session=ygg_session)
        
        if response.status_code in [401, 403, 307, 301]:
            logger.warning(f"Received status code {response.status_code}, attempting re-authentication")
            ygg_session = new_session()
            response = dwl_torrent(query_params, requests_session=ygg_session)
        
        if response.status_code == 200:
            logger.info("Successfully retrieved torrent file")
            save_session(ygg_session)
            return Response(response.content, content_type="application/x-bittorrent")
        else:
            logger.error(f"Failed to retrieve torrent file. Status code: {response.status_code}")
            raise TorrentRetrievalError(f"Failed to retrieve torrent file. Status code: {response.status_code}")

    except TimeoutError as e:
        logger.error(f"Timeout error while retrieving torrent file: {str(e)}")
        return jsonify({"error": "Request timed out"}), 504
    except TorrentRetrievalError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in proxy_torrent: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    logger.info(f"Starting YGG RSS Proxy on {settings.dev_host}:{settings.dev_port}")
    app.run(host=settings.dev_host, port=settings.dev_port, debug=settings.debug)