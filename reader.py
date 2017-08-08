#!/usr/bin/env python3

"""Get a cleaner version of a web page for reading purposes.

This script uses the Mercury API to perform content extraction and html2text 
for cleaning/conversion.
"""

import os
import sys
import requests
import argparse
import json

from html import unescape
from html2text import HTML2Text
from getpass import getpass

MERCURY_API = 'https://mercury.postlight.com/parser'

def handle(response):
    """Convenience method to throw away bad responses"""
    if response.status_code == 200: # success
        return response.json()
    else:
        message = 'HTTP status {} ({}): {}'.format(
            response.status_code,
            response.reason,
            response.url
        )
        print(message, file=sys.stderr)
        sys.exit(1)

def main(url, api_key, body_width):
    """Convert Mercury API HTML content to Markdown and plain-text
    
    url: a URL whose content should be extracted and converted
    api_key: Mercury API key (https://mercury.postlight.com/web-parser/)
    """
    response = handle(
        requests.get(
            MERCURY_API,
            params={'url': url},
            headers={'Content-Type': 'application/json', 'x-api-key': api_key}
        )
    )
    text = HTML2Text()
    text.body_width = body_width
    text.ignore_emphasis = True
    text.ignore_images = True
    text.ignore_links = True
    markdown = HTML2Text()
    markdown.body_width = body_width
    response['content'] = {
        'html': response['content'],
        'markdown': unescape(markdown.handle(response['content'])),
        'text': unescape(text.handle(response['content']))
    }
    print(json.dumps(response, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'url',
        help='a URL to process',
    )
    parser.add_argument(
        '-k', '--api-key',
        default=None,
        help='a Mercury API key'
    )
    parser.add_argument(
        '-w', '--body-width',
        type=int,
        default=None,
        help='character offset at which to wrap lines for plain-text'
    )
    args = parser.parse_args()
    api_key = (
        args.api_key or
        os.environ.get('MERCURY_API_KEY') or
        getpass('Mercury API key:')
    )
    main(args.url, api_key, args.body_width)
