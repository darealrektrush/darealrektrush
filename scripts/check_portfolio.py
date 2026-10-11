"""Offline checks for public portfolio navigation and SVG assets."""

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_REPOS = {
    "crabstar_oracle", "project-q-", "crabstar-universe",
    "shadow-smart-money-engine", "crabstar-web", "rektrush-os",
    "oracle-revenue-operations",
}


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.urls.append(value)


def check():
    failures = []
    references = 0
    documents = sorted(ROOT.rglob("*.md"))
    for document in documents:
        if ".git" in document.parts:
            continue
        content = document.read_text(encoding="utf-8")
        # Fenced examples and inline code are not rendered navigation.
        content = re.sub(r"^(```|~~~).*?^\1[^\n]*$", "", content,
                         flags=re.MULTILINE | re.DOTALL)
        content = re.sub(r"`[^`\n]+`", "", content)
        parser = References()
        parser.feed(content)
        urls = parser.urls + re.findall(r"!?\[[^\]\n]*\]\(([^\s)]+)\)", content)
        for url in urls:
            references += 1
            parsed = urlsplit(url)
            if parsed.hostname and parsed.hostname.lower() == "github.com":
                segments = [unquote(part).lower() for part in parsed.path.split("/") if part]
                if len(segments) >= 2 and segments[0] == "darealrektrush" and segments[1] in PRIVATE_REPOS:
                    failures.append(f"{document.relative_to(ROOT)}: private implementation link")
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                failures.append(f"{document.relative_to(ROOT)}: missing or escaping target {url}")
    assets = sorted((ROOT / "assets").rglob("*.svg"))
    for asset in assets:
        try:
            ET.parse(asset)
        except ET.ParseError as error:
            failures.append(f"{asset.relative_to(ROOT)}: invalid SVG: {error}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Portfolio checks passed: {len(documents)} Markdown files, "
          f"{references} references, {len(assets)} SVG assets.")
    print("External availability and Markdown fragments are not checked.")


if __name__ == "__main__":
    check()
