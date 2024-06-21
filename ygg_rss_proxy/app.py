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

app = Flask(__name__)

app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{settings.db_path}"
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "session:"
app.config["SECRET_KEY"] = settings.secret_key
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"timeout": settings.db_timeout}
}

db = SQLAlchemy(app)
app.config["SESSION_SQLALCHEMY"] = db


Session(app)


@app.before_request
def before_request():
    init_session()


@app.route("/rss", methods=["GET"])
def proxy_rss():
    query_params = request.query_string.decode("utf-8")
    ygg_session = get_session()

    try:
        response = get_rss_feed(query_params, requests_session=ygg_session)
    except TimeoutError as e:
        logger.error(f"Timeout Err: {e}")

    if response.status_code in [401, 403, 307, 301]:
        # Session may have expired, re-authenticate and retry the request
        logger.debug(f"Response status : {response.status_code}")
        logger.info("Session may have expired, re-authenticating...")
        ygg_session = new_session()
        response = get_rss_feed(query_params, requests_session=ygg_session)

    if response.status_code == 200:
        # Saving session
        save_session(ygg_session)
        modified_rss = replace_torrent_links(response.content)
        return Response(modified_rss, content_type="application/xml; charset=utf-8")
    else:
        return jsonify({"error": "Failed to retrieve RSS feed"}), response.status_code


@app.route("/torrent", methods=["GET"])
def proxy_torrent():
    query_params = request.query_string.decode("utf-8")
    ygg_session = get_session()

    try:
        response = dwl_torrent(query_params, requests_session=ygg_session)
    except TimeoutError as e:
        logger.error(f"Timeout Err: {e}")

    if response.status_code in [
        401,
        403,
        307,
        301,
    ]:  # Unauthorized, session may have expired
        logger.debug(f"Response status : {response.status_code}")
        logger.info("Session may have expired, re-authenticating...")
        ygg_session = new_session()
        response = dwl_torrent(query_params, requests_session=ygg_session)

    if response.status_code == 200:
        save_session(ygg_session)
        return Response(response.content, content_type="application/x-bittorrent")
    else:
        return (
            jsonify({"error": "Failed to retrieve torrent file"}),
            response.status_code,
        )


if __name__ == "__main__":
    app.run(host=settings.dev_host, port=settings.dev_port, debug=settings.debug)
