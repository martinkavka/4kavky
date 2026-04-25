# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Static memorial site for the (now closed) Czech family board-game publisher **4 Kavky**. Plain HTML/CSS/JS — no build step, no framework, no tracking. Deployed on Cloudflare Pages at www.4kavky.cz. Brand is always **4 Kavky** (never just "Kavky"). Product spelled **Čeština 2.0** (with space).

Source of truth for blog content lives in `stary-web/blog/*.md` — rendered pages in `/blog/<slug>/index.html` are generated artifacts.

## Commands

```bash
# Regenerate all blog articles from stary-web/blog/*.md
python3 scripts/build_blog.py

# Apply Czech typography (em→en dash, nbsp after single-letter prepositions
# and digits) to the hardcoded file list inside the script: index.html,
# o-nas/, dalsi-projekty/, blog/ index + all blog articles. Idempotent.
python3 scripts/typography.py

# Local preview (anything that serves the directory works)
python3 -m http.server 8000
```

There is no test suite, no linter, no package manager, no `node_modules`.

## Architecture

**Pages are hand-authored HTML**, except blog articles which are generated. Each page includes the same `<header>` and `<footer>` inline (no templating engine). When the shared chrome needs to change across the site, add a one-shot sweep script under `scripts/` — follow the pattern in `update_footer.py`: define OLD and NEW strings verbatim, iterate the same file list as `typography.py`, match-and-replace. Note: `update_footer.py` itself is already spent (its OLD string no longer exists in files).

**`scripts/build_blog.py`** reads each `stary-web/blog/*.md`, preserves the text verbatim (explicit user requirement), handles leftover CMS image-placeholder lines via `match_image()` (exact-slug first, then partial match with `len(slug) ≥ 8` guard so generic tokens like "Martin" don't match `martin-slova.webp`), detects emoji-leading paragraphs (Unicode ≥0x1F000 plus a few symbol blocks) and renders them as `<p class="emoji-line">` — not `<ul><li>`. Special case: `deskoherni-slang` runs in `glossary_mode` (bold terms, heading heuristic disabled). Runs `typography.fix_html` before writing. Output URL pattern is `/blog/<slug>/`.

**`stary-web/`** contains the original Shoptet content used as migration source: `blog/*.md` (authoritative blog text), `fotky/`, and a few `.md` files (`homepage.md`, `o-nas.md`, `nase-dalsi-projekty-odkazy.md`) that were reference for hand-authored pages.

**`scripts/typography.py`** splits HTML on tags, applies nbsp only to text content, and is safe to run repeatedly. Any Python edit that writes Czech text back to disk should be followed by running this script. `NBSP_LETTERS = "aiouvszkAIOUVSZK"`.

**`css/styles.css`** is a single file built around design tokens (`--paper`, `--paper-soft`, `--ink`, `--accent`, `--moss`, font-stack tokens). Warm paper palette with Fraunces (variable) headings and Inter body. Visual primitives: polaroid-style `.photo-card` (sits straight; `.photo-card--right` variant kept in HTML but currently styled identically — no rotation per user preference), SVG wave dividers between sections (`.wave--paper-soft` / `.wave--paper`), `.prose` container for long-form text. Don't introduce a framework — extend the tokens and existing primitives.

## Working with existing content

Most HTML text already contains nbsp bytes (`\u00a0`) inserted by `typography.py`. The `Edit` tool's exact-string matching will fail if you search for plain spaces where the file has nbsp. Options:
- Read the file first and copy the exact bytes.
- Use a small Python block: `t.replace(old_with_nbsp, new)` — more reliable for multi-replace passes.
- After any text change, run `python3 scripts/typography.py` so new text picks up the same treatment.

En-dash (`–`) everywhere, em-dash never. Apostrophes and quotes: Czech conventions.

## What to avoid

- Don't add a build step, bundler, framework, or dependency manager.
- Don't add analytics, cookies, forms, or any tracking.
- Don't rename `/blog/<slug>/` URLs — they're linked from elsewhere.
- Don't alter blog article prose when regenerating; the MD source is authoritative and text is meant to stay verbatim.
