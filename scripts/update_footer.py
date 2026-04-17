#!/usr/bin/env python3
"""One-shot rewrite of the shared footer across all HTML files.
Safe to run idempotently — matches the old footer block verbatim.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

OLD = """  <footer class=\"site-footer\">
    <div class=\"container\">
      <div class=\"footer-grid\">
        <div>
          <div class=\"footer-logo\">
            <img src=\"/assets/logo/logo.webp\" alt=\"4 Kavky\" />
          </div>
          <p style=\"margin-top: 16px; color: rgba(247, 241, 230, 0.7);\">Rodinné deskovkářství Alice a\u00a0Martina Kavkových. 2020–2025.</p>
        </div>
        <div>
          <h4>Na webu</h4>
          <ul>
            <li><a href=\"/o-nas/\">O\u00a0nás</a></li>
            <li><a href=\"/blog/\">Blog</a></li>
            <li><a href=\"https://www.youtube.com/@4kavky/videos\" target=\"_blank\" rel=\"noopener\">Videa</a></li>
            <li><a href=\"/dalsi-projekty/\">Naše další projekty</a></li>
          </ul>
        </div>
        <div>
          <h4>4\u00a0Kavky dál</h4>
          <ul>
            <li><a href=\"https://www.audioturistka.cz\" target=\"_blank\" rel=\"noopener\">Audioturistka</a></li>
            <li><a href=\"https://cestina20.cz\" target=\"_blank\" rel=\"noopener\">Čeština 2.0</a></li>
            <li><a href=\"https://www.retrohrani.cz\" target=\"_blank\" rel=\"noopener\">Retrohraní</a></li>
            <li><a href=\"https://martinkavka.cz\" target=\"_blank\" rel=\"noopener\">martinkavka.cz</a></li>
          </ul>
        </div>
      </div>
      <div class=\"footer-note\">
        © 2020–2026 4\u00a0Kavky. Web jako vzpomínka.
      </div>
    </div>
  </footer>"""

NEW = """  <footer class=\"site-footer\">
    <div class=\"container\">
      <div class=\"footer-grid\">
        <div class=\"footer-brand\">
          <div class=\"footer-logo\">
            <img src=\"/assets/logo/logo.webp\" alt=\"4 Kavky\" />
          </div>
          <p>Rodinné deskovkářství Alice a\u00a0Martina Kavkových. 2020–2025.</p>
        </div>
        <nav class=\"footer-nav\" aria-label=\"Rozcestník\">
          <ul>
            <li><a href=\"/o-nas/\">O\u00a0nás</a></li>
            <li><a href=\"/blog/\">Blog</a></li>
            <li><a href=\"https://www.youtube.com/@4kavky/videos\" target=\"_blank\" rel=\"noopener\">Videa</a></li>
            <li><a href=\"/dalsi-projekty/\">Naše další projekty</a></li>
          </ul>
        </nav>
      </div>
      <div class=\"footer-note\">© 2020–2026 Alice a\u00a0Martin Kavkovi</div>
    </div>
  </footer>"""

def main() -> None:
    files = [
        ROOT / "index.html",
        ROOT / "o-nas" / "index.html",
        ROOT / "dalsi-projekty" / "index.html",
        ROOT / "blog" / "index.html",
        *sorted((ROOT / "blog").glob("*/index.html")),
    ]
    for f in files:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        if OLD in t:
            f.write_text(t.replace(OLD, NEW), encoding="utf-8")
            print(f"✓ {f.relative_to(ROOT)}")
        elif NEW in t:
            print(f"· {f.relative_to(ROOT)} (already new)")
        else:
            print(f"! {f.relative_to(ROOT)} (footer not matched)")

if __name__ == "__main__":
    main()
