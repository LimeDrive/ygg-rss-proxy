from flask import Flask, request, jsonify, Response, redirect
import requests
import os
from lxml import etree

app = Flask(__name__)


USERNAME = os.getenv('YGG_USER')
PASSWORD = os.getenv('YGG_PASS')
LOCAL_RSS_HOST= os.getenv('LOCAL_RSS_HOST')
LOCAL_RSS_PORT= os.getenv('LOCAL_RSS_PORT')

AUTH_URL = 'https://www.ygg.re/auth/process_login'
RSS_URL = 'https://www.ygg.re/rss'
TORRENT_URL = 'https://www.ygg.re/rss/download'

session = requests.Session()

def authenticate():
    auth_data = {
        'id': USERNAME,
        'pass': PASSWORD
    }
    response = session.post(AUTH_URL, data=auth_data)
    if response.status_code == 200:
        return response.cookies
    else:
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
            new_url = f"http://{LOCAL_RSS_HOST}:{LOCAL_RSS_HOST}/torrent?{params}"
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

    if response.status_code == 200:
        modified_rss = replace_torrent_links(response.content)
        return Response(modified_rss, content_type='application/xml; charset=utf-8')
    else:
        return jsonify({'error': 'Failed to retrieve RSS feed'}), response.status_code

@app.route('/torrent', methods=['GET'])
def proxy_torrent():
    torrent_url = request.url.replace(f"http://{LOCAL_RSS_HOST}:{LOCAL_RSS_HOST}/torrent", TORRENT_URL)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
