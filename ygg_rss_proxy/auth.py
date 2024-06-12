import requests
from ygg_rss_proxy.fspy import FlareSolverr
from ygg_rss_proxy.settings import settings
from ygg_rss_proxy.logging_config import logger
import http.cookiejar as cookielib

# YGG Basic Login playload
ygg_playload = {"id": settings.ygg_user, "pass": settings.ygg_pass}
# Urls
URL_AUTH = f"{settings.ygg_url}/auth/process_login"
URL_LOGIN = f"{settings.ygg_url}/auth/login"


def ygg_basic_login(
    session: requests.Session, ygg_playload: dict = ygg_playload
) -> requests.Session:
    """
    This function performs a basic login to YGG (Your Great Great Website) using the provided session and payload.

    Parameters:
    session (requests.Session): The session object to be used for the login request.
    ygg_playload (dict): The payload containing the login credentials. Defaults to the global ygg_playload.

    Returns:
    requests.Session: The session object with the updated cookies if the login is successful.

    Raises:
    Exception: If the login is unsuccessful.
    """
    response = session.post(URL_AUTH, data=ygg_playload, allow_redirects=True)
    if response.status_code == 200 and "auth/login" not in response.url:
        logger.info("Successfully authenticated to YGG")
        return session
    else:
        logger.error(
            f"Failed to authenticate to YGG with status code : {response.status_code}"
        )
        logger.debug(f"Response content: {response.content}")
        raise Exception("Failed to authenticate to YGG")


def ygg_cloudflare_login(
    session: requests.Session, ygg_playload: dict = ygg_playload
) -> requests.Session:
    """
    This function performs a login to YGG (Your Great Great Website) using the provided session and payload,
    while handling Cloudflare protection. It uses FlareSolverr to bypass Cloudflare's anti-bot measures.

    Parameters:
    session (requests.Session): The session object to be used for the login request.
    ygg_playload (dict): The payload containing the login credentials. Defaults to the global ygg_playload.

    Returns:
    requests.Session: The session object with the updated cookies and headers if the login is successful.

    Raises:
    Exception: If the login is unsuccessful or if the connection to FlareSolverr fails.
    """

    fs_solver = FlareSolverr(
        host=settings.flaresolverr_host,
        port=settings.flaresolverr_port,
        http_schema=settings.flaresolverr_shema,
        additional_headers=None,
        v="v1",
    )

    if fs_solver.version is None:
        logger.error("Failed to connect to FlareSolverr, please check our instance")
        raise Exception("Failed to connect to FlareSolverr")

    response = fs_solver.request_get(url="https://www.ygg.re")
    logger.debug(f"FlareSolverr response: {response}")

    if not response.solution.cookies:
        logger.error("Failed to get cookies from flaresolverr")
        logger.debug(f"Response content: {response.solution}")
        raise Exception("Failed to get cookies from flaresolverr")

    if response.status == 200:
        logger.debug(f"Cloudflare cookies: {response.solution.cookies}")
        cookie_jar = cookielib.CookieJar()
        cookies = response.solution.cookies

        cf_clearance_found = False
        for cookie in cookies:
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
        # Check if cf_clearance cookie is found
        if not cf_clearance_found:
            logger.error(f"Failed to get cf_clearance from flaresolverr")
            logger.debug(f"Response cookies: {response.solution.cookies}")
            logger.debug(f"Response : {response.solution.response}")
            raise Exception("Failed to get cf_clearance from flaresolverr")

        # Update the session with the new cookies
        session.cookies = cookie_jar
        session.headers.update({"User-Agent": response.solution.user_agent})
        session = ygg_basic_login(session=session, ygg_playload=ygg_playload)
        logger.debug(f"Session cookies: {session.cookies}")
        return session
    else:
        logger.debug(f"Response : {response.solution.response}")
        logger.debug(f"Response cookie: {response.solution.cookies}")
        logger.error(
            f"Failed to authenticate to YGG with status code : {response.solution.status}"
        )
        raise Exception("Failed to authenticate to YGG")


def ygg_login(
    session=requests.Session(), ygg_playload: dict = ygg_playload
) -> requests.Session:
    """
    This function performs a login to YGG (Your Great Great Website) using the provided session and payload.
    It checks if Cloudflare is enabled and uses the appropriate login method.

    Parameters:
    session (requests.Session): The session object to be used for the login request.
    ygg_playload (dict): The payload containing the login credentials. Defaults to the global ygg_playload.

    Returns:
    requests.Session: The session object with the updated cookies and headers if the login is successful.

    Raises:
    Exception: If the login is unsuccessful or if the connection to FlareSolverr fails.
    """
    # Check if Cloudflare is enabled
    if session.get(URL_LOGIN).status_code == 403:
        logger.info("Cloudflare is enabled, using FlareSolverr")
        return ygg_cloudflare_login(session, ygg_playload)
    else:
        logger.info("Cloudflare is disabled, using basic login")
        return ygg_basic_login(session, ygg_playload)


if __name__ == "__main__":
    pass
