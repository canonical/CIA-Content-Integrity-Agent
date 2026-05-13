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


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip_tags = {"script", "style", "head"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._parts)


def extract_visible_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()
