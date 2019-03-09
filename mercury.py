#!/usr/bin/env python3

"""Python wrapper of the Mercury Parser command line

This requires you've installed Node.js 
(https://nodejs.org/en/) 
and the mercury-parser 
(https://github.com/postlight/mercury-parser):

# Install Mercury globally
$ yarn global add @postlight/mercury-parser
# or
$ npm -g install @postlight/mercury-parser

"""

import json
import sys

from reader import HTML2Text, Format, unescape, main

from Naked.toolshed.shell import muterun_js

def mercury(url, mercury_cli_path):
    """Wrap the Mercury Parser command line driver
    
    url: URL string to parse
    mercur_cli_path: path to mercury-parser command line driver
    """
    response = muterun_js(
        mercury_cli_path,
        url
    )
    if response.exitcode != 0:
        print('[ERROR] URL: {}'.format(url), file=sys.stderr)
        print('[ERROR]', response.stderr.decode('utf-8'), file=sys.stderr)
        sys.exit(response.exitcode)
    else:
        result = json.loads(response.stdout.decode('utf-8'))
        if 'error' in result:
            print('[ERROR] URL: {}'.format(url), file=sys.stderr)
            print('[ERROR]', result['messages'], file=sys.stderr)
            sys.exit(1)
        return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'url',
        help='URL to parse',
    )
    parser.add_argument(
        '-f', '--format',
        choices=list(Format.formatter),
        default='json',
        help='output format'
    )
    parser.add_argument(
        '-w', '--body-width',
        type=int,
        default=None,
        help='character offset at which to wrap lines for plain-text'
    )
    parser.add_argument(
        '-p', '--mercury-path',
        default='/usr/local/bin/mercury-parser',
        help='path to mercury-parser command line driver'
    )
    args = parser.parse_args()
    obj = main(
        mercury(args.url, args.mercury_path),
        args.body_width
    )
    print(Format.formatter[args.format](obj))
