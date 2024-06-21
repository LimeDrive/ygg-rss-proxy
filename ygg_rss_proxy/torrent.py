from typing import Any
from lxml import etree
from ygg_rss_proxy.settings import settings
import requests
import timeout_decorator

URL_DWL: str = f"{settings.ygg_url}/rss/download"


@timeout_decorator.timeout(60, exception_message=f"Timeout after 60 seconds")
def dwl_torrent(
    query_params: str, requests_session: requests.Session
) -> requests.Response:
    rss_url_with_params = f"{URL_DWL}?{query_params}"
    response = requests_session.get(rss_url_with_params)
    return response
