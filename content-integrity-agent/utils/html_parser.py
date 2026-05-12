from html.parser import HTMLParser
from typing import Dict, Optional


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.copydoc_url = None
        self.title = None
        self._in_title = False
        self._in_head = False
        self._title_parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self._in_head = True
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        if tag == "meta" and self._in_head:
            attr_dict = dict(attrs)
            if attr_dict.get("name") == "copydoc" and "content" in attr_dict:
                self.copydoc_url = attr_dict["content"]

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_parts).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)


def extract_page_meta(html: str) -> Dict[str, Optional[str]]:
    parser = _MetaParser()
    parser.feed(html)
    return {
        "copydoc_url": parser.copydoc_url,
        "title": parser.title,
    }
