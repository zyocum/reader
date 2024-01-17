# reader
Extract clean(er), readable text from web pages via [Postlight Web Parser](https://github.com/postlight/parser).

## A note on the Postlight Parser
The creators of the Postlight Parser initially offered it as a free service via a ReSTful API, but have since open sourced it.  The API was shut down April 15, 2019.  To continue using the parser, install its command-line driver using [`yarn`](https://github.com/yarnpkg/yarn) or [`npm`](https://github.com/npm/cli) package managers:

```
# Install `postlight-parser` globally
yarn global add @postlight/postlight-parser
#   org
npm -g install @postlight/postlight-parser
```

## Install

Clone this repository, create a virtual environment, and install the Python requirements:

```
$ python3 -m venv .
...
$ source bin/activate
(reader) $ pip install -r requirements.txt
...
```

## Usage

```
(reader) $ ./reader.py -h
usage: reader.py [-h] [-f {json,md,txt}] [-w BODY_WIDTH] filename

Get a cleaner version of a web page for reading purposes. This script reads JSON input from the Postlight Parser
(https://github.com/postlight/parser) and performs conversion of HTML to markdown and plain-text via html2text.

positional arguments:
  filename              load postlight-parser JSON result from file (use "-" to read from stdin)

options:
  -h, --help            show this help message and exit
  -f {json,md,txt}, --format {json,md,txt}
                        output format (default: json)
  -w BODY_WIDTH, --body-width BODY_WIDTH
                        character offset at which to wrap lines for plain-text (default: None)
```

Alternatively, there is a `postlight_parser.py` script that acts just like `reader.py`, except it wraps the `postlight-parser` command line on your behalf, so instead of loading the JSON from stdin or a file, it runs the Node.js javascript internally, so all it requires is a URL:

```
(reader) $ ./postlight_parser.py -h    
usage: postlight_parser.py [-h] [-f {json,md,txt}] [-w BODY_WIDTH] [-p PARSER_PATH] url

Python wrapper of the postlight-parser command line This requires you've installed Node.js (https://nodejs.org/en/) and the postlight-parser
(https://github.com/postlight/parser): # Install postlight-parser globally $ yarn global add @postlight/parser # or $ npm -g install
@postlight/parser

positional arguments:
  url                   URL to parse

options:
  -h, --help            show this help message and exit
  -f {json,md,txt}, --format {json,md,txt}
                        output format (default: json)
  -w BODY_WIDTH, --body-width BODY_WIDTH
                        character offset at which to wrap lines for plain-text (default: None)
  -p PARSER_PATH, --parser-path PARSER_PATH
                        path to postlight-parser command line driver (default: /opt/homebrew/bin/postlight-parser)
```

If you installed `postlight-parser` somewhere other than the default path, just supply the path with the `-p/--parser-path` option.

## Examples

### Postlight Web Parser JSON

The Postlight Web Parser's raw JSON results are useful on their own:

```
(reader) $ postlight-parser https://reader.postlight.com | jq .                               
{
  "title": "Postlight Reader",
  "content": "<div><div class=\"feature\"> <div> <p> Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. </p> </div> <figure> <img alt=\"Postlight Reader settings tag\" src=\"https://reader.postlight.com/images/reader_customize_image.jpg\"> </figure>\n</div><div class=\"feature\"> <div> <p> Send beautifully formatted articles to your Kindle device with one click. </p> </div> <figure> <img alt=\"Kindle article\" src=\"https://reader.postlight.com/images/reader_kindle_image.png\"> </figure>\n</div><div class=\"galaxy\"> <div class=\"shortcut\"> <svg width=\"172\" height=\"55\"><path/><rect width=\"69\" height=\"54\"/><rect width=\"69\" height=\"54\"/></svg> <div> <p> Press <strong>Command + Esc</strong> on your keyboard to toggle the Postlight Reader view. </p> </div> </div> <p class=\"downloads\"> <a href=\"https://chrome.google.com/webstore/detail/oknpjjbmpnndlpmnhmekjpocelpnlfdi\"> Install for Chrome </a> <a href=\"https://microsoftedge.microsoft.com/addons/detail/mercury-reader/kpldbdfpngbdadafgaccakmeaoeligcl\"> Install for Edge </a> <a href=\"https://addons.mozilla.org/addon/postlight-reader/\"> Install for Firefox </a> </p> <section class=\"developers\"> <div> <p class=\"dek\">The Postlight Parser makes sense of any web page, and it&apos;s open source and available to use for free in your applications.</p> <p class=\"downloads\"> <a href=\"https://github.com/postlight/parser\">Get the Code</a> </p> </div> </section> <section class=\"users\"> <p> The Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: </p> <ul> <li> <img alt=\"Reeder\" src=\"https://reader.postlight.com/icons/reeder.png\"> Reeder </li> <li> <img alt=\"Medium\" src=\"https://reader.postlight.com/icons/medium.png\"> Medium </li> <li> <img alt=\"Apollo\" src=\"https://reader.postlight.com/icons/apollo.png\"> Apollo </li> <li> <img alt=\"Zapier\" src=\"https://reader.postlight.com/icons/zapier.png\"> Zapier </li> <li> <img alt=\"Bear\" src=\"https://reader.postlight.com/icons/bear.png\"> Bear </li> </ul> </section>\n</div></div>",
  "author": null,
  "date_published": null,
  "lead_image_url": "https://reader.postlight.com/share.png",
  "dek": null,
  "next_page_url": null,
  "url": "https://reader.postlight.com/",
  "domain": "reader.postlight.com",
  "excerpt": "Postlight Reader is a browser extension that removes ads and distractions, leaving only text and images for a beautiful reading view on any site.",
  "word_count": 112,
  "direction": "ltr",
  "total_pages": 1,
  "rendered_pages": 1
}
```

### Full JSON

`reader.py` augments the Postlight Web Parser's results with addition Markdown (`.content.mardkwon`) and plain-text (`.content.text`) conversions of the original HTML content:

```
(reader) $ postlight-parser https://reader.postlight.com | ./reader.py - | jq .
{
  "title": "Postlight Reader",
  "content": {
    "html": "<div><div class=\"feature\"> <div> <p> Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. </p> </div> <figure> <img alt=\"Postlight Reader settings tag\" src=\"https://reader.postlight.com/images/reader_customize_image.jpg\"> </figure>\n</div><div class=\"feature\"> <div> <p> Send beautifully formatted articles to your Kindle device with one click. </p> </div> <figure> <img alt=\"Kindle article\" src=\"https://reader.postlight.com/images/reader_kindle_image.png\"> </figure>\n</div><div class=\"galaxy\"> <div class=\"shortcut\"> <svg width=\"172\" height=\"55\"><path/><rect width=\"69\" height=\"54\"/><rect width=\"69\" height=\"54\"/></svg> <div> <p> Press <strong>Command + Esc</strong> on your keyboard to toggle the Postlight Reader view. </p> </div> </div> <p class=\"downloads\"> <a href=\"https://chrome.google.com/webstore/detail/oknpjjbmpnndlpmnhmekjpocelpnlfdi\"> Install for Chrome </a> <a href=\"https://microsoftedge.microsoft.com/addons/detail/mercury-reader/kpldbdfpngbdadafgaccakmeaoeligcl\"> Install for Edge </a> <a href=\"https://addons.mozilla.org/addon/postlight-reader/\"> Install for Firefox </a> </p> <section class=\"developers\"> <div> <p class=\"dek\">The Postlight Parser makes sense of any web page, and it&apos;s open source and available to use for free in your applications.</p> <p class=\"downloads\"> <a href=\"https://github.com/postlight/parser\">Get the Code</a> </p> </div> </section> <section class=\"users\"> <p> The Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: </p> <ul> <li> <img alt=\"Reeder\" src=\"https://reader.postlight.com/icons/reeder.png\"> Reeder </li> <li> <img alt=\"Medium\" src=\"https://reader.postlight.com/icons/medium.png\"> Medium </li> <li> <img alt=\"Apollo\" src=\"https://reader.postlight.com/icons/apollo.png\"> Apollo </li> <li> <img alt=\"Zapier\" src=\"https://reader.postlight.com/icons/zapier.png\"> Zapier </li> <li> <img alt=\"Bear\" src=\"https://reader.postlight.com/icons/bear.png\"> Bear </li> </ul> </section>\n</div></div>",
    "markdown": "Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. \n\n![Postlight Reader settings tag](https://reader.postlight.com/images/reader_customize_image.jpg)\n\nSend beautifully formatted articles to your Kindle device with one click. \n\n![Kindle article](https://reader.postlight.com/images/reader_kindle_image.png)\n\nPress **Command + Esc** on your keyboard to toggle the Postlight Reader view. \n\n[ Install for Chrome ](https://chrome.google.com/webstore/detail/oknpjjbmpnndlpmnhmekjpocelpnlfdi) [ Install for Edge ](https://microsoftedge.microsoft.com/addons/detail/mercury-reader/kpldbdfpngbdadafgaccakmeaoeligcl) [ Install for Firefox ](https://addons.mozilla.org/addon/postlight-reader/)\n\nThe Postlight Parser makes sense of any web page, and it's open source and available to use for free in your applications.\n\n[Get the Code](https://github.com/postlight/parser)\n\nThe Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: \n\n  * ![Reeder](https://reader.postlight.com/icons/reeder.png) Reeder \n  * ![Medium](https://reader.postlight.com/icons/medium.png) Medium \n  * ![Apollo](https://reader.postlight.com/icons/apollo.png) Apollo \n  * ![Zapier](https://reader.postlight.com/icons/zapier.png) Zapier \n  * ![Bear](https://reader.postlight.com/icons/bear.png) Bear \n\n\n",
    "text": "Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. \n\nSend beautifully formatted articles to your Kindle device with one click. \n\nPress Command + Esc on your keyboard to toggle the Postlight Reader view. \n\nInstall for Chrome  Install for Edge  Install for Firefox \n\nThe Postlight Parser makes sense of any web page, and it's open source and available to use for free in your applications.\n\nGet the Code\n\nThe Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: \n\n  * Reeder \n  * Medium \n  * Apollo \n  * Zapier \n  * Bear \n\n\n"
  },
  "author": null,
  "date_published": null,
  "lead_image_url": "https://reader.postlight.com/share.png",
  "dek": null,
  "next_page_url": null,
  "url": "https://reader.postlight.com/",
  "domain": "reader.postlight.com",
  "excerpt": "Postlight Reader is a browser extension that removes ads and distractions, leaving only text and images for a beautiful reading view on any site.",
  "word_count": 112,
  "direction": "ltr",
  "total_pages": 1,
  "rendered_pages": 1
}
```

### HTML
The original extracted HTML content from the Postlight Web Parser is accessible from `.content.html`:

```
(reader) $ postlight-parser https://reader.postlight.com | ./reader.py - | jq -r .content.html
<div><div class="feature"> <div> <p> Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. </p> </div> <figure> <img alt="Postlight Reader settings tag" src="https://reader.postlight.com/images/reader_customize_image.jpg"> </figure>
</div><div class="feature"> <div> <p> Send beautifully formatted articles to your Kindle device with one click. </p> </div> <figure> <img alt="Kindle article" src="https://reader.postlight.com/images/reader_kindle_image.png"> </figure>
</div><div class="galaxy"> <div class="shortcut"> <svg width="172" height="55"><path/><rect width="69" height="54"/><rect width="69" height="54"/></svg> <div> <p> Press <strong>Command + Esc</strong> on your keyboard to toggle the Postlight Reader view. </p> </div> </div> <p class="downloads"> <a href="https://chrome.google.com/webstore/detail/oknpjjbmpnndlpmnhmekjpocelpnlfdi"> Install for Chrome </a> <a href="https://microsoftedge.microsoft.com/addons/detail/mercury-reader/kpldbdfpngbdadafgaccakmeaoeligcl"> Install for Edge </a> <a href="https://addons.mozilla.org/addon/postlight-reader/"> Install for Firefox </a> </p> <section class="developers"> <div> <p class="dek">The Postlight Parser makes sense of any web page, and it&apos;s open source and available to use for free in your applications.</p> <p class="downloads"> <a href="https://github.com/postlight/parser">Get the Code</a> </p> </div> </section> <section class="users"> <p> The Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: </p> <ul> <li> <img alt="Reeder" src="https://reader.postlight.com/icons/reeder.png"> Reeder </li> <li> <img alt="Medium" src="https://reader.postlight.com/icons/medium.png"> Medium </li> <li> <img alt="Apollo" src="https://reader.postlight.com/icons/apollo.png"> Apollo </li> <li> <img alt="Zapier" src="https://reader.postlight.com/icons/zapier.png"> Zapier </li> <li> <img alt="Bear" src="https://reader.postlight.com/icons/bear.png"> Bear </li> </ul> </section>
</div></div>
```

### Markdown
A Markdown conversion from the HTML is added in `.content.markdown` which can be extracted just like the HTML via `jq` in the previous example.  However, as a convenience `reader.py` can output the document as Markdown (as opposed to JSON) including some of the human-relevant metadata using the `-f/--format` option:

```
(reader) $ postlight-parser https://reader.postlight.com | ./reader.py - --format=md

date: None  
author(s): None  

# [Postlight Reader](https://reader.postlight.com/)

Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. 

![Postlight Reader settings tag](https://reader.postlight.com/images/reader_customize_image.jpg)

Send beautifully formatted articles to your Kindle device with one click. 

![Kindle article](https://reader.postlight.com/images/reader_kindle_image.png)

Press **Command + Esc** on your keyboard to toggle the Postlight Reader view. 

[ Install for Chrome ](https://chrome.google.com/webstore/detail/oknpjjbmpnndlpmnhmekjpocelpnlfdi) [ Install for Edge ](https://microsoftedge.microsoft.com/addons/detail/mercury-reader/kpldbdfpngbdadafgaccakmeaoeligcl) [ Install for Firefox ](https://addons.mozilla.org/addon/postlight-reader/)

The Postlight Parser makes sense of any web page, and it's open source and available to use for free in your applications.

[Get the Code](https://github.com/postlight/parser)

The Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: 

  * ![Reeder](https://reader.postlight.com/icons/reeder.png) Reeder 
  * ![Medium](https://reader.postlight.com/icons/medium.png) Medium 
  * ![Apollo](https://reader.postlight.com/icons/apollo.png) Apollo 
  * ![Zapier](https://reader.postlight.com/icons/zapier.png) Zapier 
  * ![Bear](https://reader.postlight.com/icons/bear.png) Bear 



```
### Plain-text
Similarly to the previous example, `reader.py` can also format the whole document, along with a subset of the metadata, as plain-text:

```
(reader) $ postlight-parser https://reader.postlight.com | ./reader.py - --format=txt

url: https://reader.postlight.com/
date: None
author(s): None

Postlight Reader

Customize your Reader look and feel based on how you like to read. Change the typeface and text size, or turn on the dark theme for more comfortable reading at night. 

Send beautifully formatted articles to your Kindle device with one click. 

Press Command + Esc on your keyboard to toggle the Postlight Reader view. 

Install for Chrome  Install for Edge  Install for Firefox 

The Postlight Parser makes sense of any web page, and it's open source and available to use for free in your applications.

Get the Code

The Postlight Parser already powers technologies and publishers across the internet, serving millions of users at places like: 

  * Reeder 
  * Medium 
  * Apollo 
  * Zapier 
  * Bear 



```

### Read Web Content in Your Terminal
One use case for this script is to convert content from the web to a format that is suitable for reading in your terminal.  Here's a short shell pipeline to extract the content and feed the converted plain-text to your `$PAGER` of choice for easy reading:

```
#!/bin/bash
url=$1
reader=path/to/reader.py
postlight-parser "$url" | "$reader" - -w 80 -f txt | "$PAGER"
```
