import logging
from flask import Flask, request, jsonify, Response, redirect
import requests
import os
from lxml import etree

app = Flask(__name__)

USERNAME = os.getenv('YGG_USER', 'BaD')
PASSWORD = os.getenv('YGG_PASS', 'BoY')
RSS_HOST = os.getenv('RSS_HOST', 'localhost')
RSS_PORT = os.getenv('RSS_PORT', '5000')
RSS_SHEMA = os.getenv('RSS_SHEMA', 'http')
FLARESOLVERR_SHEMA = os.getenv('FLARESOLVERR_SHEMA', 'http')
FLARESOLVERR_HOST = os.getenv('FLARESOLVERR_HOST', 'localhost')
FLARESOLVERR_PORT = os.getenv('FLARESOLVERR_PORT', '8191')
YGG_URL = os.getenv('YGG_URL', 'https://www.ygg.re')
INTERNAL_PORT = os.getenv('INTERNAL_PORT', 5000 )
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

FLARESOLVERR = f'{FLARESOLVERR_SHEMA}://{FLARESOLVERR_HOST}:{FLARESOLVERR_PORT}/v1'
AUTH_URL = f'{YGG_URL}/auth/process_login'
RSS_URL = f'{YGG_URL}/rss'
TORRENT_URL = f'{YGG_URL}/rss/download'

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))

session = requests.Session()

def flaresolverr_request():
    url = FLARESOLVERR

    if requests.get(url).status_code != 405:
        logging.error('Flaresolverr is not available')

    data = {
        'cmd': 'request.get',
        'maxTimeout': 60000,
        'url': RSS_URL,
        'returnOnlyCookies': True
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        logging.info('The request with flaresolverr was successful')
        logging.debug(response.json())
        return response.json()
    else:
        logging.error(f'The request with flaresolverr failed with status code: {response.status_code}')

def auth_ygg(cloudflare):
    data = {
        'id': USERNAME,
        'pass': PASSWORD
    }

    if cloudflare:
        flaresolverr_response = flaresolverr_request()
        if flaresolverr_response is None:
            return None
        cookies = flaresolverr_response['solution']['cookies']
        user_agent = flaresolverr_response['solution']['userAgent']
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        session.headers.update({'User-Agent': user_agent})

    response = session.post(AUTH_URL, data=data)

    if response.status_code == 200:
        logging.info('The request was successful')
        return session.cookies
    else:
        logging.error(f'The request failed with status code: {response.status_code}. Please check or verify the username and password.')
        return None

def authenticate():
    response = requests.get(YGG_URL)
    if response.status_code == 403:
        logging.info('Cloudflare detected')
        return auth_ygg(cloudflare=True)
    elif response.status_code == 200:
        logging.info('No Cloudflare detected')
        return auth_ygg(cloudflare=False)
    else:
        logging.error(f'Unexpected status code: {response.status_code}')
        return None

def get_rss_feed(query_params):
    rss_url_with_params = f"{RSS_URL}?{query_params}"
    response = session.get(rss_url_with_params)
    return response

def replace_torrent_links(rss_content):
    parser = etree.XMLParser(recover=True)
    tree = etree.fromstring(rss_content, parser)

    for enclosure in tree.xpath("//item/enclosure"):
        original_url = enclosure.get('url')
        if original_url.startswith(TORRENT_URL):
            params = original_url.split('?')[1]
            new_url = f"http://{RSS_HOST}:{RSS_PORT}/torrent?{params}"
            enclosure.set('url', new_url)

    return etree.tostring(tree, encoding='utf-8', xml_declaration=True)

@app.route('/rss', methods=['GET'])
def proxy_rss():
    query_params = request.query_string.decode('utf-8')

    if not session.cookies:
        cookies = authenticate()
        if cookies is None:
            return jsonify({'error': 'Authentication failed'}), 401

    response = get_rss_feed(query_params)

    if response.status_code == 401:  # Unauthorized, session may have expired
        cookies = authenticate()
        if cookies is None:
            return jsonify({'error': 'Re-authentication failed'}), 401

        response = get_rss_feed(query_params)

    if response.status_code == 403:  # Forbidden, Cloudflare challenge
        cookies = authenticate()
        if cookies is None:
            return jsonify({'error': 'Cloudflare Re-authentication failed'}), 403

    if response.status_code == 200:
        modified_rss = replace_torrent_links(response.content)
        return Response(modified_rss, content_type='application/xml; charset=utf-8')
    else:
        return jsonify({'error': 'Failed to retrieve RSS feed'}), response.status_code

@app.route('/torrent', methods=['GET'])
def proxy_torrent():
    torrent_url = request.url.replace(f"http://{RSS_HOST}:{RSS_PORT}/torrent", TORRENT_URL)

    if not session.cookies:
        cookies = authenticate()
        if cookies is None:
            return jsonify({'error': 'Authentication failed'}), 401

    response = session.get(torrent_url)

    if response.status_code == 401:  # Unauthorized, session may have expired
        cookies = authenticate()
        if cookies is None:
            return jsonify({'error': 'Re-authentication failed'}), 401

        response = session.get(torrent_url)

    if response.status_code == 200:
        return Response(response.content, content_type='application/x-bittorrent')
    else:
        return jsonify({'error': 'Failed to retrieve torrent file'}), response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=INTERNAL_PORT)