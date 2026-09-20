"""Fetch the small list of official Shopee sources used by this lab.

Checks robots.txt, spaces requests by at least one second, and keeps raw pages
outside data/. It does not log in, bypass access controls, or call private APIs.
Run: python scripts/crawl_shopee.py
"""

from __future__ import annotations

import codecs
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from fetch_public_pages import TextExtractor


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "shopee"
LOG = ROOT / "report" / "shopee_crawl_log.json"
USER_AGENT = "Day7DataFoundationsCourse/1.0 (+educational-lab)"
SOURCES = {
    "buyer-request": "https://help.shopee.vn/portal/4/article/79233",
    "buyer-evidence": "https://help.shopee.vn/portal/4/article/79467",
    "regulations": "https://help.shopee.vn/portal/4/article/77245",
    "return-policy": "https://help.shopee.vn/portal/4/article/77251",
    "disputes": "https://help.shopee.vn/portal/4/article/77265",
    "refund-help": "https://help.shopee.vn/portal/4/article/79507",
    "refund-blog": "https://shopee.vn/blog/?p=188413",
}


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    robots = {}
    events = []
    last_request = 0.0

    def fetch(url: str):
        nonlocal last_request
        time.sleep(max(0.0, 1.1 - (time.monotonic() - last_request)))
        last_request = time.monotonic()
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"})
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                codecs.lookup(charset)
            except LookupError:
                charset = "utf-8"
            return response.status, response.geturl(), raw, raw.decode(charset, errors="replace")

    for name, url in SOURCES.items():
        event = {"source_id": name, "url": url, "checked_at": datetime.now().astimezone().isoformat(), "user_agent": USER_AGENT}
        try:
            parsed = urlparse(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            if origin not in robots:
                status, _, raw, body = fetch(origin + "/robots.txt")
                parser = RobotFileParser()
                parser.parse(body.splitlines())
                robots[origin] = (parser, body)
                (CACHE / f"{parsed.netloc}-robots.txt").write_bytes(raw)
            parser, body = robots[origin]
            event["robots_url"] = origin + "/robots.txt"
            event["robots_allowed"] = parser.can_fetch(USER_AGENT, url)
            if not event["robots_allowed"]:
                event["status"] = "skipped-robots-disallow"
            else:
                status, final_url, raw, html = fetch(url)
                extractor = TextExtractor()
                extractor.feed(html)
                extractor.close()
                text = extractor.text()
                (CACHE / f"{name}.html").write_bytes(raw)
                (CACHE / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
                event.update({
                    "status": "fetched" if len(text) >= 80 else "empty-page-shell",
                    "http_status": status,
                    "final_url": final_url,
                    "title": extractor.page_title(),
                    "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "extracted_characters": len(text),
                    "raw_cache": str((CACHE / f"{name}.html").relative_to(ROOT)).replace("\\", "/"),
                })
        except Exception as error:
            event.update({"status": "fetch-failed", "error": f"{type(error).__name__}: {error}"})
        events.append(event)
        LOG.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: {event['status']} ({event.get('extracted_characters', 0)} characters)", flush=True)
    return 0 if any(event["status"] == "fetched" for event in events) else 1


if __name__ == "__main__":
    raise SystemExit(main())
