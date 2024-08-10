import logging
from typing import Union, Literal, Optional, List, Tuple
from urllib.parse import urlencode

import orjson
import requests

from .response_models import (
    SessionsListResponse,
    SesssionCreateResponse,
    FlareSolverOK,
    GetPostRequestResponse,
)
from .solver_exceptions import UnsupportedProxySchema, FlareSolverError

# Set up logging
logger = logging.getLogger(__name__)

def _check_proxy_url(proxy_url: str) -> None:
    """
    Check if the proxy URL has a supported schema.

    Args:
        proxy_url (str): The proxy URL to check.

    Raises:
        UnsupportedProxySchema: If the proxy schema is not supported.
    """
    supported_schemas = ['http://', 'https://', 'socks4://', 'socks5://']
    if not any(proxy_url.startswith(schema) for schema in supported_schemas):
        logger.error(f"Unsupported proxy schema: {proxy_url.split('://', 1)[0]}")
        raise UnsupportedProxySchema(
            f"Supported proxy schemas: {supported_schemas}. Yours: {proxy_url.split('://', 1)[0]}"
        )

class FlareSolverr:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[Union[str, int]] = "8191",
        http_schema: Literal["http", "https"] = "http",
        additional_headers: dict = None,
        v: str = "v1",
    ) -> None:
        """
        Initialize the FlareSolverr class.

        Args:
            host (str): Host address for FlareSolverr. Default: localhost.
            port (Optional[Union[str, int]]): Host port for FlareSolverr. Default: 8191.
            http_schema (Literal["http", "https"]): Http schema for the requests module. Default: http
            additional_headers (dict): Additional headers for requests to FlareSolverr.
            v (str): FlareSolverr endpoint version. Do not change until strictly necessary.
        """
        self.req_session = requests.Session()
        ah = additional_headers if additional_headers is not None else {}
        self.req_session.headers.update({"Content-Type": "application/json", **ah})

        self.host = host
        self.port = str(port) if port is not None else None
        self.http_schema = http_schema
        self.v = v
        self.flare_solverr_url = (
            f"{http_schema}://{host}{':' + self.port if port is not None else ''}"
        )
        self.version, self.user_agent = self._check_flare_solver()
        self.flare_solverr_url = (
            f"{http_schema}://{host}{':' + self.port if port is not None else ''}/{v}"
        )
        logger.info(f"FlareSolverr initialized with URL: {self.flare_solverr_url}")

    def _check_flare_solver(self) -> Tuple[str, str]:
        """
        Check the FlareSolverr version and user agent.

        Returns:
            Tuple[str, str]: The version and user agent of FlareSolverr.

        Raises:
            FlareSolverError: If unable to connect to FlareSolverr.
        """
        try:
            response = self.req_session.get(self.flare_solverr_url)
            response.raise_for_status()
            resp_dict = orjson.loads(response.content)
            logger.info(f"FlareSolverr version: {resp_dict['version']}, User Agent: {resp_dict['userAgent']}")
            return resp_dict["version"], resp_dict["userAgent"]
        except requests.RequestException as e:
            logger.error(f"Failed to connect to FlareSolverr: {str(e)}")
            raise FlareSolverError(f"Failed to connect to FlareSolverr: {str(e)}")

    @property
    def sessions(self) -> List[str]:
        """
        Get session ids as a list.

        Returns:
            List[str]: All session ids as a list.

        Raises:
            FlareSolverError: If unable to retrieve sessions.
        """
        payload = {"cmd": "sessions.list"}
        try:
            response = self.req_session.post(self.flare_solverr_url, json=payload)
            response.raise_for_status()
            response_dict = orjson.loads(response.content)

            if response_dict["status"] != "ok":
                raise FlareSolverError.from_dict(response_dict)
            sessions = SessionsListResponse.from_dict(response_dict).sessions
            logger.info(f"Retrieved {len(sessions)} sessions")
            return sessions
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve sessions: {str(e)}")
            raise FlareSolverError(f"Failed to retrieve sessions: {str(e)}")

    def create_session(
        self, session_id: str = None, proxy_url: str = None
    ) -> SesssionCreateResponse:
        """
        Create a session. This will launch a new browser instance which will retain cookies.

        Args:
            session_id (str, optional): Session ID for the new session.
            proxy_url (str, optional): Proxy URL for the session.

        Returns:
            SesssionCreateResponse: FlareSolverr sessions.create response as a class.

        Raises:
            FlareSolverError: If unable to create a session.
        """
        payload = {"cmd": "sessions.create"}
        if session_id:
            payload["session"] = session_id
        if proxy_url:
            _check_proxy_url(proxy_url)
            payload["proxy"] = {"url": proxy_url}

        try:
            response = self.req_session.post(self.flare_solverr_url, json=payload)
            response.raise_for_status()
            response_dict = orjson.loads(response.content)

            if response_dict["status"] != "ok":
                raise FlareSolverError.from_dict(response_dict)
            logger.info(f"Session created successfully: {session_id if session_id else 'default'}")
            return SesssionCreateResponse.from_dict(response_dict)
        except requests.RequestException as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise FlareSolverError(f"Failed to create session: {str(e)}")

    def destroy_session(self, session_id: str) -> FlareSolverOK:
        """
        Destroy an existing FlareSolverr session.

        Args:
            session_id (str): The ID of the session to destroy.

        Returns:
            FlareSolverOK: Class containing OK message.

        Raises:
            FlareSolverError: If unable to destroy the session.
        """
        payload = {"cmd": "sessions.destroy", "session": session_id}

        try:
            response = self.req_session.post(self.flare_solverr_url, json=payload)
            response.raise_for_status()
            response_dict = orjson.loads(response.content)

            if response_dict["status"] != "ok":
                raise FlareSolverError.from_dict(response_dict)
            logger.info(f"Session destroyed successfully: {session_id}")
            return FlareSolverOK.from_dict(response_dict)
        except requests.RequestException as e:
            logger.error(f"Failed to destroy session {session_id}: {str(e)}")
            raise FlareSolverError(f"Failed to destroy session {session_id}: {str(e)}")

    def _do_the_work_for_get_post(
        self, payload: dict, session, session_ttl_minutes, cookies, proxy_url
    ) -> GetPostRequestResponse:
        """
        Helper method to handle GET and POST requests.

        Args:
            payload (dict): The request payload.
            session (str, optional): Session ID for the request.
            session_ttl_minutes (int, optional): Session TTL in minutes.
            cookies (List[dict], optional): Additional cookies for the request.
            proxy_url (str, optional): Proxy URL for the request.

        Returns:
            GetPostRequestResponse: The response from FlareSolverr.

        Raises:
            FlareSolverError: If the request fails.
        """
        if session:
            payload["session"] = session
        if session_ttl_minutes:
            payload["session_ttl_minutes"] = session_ttl_minutes
        if cookies:
            payload["cookies"] = cookies
        if proxy_url:
            _check_proxy_url(proxy_url)
            payload["proxy"] = {"url": proxy_url}

        try:
            response = self.req_session.post(self.flare_solverr_url, json=payload)
            response.raise_for_status()
            response_dict = orjson.loads(response.content)

            if response_dict["status"] != "ok":
                raise FlareSolverError.from_dict(response_dict)
            logger.info(f"Request successful: {payload['cmd']} to {payload['url']}")
            return GetPostRequestResponse.from_dict(response_dict)
        except requests.RequestException as e:
            logger.error(f"Request failed: {payload['cmd']} to {payload['url']} - {str(e)}")
            raise FlareSolverError(f"Request failed: {payload['cmd']} to {payload['url']} - {str(e)}")

    def request_get(
        self,
        url: str,
        session: Optional[str] = None,
        session_ttl_minutes: Optional[int] = None,
        max_timeout: int = 60000,
        cookies: Optional[List[dict]] = None,
        return_only_cookies: bool = False,
        proxy_url: Optional[str] = None,
    ) -> GetPostRequestResponse:
        """
        Perform a GET request through FlareSolverr.

        Args:
            url (str): The URL to request.
            session (Optional[str]): Session ID for the request.
            session_ttl_minutes (Optional[int]): Session TTL in minutes.
            max_timeout (int): Max timeout to solve the challenge in milliseconds.
            cookies (Optional[List[dict]]): Additional cookies for the request.
            return_only_cookies (bool): Only return the cookies if True.
            proxy_url (Optional[str]): Proxy URL for the request.

        Returns:
            GetPostRequestResponse: The response from FlareSolverr.
        """
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": max_timeout,
            "returnOnlyCookies": return_only_cookies,
        }
        logger.info(f"Initiating GET request to {url}")
        return self._do_the_work_for_get_post(
            payload, session, session_ttl_minutes, cookies, proxy_url
        )

    def request_post(
        self,
        url: str,
        post_data: dict,
        session: Optional[str] = None,
        session_ttl_minutes: Optional[int] = None,
        max_timeout: int = 60000,
        cookies: Optional[List[dict]] = None,
        return_only_cookies: bool = False,
        proxy_url: Optional[str] = None,
    ) -> GetPostRequestResponse:
        """
        Perform a POST request through FlareSolverr.

        Args:
            url (str): The URL to request.
            post_data (dict): Data to post as a dictionary.
            session (Optional[str]): Session ID for the request.
            session_ttl_minutes (Optional[int]): Session TTL in minutes.
            max_timeout (int): Max timeout to solve the challenge in milliseconds.
            cookies (Optional[List[dict]]): Additional cookies for the request.
            return_only_cookies (bool): Only return the cookies if True.
            proxy_url (Optional[str]): Proxy URL for the request.

        Returns:
            GetPostRequestResponse: The response from FlareSolverr.
        """
        payload = {
            "cmd": "request.post",
            "url": url,
            "maxTimeout": max_timeout,
            "returnOnlyCookies": return_only_cookies,
            "postData": urlencode(post_data),
        }
        logger.info(f"Initiating POST request to {url}")
        return self._do_the_work_for_get_post(
            payload, session, session_ttl_minutes, cookies, proxy_url
        )