# reader
Extract clean(er), readable text from web pages via [trafilatura](https://trafilatura.readthedocs.io/).

## A note on the parser
Earlier versions of this project used the [Postlight Parser](https://github.com/postlight/parser), which required Node.js and shelling out to its command-line driver, plus [html2text](https://github.com/Alir3z4/html2text) for the Markdown/plain-text conversions. Both have been replaced by [trafilatura](https://trafilatura.readthedocs.io/), a well-maintained Python library that consistently tops content-extraction benchmarks and emits HTML, Markdown, and plain-text natively. Everything now runs in a single Python process with a single dependency.

## Install

Clone this repository and install the dependencies with [uv](https://docs.astral.sh/uv/):

```
$ uv sync
```

Or with a classic virtual environment:

```
$ python3 -m venv .venv
$ source .venv/bin/activate
(reader) $ pip install -r requirements.txt
```

## Usage

```
(reader) $ ./reader.py -h
usage: reader.py [-h] [-f {json,html,md,txt}] [-w BODY_WIDTH] source

Get a cleaner version of a web page for reading purposes. This script fetches a URL (or reads
local HTML) and extracts the main content and metadata via [trafilatura](https://trafilatura.readthedocs.io/), outputting the document as JSON, Markdown, plain-text, or
HTML.

positional arguments:
  source                URL to fetch and parse, or path to a local HTML file (use "-" to read
                        HTML from stdin)

options:
  -h, --help            show this help message and exit
  -f {json,html,md,txt}, --format {json,html,md,txt}
                        output format (default: json)
  -w BODY_WIDTH, --body-width BODY_WIDTH
                        character offset at which to hard-wrap lines of markdown and plain-text
                        content (default: None)
```

When wrapping markdown, lines whose markup would break if split across lines (headings, table rows, horizontal rules, and fenced code blocks) are left intact.

The source can be a URL (fetched by trafilatura), a local HTML file, or `-` to read HTML from stdin — so you can also feed it pages saved locally or fetched by other tools (`curl`, a headless browser, etc.).

## Examples

### Full JSON

The default output is JSON containing trafilatura's extracted metadata alongside the content in three forms: HTML (`.content.html`), Markdown (`.content.markdown`), and plain-text (`.content.text`):

```
(reader) $ ./reader.py https://www.paulgraham.com/greatwork.html | jq .
{
  "title": "How to Do Great Work",
  "author": null,
  "url": "https://www.paulgraham.com/greatwork.html",
  "hostname": "paulgraham.com",
  "description": null,
  "sitename": "paulgraham.com",
  "date": "2023-01-01",
  "categories": [],
  "tags": [],
  "fingerprint": null,
  "id": null,
  "license": null,
  "language": null,
  "image": null,
  "pagetype": null,
  "filedate": "2026-08-19",
  "content": {
    "html": "<html>...</html>",
    "markdown": "July 2023 If you collected lists of techniques for doing great work...",
    "text": "July 2023 If you collected lists of techniques for doing great work..."
  },
  "word_count": 11807
}
```

### HTML
The extracted HTML content is accessible from `.content.html`, or directly with `--format=html`:

```
(reader) $ ./reader.py https://www.paulgraham.com/greatwork.html -f html
```

### Markdown
As a convenience, the `-f/--format` option can output the whole document as Markdown, including some of the human-relevant metadata:

```
(reader) $ ./reader.py https://www.paulgraham.com/greatwork.html --format=md

date: 2023-01-01
author(s): None

# [How to Do Great Work](https://www.paulgraham.com/greatwork.html)

July 2023 If you collected lists of techniques for doing great work in a lot
of different fields, what would the intersection look like? I decided to find
out by making it.
...
```

### Plain-text
Similarly, the whole document can be formatted as plain-text:

```
(reader) $ ./reader.py https://www.paulgraham.com/greatwork.html --format=txt -w 80

url: https://www.paulgraham.com/greatwork.html
date: 2023-01-01
author(s): None

How to Do Great Work

July 2023 If you collected lists of techniques for doing great work in a lot
of different fields, what would the intersection look like? I decided to find
out by making it.
...
```

### Read Web Content in Your Terminal
One use case for this script is to convert content from the web to a format that is suitable for reading in your terminal.  Here's a short shell pipeline to extract the content and feed the converted plain-text to your `$PAGER` of choice for easy reading:

```
#!/bin/sh
# Read a web page as clean plain text in $PAGER.
# Usage: newspaper.sh <url>
set -eu

"path/to/reader.py" "$1" -w 80 -f txt | "${PAGER:-less}"
```
