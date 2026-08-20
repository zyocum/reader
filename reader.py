#!/usr/bin/env python3

"""Get a cleaner version of a web page for reading purposes.

This script fetches a URL (or reads local HTML) and extracts the main
content and metadata via trafilatura
(https://trafilatura.readthedocs.io/), outputting the document as JSON,
Markdown, plain-text, or HTML.
"""

import json
import re
import sys
import textwrap
from copy import deepcopy
from http.client import responses
from typing import ClassVar, NoReturn, Protocol, TypedDict

from lxml import etree
from lxml.etree import _Element  # pyright: ignore[reportPrivateUsage]
from trafilatura import bare_extraction, fetch_response

# these are the same (non-underscored) helpers trafilatura.extract()
# dispatches to when serializing its extraction result; using them
# directly lets us extract once and serialize three ways
from trafilatura.htmlprocessing import build_html_output
from trafilatura.utils import normalize_unicode
from trafilatura.xml import xmltotxt


class Content(TypedDict):
    """The extracted main content, serialized three ways"""

    html: str
    markdown: str
    text: str


class ParseResult(TypedDict):
    """Document metadata and content extracted by trafilatura"""

    title: str | None
    author: str | None
    url: str | None
    hostname: str | None
    description: str | None
    sitename: str | None
    date: str | None
    categories: list[str] | None
    tags: list[str] | None
    fingerprint: str | None
    id: str | None
    license: str | None
    language: str | None
    image: str | None
    pagetype: str | None
    filedate: str | None
    content: Content
    word_count: int


class Formatter(Protocol):
    """A named function that renders a ParseResult as output text"""

    __name__: str

    def __call__(self, obj: ParseResult, /) -> str: ...


class Format:
    """This is a decorator class for registering document format methods.

    You can register additional document formatter functions by decorating
    them with @Format.

    A formatter should be a function that takes as input a parse result
    dict.  It's output can be any string derived from that input.

    By convention formatters should have a '_format' suffix in their function
    name.  By this convention, if you have a formatter named 'json_format',
    then you can call this with Format.formatter['json']().
    """

    formatter: ClassVar[dict[str, Formatter]] = {}
    format: Formatter

    def __init__(self, f: Formatter) -> None:
        key, _ = f.__name__.rsplit("_", 1)
        self.formatter.update({key: f})
        self.format = f

    def __call__(self, obj: ParseResult) -> str:
        return self.format(obj)


@Format
def json_format(obj: ParseResult) -> str:
    """Formatter that formats as JSON"""
    return json.dumps(obj, ensure_ascii=False)


@Format
def html_format(obj: ParseResult) -> str:
    """Formatter that outputs the extracted content as HTML"""
    return obj["content"]["html"]


def metadata(obj: ParseResult) -> dict[str, str | int]:
    """The human-relevant, non-empty metadata fields of a parse result"""
    fields: dict[str, str | int | None] = {
        "title": obj["title"],
        "author": obj["author"],
        "url": obj["url"],
        "sitename": obj["sitename"],
        "date": obj["date"],
        "description": obj["description"],
        "categories": ", ".join(obj["categories"] or []),
        "tags": ", ".join(obj["tags"] or []),
        "words": obj["word_count"],
    }
    return {key: value for key, value in fields.items() if value}


@Format
def md_format(obj: ParseResult) -> str:
    """Formatter that formats as markdown with YAML front matter"""
    front_matter = "\n".join(
        (
            "---",
            # JSON scalars are valid YAML scalars, so this quoting is safe
            *(
                f"{key}: {json.dumps(value, ensure_ascii=False)}"
                for key, value in metadata(obj).items()
            ),
            "---",
        )
    )
    body = obj["content"]["markdown"]
    # supply a title heading unless the content already leads with one
    if obj["title"] and not body.lstrip().startswith("# "):
        title = (
            f"# [{obj['title']}]({obj['url']})" if obj["url"] else f"# {obj['title']}"
        )
        body = f"{title}\n\n{body}"
    return f"{front_matter}\n\n{body}"


@Format
def txt_format(obj: ParseResult) -> str:
    """Formatter that formats as plain-text with a metadata header"""
    header = "\n".join(f"{key}: {value}" for key, value in metadata(obj).items())
    return f"{header}\n\n{obj['content']['text']}"


def wrap(text: str, width: int | None, markdown: bool = False) -> str:
    """Hard-wrap each line of text at width, preserving blank lines

    In markdown mode, lines whose markup would break if split across
    lines (headings, table rows, horizontal rules, and fenced code
    blocks) are left intact.
    """
    if not width:
        return text
    lines: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if markdown and stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            lines.append(line)
        elif not stripped or (
            markdown and (in_fence or stripped.startswith(("#", "|", "---")))
        ):
            lines.append(line)
        else:
            lines.append(
                textwrap.fill(
                    line,
                    width,
                    # never split within long tokens, e.g. URLs
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
    return "\n".join(lines)


def fail(error: str, source: str) -> NoReturn:
    """Print a labeled error for source to stderr and exit"""
    print(f"[{error}] {source}", file=sys.stderr)
    sys.exit(1)


def load(source: str) -> tuple[str, str | None]:
    """Load HTML from a URL, local file, or stdin

    source: a URL (http/https), a file path, or '-' for stdin

    Returns an (html, url) tuple; url is None for local sources.
    """
    if source.startswith(("http://", "https://")):
        response = fetch_response(source, decode=True)
        if response is None:
            fail("FETCH ERROR - No response", source)
        if not 200 <= response.status < 300:
            reason = responses.get(response.status, "Unknown")
            fail(f"HTTP ERROR {response.status} - {reason}", source)
        if not response.html:
            fail("FETCH ERROR - empty response", source)
        return response.html, source
    if source == "-":
        return sys.stdin.read(), None
    try:
        with open(source, mode="r") as f:
            return f.read(), None
    except OSError as err:
        fail(f"FILE ERROR - {err.strerror}", source)


WHITESPACE = re.compile(r"\s+")

BLOCK_TAGS = {"p", "head", "list", "quote", "code", "table", "graphic"}

# lines that should stay adjacent to their neighbors (list items, table rows)
TIGHT = re.compile(r"- |\* |\||\d+\. ")


def splice(element: _Element) -> None:
    """Replace an element with its children, in place"""
    parent = element.getparent()
    if parent is None:
        return
    index = parent.index(element)
    children = list(element)
    if element.tail and children:
        last = children[-1]
        last.tail = f"{last.tail or ''}{element.tail}"
    for offset, child in enumerate(children):
        parent.insert(index + offset, child)
    parent.remove(element)


def is_layout(table: _Element) -> bool:
    """Is this (extracted) table element a layout table?

    Tables that have at most one cell or that nest block-level content
    inside a cell exist to arrange content rather than to relate it,
    and their contents read better as ordinary blocks (markdown and
    plain-text table cells can't hold block content, so it would
    otherwise be flattened onto one line).

    Note that this is necessarily heuristic: the HTML standard leaves
    layout-table detection to user-agent heuristics, and unwrapping
    ("linearizing") them is exactly what screen readers and browser
    reader modes (e.g. Readability.js's _markDataTables) do.  Operating
    on trafilatura's normalized post-extraction tree keeps the rules
    here far simpler than theirs.
    """
    cells = table.findall(".//cell")
    if len(cells) <= 1:
        return True
    return any(child.tag in BLOCK_TAGS for cell in cells for child in cell)


def unwrap_layout_tables(body: _Element) -> None:
    """Splice layout tables' contents up into their parents, in place

    Tables with no text at all (decorative image/spacer scaffolding)
    are dropped entirely; cells with inline-only content become
    paragraphs; data tables are left alone.
    """
    # reversed => document order guarantees inner tables come last, so
    # nested tables are unwrapped before their enclosing table
    for table in reversed(list(body.iter("table"))):
        if not any(text.strip() for text in table.itertext()):
            parent = table.getparent()
            if parent is not None:
                parent.remove(table)
            continue
        if not is_layout(table):
            continue
        for cell in list(table.iter("cell")):
            if any(child.tag in BLOCK_TAGS for child in cell) or not (
                cell.text and cell.text.strip()
            ):
                splice(cell)
            else:
                cell.tag = "p"
        for row in list(table.iter("row")):
            splice(row)
        splice(table)


def collapse_space(element: _Element) -> None:
    """Collapse source-formatting whitespace in an element's text nodes

    Code blocks are left untouched, since their whitespace is
    significant.
    """
    code: set[_Element] = set()
    for block in element.iter("code"):
        code.update(block.iter())
    for el in element.iter():
        if el in code:
            continue
        if el.text:
            el.text = WHITESPACE.sub(" ", el.text)
        if el.tail:
            el.tail = WHITESPACE.sub(" ", el.tail)


def markdown_text(element: _Element) -> str:
    """Serialize an extracted element as markdown"""
    element = deepcopy(element)
    collapse_space(element)
    return xmltotxt(element, include_formatting=True)


def space_blocks(text: str) -> str:
    """Separate single-line blocks with blank lines for readability

    Runs of list items and table rows are kept adjacent.
    """
    spaced: list[str] = []
    previous = ""
    for line in text.split("\n"):
        if (
            spaced
            and previous
            and line
            and not (TIGHT.match(line) and TIGHT.match(previous))
        ):
            spaced.append("")
        spaced.append(line)
        previous = line
    return "\n".join(spaced)


def plain_text(element: _Element) -> str:
    """Serialize an extracted element as plain text, sans links/images"""
    element = deepcopy(element)
    # lxml-stubs doesn't cover these two helpers, hence the ignores
    etree.strip_tags(element, "ref")  # pyright: ignore[reportAny]
    etree.strip_elements(element, "graphic", with_tail=False)  # pyright: ignore[reportAny]
    collapse_space(element)
    text = xmltotxt(element, include_formatting=False)
    return space_blocks("\n".join(line.rstrip() for line in text.split("\n")))


def main(source: str, body_width: int | None) -> ParseResult:
    """Extract a web page's content and metadata as a dict

    source: URL, HTML file path, or '-' (stdin) to fetch and parse
    body_width: int (line hard-wrap length for markdown/plain-text)

    The result dict contains trafilatura's document metadata plus the
    extracted content as HTML ('content.html'), Markdown
    ('content.markdown'), and plain-text ('content.text').
    """
    html, url = load(source)
    doc = bare_extraction(
        html,
        url=url,
        with_metadata=True,
        include_formatting=True,
        include_links=True,
        include_images=True,
    )
    if doc is None or isinstance(doc, dict):
        fail("PARSE ERROR - failed to extract content", source)
    unwrap_layout_tables(doc.body)
    unwrap_layout_tables(doc.commentsbody)
    markdown = "\n".join(
        (
            markdown_text(doc.body),
            markdown_text(doc.commentsbody),
        )
    ).strip()
    text = "\n".join(
        (
            plain_text(doc.body),
            plain_text(doc.commentsbody),
        )
    ).strip()
    # build_html_output converts doc.body in place, so it must come last
    content_html = build_html_output(doc)
    return ParseResult(
        title=doc.title,
        author=doc.author,
        url=doc.url,
        hostname=doc.hostname,
        description=doc.description,
        sitename=doc.sitename,
        date=doc.date,
        categories=doc.categories,
        tags=doc.tags,
        fingerprint=doc.fingerprint,
        id=doc.id,
        license=doc.license,
        language=doc.language,
        image=doc.image,
        pagetype=doc.pagetype,
        filedate=doc.filedate,
        content=Content(
            html=normalize_unicode(content_html),
            markdown=wrap(
                normalize_unicode(markdown),
                body_width,
                markdown=True,
            ),
            text=wrap(
                normalize_unicode(text),
                body_width,
            ),
        ),
        word_count=len(text.split()),
    )


if __name__ == "__main__":
    import argparse

    class Args(argparse.Namespace):
        source: str = ""
        format: str = "json"
        body_width: int | None = None

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=__doc__
    )
    _ = parser.add_argument(
        "source",
        help=(
            "URL to fetch and parse, or path to a local HTML file "
            '(use "-" to read HTML from stdin)'
        ),
    )
    _ = parser.add_argument(
        "-f",
        "--format",
        choices=list(Format.formatter),
        default="json",
        help="output format",
    )
    _ = parser.add_argument(
        "-w",
        "--body-width",
        type=int,
        default=None,
        help=(
            "character offset at which to hard-wrap lines of markdown "
            "and plain-text content"
        ),
    )
    args = parser.parse_args(namespace=Args())
    obj = main(
        args.source,
        args.body_width,
    )
    print(Format.formatter[args.format](obj))
