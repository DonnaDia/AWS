"""A module with page-loading time representation."""
import os

import boto3
import requests

from flask import Flask
from flask import jsonify
from flask import request


app = Flask(__name__)

PAGES_TABLE = os.environ['PAGES_TABLE']
client = boto3.client('dynamodb')


def url_load_timer(url):
    """Splits multiple urls per '&' sign and gets page-loading time in seconds
    for every url. Returns a list of urls with loading time correspondingly."""
    urls_with_time = []

    if "&" in url:
        urls = url.split("&")
    else:
        urls = url.split()

    for i in urls:
        url_with_protocol = "https://" + i
        i = f"{i}: {str(round(requests.get(url_with_protocol).elapsed.total_seconds(), 3))}s"
        urls_with_time.append(i)

    return urls_with_time


@app.route('/')
def hello():
    """Returns greeting on the home page."""
    return 'Hello, World!'


@app.route('/page_loadtime/<string:url>')
def url_load_formatter(url):
    """Returns data separated by a newline sign."""
    return "\n".join(url_load_timer(url))


@app.route('/page_loadtime_json/<page>')
def page_loadtime_json(page):
    """Returns pages along with loading time in a json like format."""
    output = []
    for i in url_load_timer(page):
        page, time = i.split(':')
        form = '{"page": "%s", \n"loading_time": "%s"}' % (page, time.strip())
        output.append(form)

    return "\n".join(output)


@app.route("/pages/<string:page>")
def get_page(page):
    """Gets page and loadtime from dynamodb."""
    resp = client.get_item(
        TableName=PAGES_TABLE,
        Key={
            'page': {'S': page}
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'Page does not exist'}), 404

    return jsonify({
        'page': item.get('page').get('S'),
        'loading_time': item.get('loading_time').get('S')
    })


@app.route("/pages", methods=["POST"])
def create_page():
    """Creates page and loadtime from dynamodb."""
    page = request.json.get('page')
    loading_time = url_load_formatter(page)
    if not page:
        return jsonify({'error': 'Please provide page'}), 400

    resp = client.put_item(
        TableName=PAGES_TABLE,
        Item={
            'page': {'S': page},
            'loading_time': {'S': loading_time}
        }
    )

    return jsonify({
        'page': page,
        'loading_time': loading_time
    })
