from typing import Any
from lxml import etree
from ygg_rss_proxy.settings import settings
import requests
import timeout_decorator

# URLs
URL_RSS: str = f"{settings.ygg_url}/rss"
URL_TORRENTS: str = f"{settings.ygg_url}/rss/download"
URL_PROXY = f"{settings.rss_shema}://{settings.rss_host}:{settings.rss_port}"


@timeout_decorator.timeout(30, exception_message=f"Timeout after 30 seconds")
def get_rss_feed(query_params, requests_session: requests.Session) -> requests.Response:
    rss_url_with_params = f"{URL_RSS}?{query_params}"
    response = requests_session.get(rss_url_with_params)
    return response


@timeout_decorator.timeout(30, exception_message=f"Timeout after 30 seconds")
def replace_torrent_links(rss_content) -> Any:
    parser = etree.XMLParser(recover=True)
    tree = etree.fromstring(rss_content, parser)

    for enclosure in tree.xpath("//item/enclosure"):
        original_url = enclosure.get("url")
        if original_url.startswith(URL_TORRENTS):
            params = original_url.split("?")[1]
            new_url = f"{URL_PROXY}/torrent?{params}"
            enclosure.set("url", new_url)

    return etree.tostring(tree, encoding="utf-8", xml_declaration=True)
