import requests
import timeout_decorator
from tenacity import retry, stop_after_attempt, wait_fixed
from ygg_rss_proxy.fspy import FlareSolverr
from ygg_rss_proxy.settings import settings
from ygg_rss_proxy.logging_config import logger
import http.cookiejar as cookielib

# Custom exceptions
class YGGLoginError(Exception):
    """Base exception for YGG login errors"""

class CloudflareBypassError(YGGLoginError):
    """Exception raised when Cloudflare bypass fails"""

class BasicLoginError(YGGLoginError):
    """Exception raised when basic login fails"""

# YGG Basic Login payload
ygg_payload = {"id": settings.ygg_user, "pass": settings.ygg_pass}
# URLs
URL_AUTH = f"{settings.ygg_url}/auth/process_login"
URL_LOGIN = f"{settings.ygg_url}/auth/login"

def ygg_basic_login(
    session: requests.Session, ygg_payload: dict = ygg_payload
) -> requests.Session:
    """
    Perform a basic login to YGG using the provided session and payload.

    Args:
        session (requests.Session): The session object to be used for the login request.
        ygg_payload (dict): The payload containing the login credentials.

    Returns:
        requests.Session: The session object with updated cookies if login is successful.

    Raises:
        BasicLoginError: If the login is unsuccessful.
    """
    logger.info("Attempting basic login to YGG")
    try:
        response = session.post(URL_AUTH, data=ygg_payload, allow_redirects=True)
        if response.status_code == 200 and "auth/login" not in response.url:
            logger.info("Successfully authenticated to YGG using basic login")
            return session
        else:
            logger.error(f"Failed to authenticate to YGG. Status code: {response.status_code}, URL: {response.url}")
            raise BasicLoginError(f"Authentication failed with status code: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Network error during basic login: {str(e)}")
        raise BasicLoginError(f"Network error during basic login: {str(e)}") from e

def ygg_cloudflare_login(
    session: requests.Session, ygg_payload: dict = ygg_payload
) -> requests.Session:
    """
    Perform a login to YGG while bypassing Cloudflare protection using FlareSolverr.

    Args:
        session (requests.Session): The session object to be used for the login request.
        ygg_payload (dict): The payload containing the login credentials.

    Returns:
        requests.Session: The session object with updated cookies and headers if login is successful.

    Raises:
        CloudflareBypassError: If Cloudflare bypass or login fails.
    """
    logger.info("Attempting Cloudflare bypass for YGG login")
    try:
        fs_solver = FlareSolverr(
            host=settings.flaresolverr_host,
            port=settings.flaresolverr_port,
            http_schema=settings.flaresolverr_shema,
            additional_headers=None,
            v="v1",
        )

        if fs_solver.version is None:
            raise CloudflareBypassError("Failed to connect to FlareSolverr")

        response = fs_solver.request_get(url="https://www.ygg.re")
        logger.debug(f"FlareSolverr response - Message: {response.message}, Status: {response.solution.status}")

        if not response.solution.cookies:
            raise CloudflareBypassError("Failed to get cookies from FlareSolverr")

        if response.message == "Challenge solved!":
            cookie_jar = cookielib.CookieJar()
            cf_clearance_found = False
            for cookie in response.solution.cookies:
                if cookie["name"] == "cf_clearance":
                    cookie_jar.set_cookie(
                        cookielib.Cookie(
                            version=0,
                            name=cookie["name"],
                            value=cookie["value"],
                            port=None,
                            port_specified=False,
                            domain=cookie["domain"],
                            domain_specified=True,
                            domain_initial_dot=True,
                            path=cookie["path"],
                            path_specified=True,
                            secure=cookie["secure"],
                            expires=cookie["expiry"],
                            discard=False,
                            comment=None,
                            comment_url=None,
                            rest={"HttpOnly": cookie["httpOnly"]},
                            rfc2109=False,
                        )
                    )
                    cf_clearance_found = True
                    break

            if not cf_clearance_found:
                logger.error("Failed to get cf_clearance from FlareSolverr")
                raise CloudflareBypassError("Failed to get cf_clearance from FlareSolverr")

            session.cookies = cookie_jar
            session.headers.update({"User-Agent": response.solution.user_agent})
            session = ygg_basic_login(session=session, ygg_payload=ygg_payload)
            logger.info("Successfully bypassed Cloudflare and logged in to YGG")
            return session
        else:
            raise CloudflareBypassError(f"Cloudflare challenge not solved: {response.solution.status}")
    except Exception as e:
        logger.error(f"Error during Cloudflare bypass: {str(e)}")
        raise CloudflareBypassError(f"Error during Cloudflare bypass: {str(e)}") from e

@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(0.3),
    retry_error_callback=lambda retry_state: YGGLoginError("Failed to connect to YGG after retries")
)
@timeout_decorator.timeout(60, exception_message="Timeout after 60 seconds")
def ygg_login(
    session=requests.Session(), ygg_payload: dict = ygg_payload
) -> requests.Session:
    """
    Perform a login to YGG, detecting if Cloudflare is enabled and using the appropriate login method.

    Args:
        session (requests.Session): The session object to be used for the login request.
        ygg_payload (dict): The payload containing the login credentials.

    Returns:
        requests.Session: The session object with updated cookies and headers if login is successful.

    Raises:
        YGGLoginError: If the login is unsuccessful or if there's a connection error.
    """
    logger.info("Initiating YGG login process")
    try:
        response = session.get(URL_LOGIN)
        if response.status_code == 403:
            logger.info("Cloudflare protection detected, using FlareSolverr for login")
            return ygg_cloudflare_login(session, ygg_payload)
        else:
            logger.info("No Cloudflare protection detected, using basic login")
            return ygg_basic_login(session, ygg_payload)
    except requests.RequestException as e:
        logger.error(f"Network error during login attempt: {str(e)}")
        raise YGGLoginError(f"Network error during login attempt: {str(e)}") from e
    except (CloudflareBypassError, BasicLoginError) as e:
        logger.error(f"Login failed: {str(e)}")
        raise YGGLoginError(f"Login failed: {str(e)}") from e

if __name__ == "__main__":
    pass