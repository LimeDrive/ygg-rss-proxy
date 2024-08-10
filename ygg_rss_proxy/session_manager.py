import requests
import pickle
from flask import session
from sqlalchemy import text
import timeout_decorator
from tenacity import retry, stop_after_attempt, wait_fixed
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from ygg_rss_proxy.auth import ygg_login
from ygg_rss_proxy.logging_config import logger


class DatabaseConnectionError(Exception):
    pass


class SessionCreationError(Exception):
    pass


@timeout_decorator.timeout(3, exception_message="Timeout after 3 seconds")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: DatabaseConnectionError(
        "Failed to connect to the database after retries"
    ),
)
def check_database_connection():
    from ygg_rss_proxy.app import db

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise DatabaseConnectionError("Failed to connect to the database")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: SessionCreationError(
        "Failed to create a new session after retries"
    ),
)
@timeout_decorator.timeout(90, exception_message="Timeout after 90 seconds")
def new_session() -> requests.Session:
    """
    Create a new session by logging into YGG and saving the session data.

    Returns:
        requests.Session: The newly created session.
    """
    try:
        logger.info("Attempting to create a new YGG session")
        ygg_session = ygg_login()
        session_data = {
            "cookies": pickle.dumps(dict_from_cookiejar(ygg_session.cookies)),
            "headers": pickle.dumps(dict(ygg_session.headers)),
        }
        session["session_data"] = pickle.dumps(session_data)
        logger.info("New YGG session created successfully")
        return ygg_session
    except Exception as e:
        logger.error(f"Failed to create a new YGG session: {e}")
        raise SessionCreationError("Failed to create a new YGG session") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: SessionCreationError(
        "Failed to initialize session after retries"
    ),
)
def init_session() -> None:
    """
    Initialize a session by checking if session data exists.
    If it doesn't, create a new session.

    Returns:
        None
    """
    try:
        logger.info("Initializing session")
        check_database_connection()
        if "session_data" not in session:
            logger.info("No existing session found, creating a new one")
            new_session()
        else:
            logger.info("Existing session found")
    except Exception as e:
        logger.error(f"Failed to initialize session: {e}")
        raise SessionCreationError("Failed to initialize session") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: SessionCreationError(
        "Failed to get session after retries"
    ),
)
def get_session() -> requests.Session:
    """
    Retrieve a session by checking if session data exists.
    If it does, load the session data and create a new requests.Session object.
    If the session data is incomplete or doesn't exist, create a new session.

    Returns:
        requests.Session: The retrieved or newly created session.
    """
    try:
        logger.info("Attempting to retrieve session")
        if "session_data" in session:
            session_data = pickle.loads(session["session_data"])
            if "cookies" not in session_data or "headers" not in session_data:
                logger.warning("Incomplete session data found, creating a new session")
                return new_session()

            logger.info("Creating requests.Session from existing data")
            requests_session = requests.Session()
            requests_session.cookies = cookiejar_from_dict(
                pickle.loads(session_data["cookies"])
            )
            requests_session.headers.update(pickle.loads(session_data["headers"]))
            return requests_session

        logger.info("No existing session found, creating a new one")
        return new_session()
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise SessionCreationError("Failed to get session") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: Exception(
        "Failed to save session after retries"
    ),
)
def save_session(requests_session: requests.Session) -> None:
    """
    Save the session data of a requests.Session object into the Flask session.
    The session data includes cookies and headers.

    Args:
        requests_session (requests.Session): The session object to save.

    Returns:
        None
    """
    try:
        logger.info("Saving session data")
        session_data = {
            "cookies": pickle.dumps(dict_from_cookiejar(requests_session.cookies)),
            "headers": pickle.dumps(dict(requests_session.headers)),
        }
        session["session_data"] = pickle.dumps(session_data)
        logger.info("Session data saved successfully")
    except Exception as e:
        logger.error(f"Failed to save session data: {e}")
        raise Exception("Failed to save session data") from e