import requests
import pickle
from flask import session
from sqlalchemy import text
import timeout_decorator
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from ygg_rss_proxy.auth import ygg_login
from ygg_rss_proxy.logging_config import logger

@timeout_decorator.timeout(3, exception_message=f"Timeout after 3 seconds")
def check_database_connection():
    from ygg_rss_proxy.app import db
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise Exception("Failed to connect to the database")

def new_session() -> requests.Session:
    """
    This function creates a new session by logging into YGG and saving the session data.

    Returns:
        requests.Session: The newly created session.
    """
    check_database_connection()
    ygg_session = ygg_login()
    session_data = {
        "cookies": pickle.dumps(dict_from_cookiejar(ygg_session.cookies)),
        "headers": pickle.dumps(dict(ygg_session.headers)),
    }
    session["session_data"] = pickle.dumps(session_data)
    return ygg_session


def init_session() -> None:
    """
    This function initializes a session by checking if session data exists.
    If it doesn't, it calls the new_session() function to create a new session.

    Returns:
        None
    """
    check_database_connection()
    if "session_data" not in session:
        new_session()

@timeout_decorator.timeout(90, exception_message=f"Timeout after 90 seconds")
def get_session() -> requests.Session:
    """
    This function retrieves a session by checking if session data exists.
    If it does, it loads the session data and creates a new requests.Session object.
    If the session data is incomplete or doesn't exist, it calls the new_session() function to create a new session.

    Returns:
        requests.Session: The retrieved or newly created session.
    """
    check_database_connection()
    if "session_data" in session:
        session_data = pickle.loads(session["session_data"])
        if "cookies" not in session_data or "headers" not in session_data:
            return new_session()

        requests_session = requests.Session()
        requests_session.cookies = cookiejar_from_dict(
            pickle.loads(session_data["cookies"])
        )
        requests_session.headers.update(pickle.loads(session_data["headers"]))
        return requests_session

    return new_session()


def save_session(requests_session: requests.Session) -> None:
    """
    This function saves the session data of a requests.Session object into the Flask session.
    The session data includes cookies and headers.

    Args:
        requests_session (requests.Session): The session object to save.

    Returns:
        None
    """
    check_database_connection()
    session_data = {
        "cookies": pickle.dumps(dict_from_cookiejar(requests_session.cookies)),
        "headers": pickle.dumps(dict(requests_session.headers)),
    }
    session["session_data"] = pickle.dumps(session_data)
