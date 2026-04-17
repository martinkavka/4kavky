#!/usr/bin/env python3
"""Czech typography fixes applied to HTML text content.
- em-dash (—) → en-dash (–)
- non-breaking space after single-letter Czech prepositions (a i o u v s z k / K S V Z)
Only touches text between tags; tags and attributes are left alone.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NBSP = "\u00a0"
NBSP_LETTERS = "aiouvszkAIOUVSZK"
# (start-of-text or non-word/non-&) + single letter OR digit + space(s) + non-space
NBSP_RE = re.compile(rf"(^|[^&\w\u00a0])([{NBSP_LETTERS}0-9]) +(?=\S)")

def fix_dashes(text: str) -> str:
    return text.replace("\u2014", "\u2013")

def add_nbsp(text: str) -> str:
    return NBSP_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}{NBSP}", text)

def fix_text(text: str) -> str:
    text = fix_dashes(text)
    # Run nbsp twice — a single pass may miss overlapping matches like "a i".
    text = add_nbsp(text)
    text = add_nbsp(text)
    return text

TAG_SPLIT_RE = re.compile(r"(<[^>]*>)")

def fix_html(html: str) -> str:
    # em-dash is safe to replace globally (never appears in tag/attr syntax)
    html = fix_dashes(html)
    # nbsp only in text content between tags
    parts = TAG_SPLIT_RE.split(html)
    return "".join(p if p.startswith("<") else add_nbsp(add_nbsp(p)) for p in parts)

def main() -> None:
    targets = [
        ROOT / "index.html",
        ROOT / "o-nas" / "index.html",
        ROOT / "dalsi-projekty" / "index.html",
        ROOT / "blog" / "index.html",
        *sorted((ROOT / "blog").glob("*/index.html")),
    ]
    for path in targets:
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        fixed = fix_html(original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8")
            print(f"✓ {path.relative_to(ROOT)}")
        else:
            print(f"· {path.relative_to(ROOT)} (no change)")

if __name__ == "__main__":
    main()
