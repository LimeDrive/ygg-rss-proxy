from typing import Any
from lxml import etree
from ygg_rss_proxy.settings import settings
import requests
import timeout_decorator
from ygg_rss_proxy.logging_config import logger

# Custom exceptions
class RSSProcessingError(Exception):
    """Base exception for RSS processing errors"""

class RSSFetchError(RSSProcessingError):
    """Exception raised when fetching RSS feed fails"""

class RSSParsingError(RSSProcessingError):
    """Exception raised when parsing RSS content fails"""

# URLs
URL_RSS: str = f"{settings.ygg_url}/rss"
URL_TORRENTS: str = f"{settings.ygg_url}/rss/download"
URL_PROXY = f"{settings.rss_shema}://{settings.rss_host}:{settings.rss_port}"

@timeout_decorator.timeout(30, exception_message="Timeout after 30 seconds")
def get_rss_feed(query_params: str, requests_session: requests.Session) -> requests.Response:
    """
    Fetch RSS feed from YGG.

    Args:
        query_params (str): Query parameters for the RSS feed.
        requests_session (requests.Session): Session object for making requests.

    Returns:
        requests.Response: Response object containing the RSS feed.

    Raises:
        RSSFetchError: If there's an error fetching the RSS feed.
        TimeoutError: If the request times out.
    """
    rss_url_with_params = f"{URL_RSS}?{query_params}"
    logger.info(f"Fetching RSS feed from: {rss_url_with_params}")
    
    try:
        response = requests_session.get(rss_url_with_params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logger.info(f"Successfully fetched RSS feed. Status code: {response.status_code}")
        return response
    except requests.RequestException as e:
        logger.error(f"Error fetching RSS feed: {str(e)}")
        raise RSSFetchError(f"Failed to fetch RSS feed: {str(e)}") from e

@timeout_decorator.timeout(30, exception_message="Timeout after 30 seconds")
def replace_torrent_links(rss_content: bytes) -> bytes:
    """
    Replace torrent links in the RSS content.

    Args:
        rss_content (bytes): Raw RSS content.

    Returns:
        bytes: Modified RSS content with replaced torrent links.

    Raises:
        RSSParsingError: If there's an error parsing the RSS content.
        TimeoutError: If the processing times out.
    """
    logger.info("Starting to replace torrent links in RSS content")
    
    try:
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(rss_content, parser)
        
        link_count = 0
        for enclosure in tree.xpath("//item/enclosure"):
            original_url = enclosure.get("url")
            if original_url.startswith(URL_TORRENTS):
                params = original_url.split("?")[1]
                new_url = f"{URL_PROXY}/torrent?{params}"
                enclosure.set("url", new_url)
                link_count += 1
        
        logger.info(f"Replaced {link_count} torrent links in RSS feed")
        return etree.tostring(tree, encoding="utf-8", xml_declaration=True)
    except etree.XMLSyntaxError as e:
        logger.error(f"XML parsing error: {str(e)}")
        raise RSSParsingError(f"Failed to parse RSS content: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while replacing torrent links: {str(e)}")
        raise RSSParsingError(f"Unexpected error while processing RSS content: {str(e)}") from e