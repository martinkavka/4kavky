#!/usr/bin/env python3
"""Generate blog article HTML files from stary-web/blog/*.md.

Preserves source text verbatim (per user requirement). Recognizes image-reference
placeholder lines (leftover CMS artifacts) and either inserts a matching image
from assets/img/ or removes the placeholder. Output: /blog/<slug>/index.html.
"""
from __future__ import annotations
import re
import sys
import unicodedata
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from typography import fix_html as fix_typography  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "stary-web" / "blog"
OUT = ROOT / "blog"
IMG_DIR = ROOT / "assets" / "img"

MONTHS_CS = {
    1: "ledna", 2: "února", 3: "března", 4: "dubna", 5: "května", 6: "června",
    7: "července", 8: "srpna", 9: "září", 10: "října", 11: "listopadu", 12: "prosince",
}

def parse_cs_date(s: str) -> tuple[str, str]:
    """Return (short '27. 11. 2023', iso '2023-11-27')."""
    m = re.match(r"\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", s)
    if not m:
        return s.strip(), ""
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    short = f"{d}. {mo}. {y}"
    iso = f"{y:04d}-{mo:02d}-{d:02d}"
    return short, iso

def slug_from_text(t: str) -> str:
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")

# Precomputed slug → file map for photo matching
IMG_FILES = {p.stem: p.name for p in IMG_DIR.glob("*.webp")}

def match_image(line: str) -> str | None:
    """If `line` looks like a CMS image placeholder, return filename in assets/img/ or None."""
    s = line.strip()
    if not s:
        return None
    if len(s) > 80:
        return None
    # Contains sentence-ending punctuation or question marks → probably prose, not placeholder
    if any(c in s for c in ".!?,:;"):
        return None
    # Try exact slug match
    slug = slug_from_text(s)
    if not slug:
        return None
    if slug in IMG_FILES:
        return IMG_FILES[slug]
    # Try partial: placeholder is often a truncated id like BQ1A3434.
    # Require ≥8 chars so generic tokens ("Martin", "Alice") don't match.
    if len(slug) < 8:
        return None
    for stem, fname in IMG_FILES.items():
        if slug in stem or stem in slug:
            return fname
    return None

# Image-placeholder *heuristic*: short, no sentence punctuation, probably non-prose
IMG_PLACEHOLDER_PATTERN = re.compile(
    r"^[\w\- ._():šěščřžýáíéúůťďňóŠĚŠČŘŽÝÁÍÉÚŮŤĎŇÓ]+$"
)

def is_likely_image_placeholder(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    if len(s) > 60:
        return False
    if any(c in s for c in ".!?,:;"):
        return False
    # Contains digit clusters or alluppercase words typical of filenames
    if re.search(r"[A-Z]{2,}\d|\d{3,}|IMG[-_ ]\d|BQ\d", s):
        return True
    # Heuristic: "word word word" is prose; filenames tend to have underscores/hyphens
    if "_" in s:
        return True
    return False

def is_heading(s: str, next_lines: list[str]) -> bool:
    """Simple heuristic for subheadings."""
    s = s.strip()
    if not s:
        return False
    if len(s) > 80:
        return False
    if s.endswith((".", "!", "?", ",", ":", ";")):
        return False
    # Short, standalone, followed by a paragraph
    # To avoid false positives we require: no space-less filename-ish tokens
    if re.search(r"\d{3,}|IMG[-_]|BQ\d", s):
        return False
    # Sentence-looking (Upper then lower-case word) or questions are prose
    return True

HTML_HEAD = """<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title_esc} — 4 Kavky</title>
  <meta name="description" content="{desc_esc}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/css/styles.css" />
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/logo/favicon-32.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/logo/apple-touch-icon.png" />
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a class="site-logo" href="/" aria-label="4 Kavky — domů">
        <img src="/assets/logo/logo.webp" alt="4 Kavky — Rodinné deskovkářství" />
      </a>
      <button class="nav-toggle" aria-label="Otevřít menu" aria-expanded="false">☰</button>
      <nav class="site-nav" aria-label="Hlavní navigace">
        <ul>
          <li><a href="/o-nas/">O nás</a></li>
          <li><a href="/blog/" aria-current="page">Blog</a></li>
          <li><a href="https://www.youtube.com/@4kavky/videos" target="_blank" rel="noopener">Videa ↗</a></li>
          <li><a href="/dalsi-projekty/">Naše další projekty</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main>
    <section class="article-header">
      <div class="container container--narrow">
        <a class="back-link" href="/blog/">Zpět na blog</a>
        <div class="date">{date_short_esc}</div>
        <h1>{title_esc}</h1>
      </div>
    </section>

    <section style="padding-top: 0;">
      <div class="container container--narrow">
        <div class="prose">
{body}
        </div>
      </div>
    </section>

    <svg class="wave wave--paper-soft" viewBox="0 0 1200 60" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0,40 C150,10 350,70 600,35 C850,5 1050,55 1200,30 L1200,60 L0,60 Z" />
    </svg>

    <section class="section--soft">
      <div class="container container--narrow" style="text-align: center;">
        <h2>Další články</h2>
        <p style="margin-top: 24px;">
          <a href="/blog/" style="display: inline-block; padding: 14px 32px; background: var(--accent); color: var(--paper); border-radius: 999px; font-weight: 600; border-bottom: 0;">Na blog →</a>
        </p>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="footer-logo">
            <img src="/assets/logo/logo.webp" alt="4 Kavky" />
          </div>
          <p>Rodinné deskovkářství Alice a Martina Kavkových. 2020–2025.</p>
        </div>
        <nav class="footer-nav" aria-label="Rozcestník">
          <ul>
            <li><a href="/o-nas/">O nás</a></li>
            <li><a href="/blog/">Blog</a></li>
            <li><a href="https://www.youtube.com/@4kavky/videos" target="_blank" rel="noopener">Videa</a></li>
            <li><a href="/dalsi-projekty/">Naše další projekty</a></li>
          </ul>
        </nav>
      </div>
    </div>
  </footer>

  <script src="/js/main.js" defer></script>
</body>
</html>
"""

URL_RE = re.compile(r"(https?://[^\s<>\"']+)")

def starts_with_emoji(s: str) -> bool:
    s = s.lstrip()
    if not s:
        return False
    cp = ord(s[0])
    if cp >= 0x1F000:
        return True
    if 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF or 0x2300 <= cp <= 0x23FF:
        return True
    return False

def linkify(text: str) -> str:
    def sub(m):
        url = m.group(1).rstrip(".,;:!?)")
        trail = m.group(1)[len(url):]
        return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>{trail}'
    return URL_RE.sub(sub, text)

GLOSSARY_SPLIT_RE = re.compile(r"^(.{1,80}?)(\s[–—=-]\s)(.+)$")

def bolden_glossary_term(paragraph: str) -> str:
    """For dictionary entries ('Term – definition' / 'Term = Y'), bold the term."""
    m = GLOSSARY_SPLIT_RE.match(paragraph)
    if not m:
        return paragraph
    term, sep, rest = m.group(1), m.group(2), m.group(3)
    # Guard against prose that happens to contain a dash: subheadings with ':' and sentence punctuation.
    if ":" in term:
        return paragraph
    if any(c in term for c in ";!?"):
        return paragraph
    return f"<strong>{term}</strong>{sep}{rest}"

def render_body(lines: list[str], glossary_mode: bool = False) -> str:
    """Convert raw blog lines to HTML paragraphs / headings / figures.
    Rules (keep source text verbatim):
      - blank line = paragraph break
      - image-placeholder-looking lines → <figure> if matched, else skipped
      - very short standalone non-prose lines → <h2>
      - everything else → <p>
    """
    out: list[str] = []
    # split into paragraphs (blocks separated by blank lines)
    blocks: list[list[str]] = []
    current: list[str] = []
    for ln in lines:
        if ln.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(ln.rstrip())
    if current:
        blocks.append(current)

    for i, block in enumerate(blocks):
        joined = "\n".join(block).strip()
        if not joined:
            continue

        # Horizontal-rule-only block (source uses dashed lines as separators)
        if all(re.fullmatch(r"[-–—_=\s]+", l) for l in block) and any(re.search(r"[-–—_=]{5,}", l) for l in block):
            out.append('          <hr class="prose-divider" />')
            continue

        # Single-line block: candidate for image or heading
        if len(block) == 1:
            line = block[0].strip()
            # Try image match
            img = match_image(line)
            if img:
                out.append(
                    f'          <figure class="photo-card" style="display:block; margin: 2.5em auto; max-width: 560px;">\n'
                    f'            <img src="/assets/img/{img}" alt="{escape(line)}" loading="lazy" />\n'
                    f'          </figure>'
                )
                continue
            if is_likely_image_placeholder(line):
                # Probable image placeholder with no match → drop silently
                continue
            # Section heading: a single letter (alphabet marker) — clearly a heading
            if re.fullmatch(r"[A-Za-zÁ-ž]{1,2}", line):
                out.append(f"          <h2>{linkify(escape(line))}</h2>")
                continue
            # General heading heuristic: short, no dash/comma/parens/slash (dictionary entries have "–"),
            # no terminal punctuation, not starting with lowercase.
            is_heading_candidate = (
                len(line) <= 50
                and not line.endswith((".", "!", "?", ":", ";", ","))
                and not any(c in line for c in ",;/()\"„“”‚‘’")
                and not re.search(r"\s[–—-]\s", line)
                and not line.lower().startswith(("a ", "ale ", "když ", "pak ", "to ", "ten ", "taky ", "takže ", "jen ", "nebo ", "ani ", "my ", "mi ", "vy "))
                and not re.match(r"^\d", line)
                and line[:1].isupper()
            )
            if is_heading_candidate and i + 1 < len(blocks) and not glossary_mode:
                out.append(f"          <h2>{linkify(escape(line))}</h2>")
                continue
            text = linkify(escape(line))
            if glossary_mode:
                text = bolden_glossary_term(text)
            out.append(f"          <p>{text}</p>")
            continue

        # Multi-line block → paragraph with soft breaks preserved as spaces
        # Emoji-leading block → render each line as its own paragraph (no bullets, no joining)
        if len(block) >= 2 and all(starts_with_emoji(l) for l in block):
            for l in block:
                out.append(f'          <p class="emoji-line">{linkify(escape(l.strip()))}</p>')
            continue
        # Check: is it a list? (many lines, short, no terminal punct)
        looks_like_list = (
            len(block) >= 3
            and all(len(l.strip()) <= 120 for l in block)
            and sum(1 for l in block if l.strip().endswith((".", "!", "?"))) <= 1
        )
        if looks_like_list:
            out.append("          <ul>")
            for l in block:
                out.append(f"            <li>{linkify(escape(l.strip()))}</li>")
            out.append("          </ul>")
            continue

        paragraph = " ".join(l.strip() for l in block)
        text = linkify(escape(paragraph))
        if glossary_mode:
            text = bolden_glossary_term(text)
        out.append(f"          <p>{text}</p>")
    return "\n".join(out)

BRAND_FIXES = [
    (re.compile(r"Čeština2\.0"), "Čeština 2.0"),
    (re.compile(r"Párty hru čeština 2\.0"), "Párty hru Čeština 2.0"),
]

def apply_brand_fixes(text: str) -> str:
    for pat, repl in BRAND_FIXES:
        text = pat.sub(repl, text)
    return text

def build_article(md_path: Path) -> None:
    raw = apply_brand_fixes(md_path.read_text(encoding="utf-8"))
    lines = raw.splitlines()
    # drop leading empties
    while lines and lines[0].strip() == "":
        lines.pop(0)
    title = lines[0].strip() if lines else md_path.stem
    # find date (first line that looks like D.M.YYYY)
    date_line_idx = None
    for i, ln in enumerate(lines[1:8], 1):
        if re.match(r"\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\s*$", ln):
            date_line_idx = i
            break
    if date_line_idx is not None:
        date_short, date_iso = parse_cs_date(lines[date_line_idx])
        body_lines = lines[date_line_idx + 1:]
    else:
        date_short, date_iso = "", ""
        body_lines = lines[1:]

    # Drop a repeated title (some articles repeat title as first body line)
    if body_lines and body_lines[0].strip().lower() == title.lower():
        body_lines = body_lines[1:]
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    glossary_mode = md_path.stem == "deskoherni-slang"
    body_html = render_body(body_lines, glossary_mode=glossary_mode)
    # derive a short description
    desc = ""
    for ln in body_lines:
        if ln.strip() and len(ln.strip()) > 40:
            desc = ln.strip()
            break
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "…"

    slug = md_path.stem
    out_dir = OUT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    html = HTML_HEAD.format(
        title_esc=escape(title),
        desc_esc=escape(desc or title),
        date_short_esc=escape(date_short),
        body=body_html,
    )
    html = fix_typography(html)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"✓ {slug}  ({date_iso})")

def main() -> None:
    md_files = sorted(SRC.glob("*.md"))
    for f in md_files:
        build_article(f)
    print(f"\nBuilt {len(md_files)} articles → {OUT}/")

if __name__ == "__main__":
    main()
