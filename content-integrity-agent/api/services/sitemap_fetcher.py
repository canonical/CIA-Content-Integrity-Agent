import xml.etree.ElementTree as ET
from typing import List, Dict, Optional


class SitemapFetcher:
    MAX_DEPTH = 3
    MAX_URLS = 10000

    def __init__(self, http_client):
        self.http = http_client

    def fetch_urls(self, sitemap_url: str, depth: int = 0) -> List[Dict[str, Optional[str]]]:
        if depth > self.MAX_DEPTH:
            return []

        try:
            xml_text = self.http.get(sitemap_url)
        except Exception:
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = self._detect_namespace(root)
        urls = []

        sitemap_elements = root.findall(f"{ns}sitemap")
        if sitemap_elements:
            for sitemap_el in sitemap_elements:
                loc_el = sitemap_el.find(f"{ns}loc")
                if loc_el is not None and loc_el.text:
                    child_urls = self.fetch_urls(loc_el.text.strip(), depth + 1)
                    urls.extend(child_urls)
                    if len(urls) >= self.MAX_URLS:
                        return urls[: self.MAX_URLS]
        else:
            for url_el in root.findall(f"{ns}url"):
                loc_el = url_el.find(f"{ns}loc")
                lastmod_el = url_el.find(f"{ns}lastmod")
                if loc_el is not None and loc_el.text:
                    urls.append({
                        "url": loc_el.text.strip(),
                        "lastmod": lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None,
                    })
                    if len(urls) >= self.MAX_URLS:
                        return urls

        return urls

    def _detect_namespace(self, root: ET.Element) -> str:
        tag = root.tag
        if tag.startswith("{"):
            ns_end = tag.index("}") + 1
            return tag[:ns_end]
        return ""