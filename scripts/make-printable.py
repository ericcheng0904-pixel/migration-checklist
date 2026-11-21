#!/usr/bin/env python3
"""Write printable HTML pages from the checklist Markdown.

Run from anywhere:

    python3 scripts/make-printable.py
    python3 scripts/make-printable.py --check

With no argument, write docs/*.html, docs/.nojekyll, and byte-for-byte copies
of the six tracker CSV files under docs/tracker-import/. With --check, exit 1
when a generated file differs from what would be written, or is missing, and
write nothing. Text is compared as UTF-8 bytes. CSV copies are compared as
the source bytes, with no newline translation.

The converter accepts the constructs these checklist files use: headings,
paragraphs, task items, plain list items, ordered lists, blockquotes, fenced
code, links, inline code, and bold. Any other construct exits non-zero and
names the file and line. HTML is UTF-8 with LF line endings and no byte-order
mark, and the CSV copies are unchanged, so a second run matches the first
byte for byte.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# Source file, output name, title, meta description (120 to 155 characters).
PAGES = (
    (
        "CHECKLIST.md",
        "woocommerce-to-shopify.html",
        "WooCommerce to Shopify migration checklist (printable)",
        "A printable page of the WooCommerce to Shopify catalog checklist. "
        "Open it in a browser, tick the items, then print or save the page as a PDF.",
    ),
    (
        "MAGENTO.md",
        "magento-to-shopify.html",
        "Magento 2 to Shopify migration checklist (printable)",
        "A printable page of the Magento 2 to Shopify catalog checklist. "
        "Open it in a browser, tick the items, then print or save the page as a PDF.",
    ),
    (
        "BIGCOMMERCE.md",
        "bigcommerce-to-shopify.html",
        "BigCommerce to Shopify migration checklist (printable)",
        "A printable page of the BigCommerce to Shopify catalog checklist. "
        "Open it in a browser, tick the items, then print or save the page as a PDF.",
    ),
    (
        "SQUARESPACE.md",
        "squarespace-to-shopify.html",
        "Squarespace to Shopify migration checklist (printable)",
        "A printable page of the Squarespace to Shopify catalog checklist. "
        "Open it in a browser, tick the items, then print or save the page as a PDF.",
    ),
    (
        "WIX.md",
        "wix-to-shopify.html",
        "Wix to Shopify migration checklist (printable)",
        "A printable page of the Wix to Shopify catalog checklist. "
        "Open it in a browser, tick the items, then print or save the page as a PDF.",
    ),
    (
        "SPOT-CHECKS.md",
        "spot-checks.html",
        "Catalog migration spot checks (printable)",
        "Printable spot checks for counting products, variants, and SKUs in catalog "
        "exports. Open the page in a browser, then print or save it as a PDF.",
    ),
)

INDEX_TITLE = "Printable catalog migration checklists"
INDEX_DESCRIPTION = (
    "Printable pages of the WooCommerce, Magento, BigCommerce, Squarespace, and "
    "Wix checklists, with spot checks and tracker CSV files. Print or save as PDF."
)

SOURCE_PAGES = {source: target for source, target, _title, _desc in PAGES}

# The three README tool links. Copied exactly; no other outside links are added.
TOOLS = (
    (
        "Checklist guide",
        "https://catalog-signoff.pages.dev/guides/woocommerce-to-shopify-migration-checklist.html",
    ),
    (
        "Free readiness scan",
        "https://catalog-signoff.pages.dev/tools/readiness-scan.html",
    ),
    (
        "Free redirect map",
        "https://catalog-signoff.pages.dev/tools/redirect-map.html",
    ),
)

# Six tracker files, copied byte for byte into docs/tracker-import/.
TRACKER_CSVS = (
    "woocommerce.csv",
    "magento.csv",
    "bigcommerce.csv",
    "squarespace.csv",
    "wix.csv",
    "spot-checks.csv",
)

# Source checklist, the export that checklist is for, and the matching tracker CSV.
PLATFORM_EXPORTS = {
    "CHECKLIST.md": ("WooCommerce product CSV", "woocommerce.csv"),
    "MAGENTO.md": ("Magento 2 product export", "magento.csv"),
    "BIGCOMMERCE.md": ("BigCommerce product export", "bigcommerce.csv"),
    "SQUARESPACE.md": ("Squarespace product export", "squarespace.csv"),
    "WIX.md": ("Wix Stores product export", "wix.csv"),
}

# Extensionless, as published. import-check has no .html and no trailing slash.
IMPORT_CHECK_URL = "https://catalog-signoff.pages.dev/tools/import-check"
SAMPLE_REPORTS_URL = "https://catalog-signoff.pages.dev/sample/"

TASK_PREFIX = "- [ ] "
_FENCE_OPEN = re.compile(r"^```([^`]*)\s*$")
_ORDERED = re.compile(r"^(\d+)\. (.*)$")
_HEADING = re.compile(r"^(#{1,6}) (.*)$")
_HR = re.compile(r"^(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
_NESTED = re.compile(r"^[ \t]+(?:[-*+]|\d+[.)])\s+")
_TAG = re.compile(r"</?[A-Za-z][^>\n]*>|<!--|<!\[CDATA\[")
_AUTOLINK = re.compile(r"<https?://[^>\s]+>")
_IMAGE = re.compile(r"!\[[^\]]*\]")
_CODE_SPAN = re.compile(r"`[^`]*`")
_CHECKED_DATE = re.compile(
    r"(?i)(?:\bdate checked\b|\blast checked\b|\bchecked on\b)\s*:?\s*\d{4}-\d{2}-\d{2}"
)
_CHECKED_LINE = re.compile(r"(?i)\s*checked\s*:?\s*\d{4}-\d{2}-\d{2}\s*")

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
html { background: #fff; }
body {
  margin: 0 auto;
  padding: 1.25rem 1rem 2.5rem;
  max-width: 40rem;
  color: #111;
  background: #fff;
  font: 1.05rem/1.5 Georgia, "Iowan Old Style", Palatino, "Palatino Linotype", serif;
  overflow-wrap: anywhere;
}
main, footer { max-width: 100%; }
h1 { font-size: 1.55rem; line-height: 1.25; margin: 0 0 1rem; }
h2 {
  font-size: 1.2rem;
  line-height: 1.3;
  margin: 1.75rem 0 0.6rem;
  break-after: avoid;
  page-break-after: avoid;
}
p { margin: 0.65rem 0; }
a { color: inherit; text-decoration: underline; text-underline-offset: 0.12em; }
ul, ol { margin: 0.6rem 0; padding-left: 1.3rem; }
li { margin: 0.35rem 0; }
ul.checks { list-style: none; padding-left: 0; margin-left: 0; }
.check {
  display: flex;
  align-items: flex-start;
  gap: 0.5em;
  list-style: none;
  margin: 0.55rem 0;
  break-inside: avoid;
  page-break-inside: avoid;
}
.box {
  flex: 0 0 auto;
  width: 0.85em;
  height: 0.85em;
  margin-top: 0.28em;
  border: 1px solid #000;
}
.check-text { min-width: 0; }
blockquote {
  margin: 1rem 0;
  padding: 0 0 0 0.9rem;
  border-left: 3px solid #000;
}
blockquote p { margin: 0.4rem 0; }
pre, code {
  font-family: ui-monospace, "Cascadia Mono", "Segoe UI Mono", Menlo, Consolas, monospace;
}
code { font-size: 0.92em; }
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  overflow-x: auto;
  max-width: 100%;
  margin: 0.8rem 0;
  padding: 0.75rem 0.8rem;
  border: 1px solid #bbb;
}
pre code { font-size: 0.82rem; }
footer {
  margin-top: 2.5rem;
  padding-top: 1rem;
  border-top: 1px solid #000;
  font-size: 0.95rem;
}
footer ul { padding-left: 1.2rem; }
@page { margin: 16mm; }
@media print {
  html, body { color: #000; background: #fff; }
  body { padding: 0; max-width: none; }
  a { color: #000; text-decoration: underline; }
  .box { border-color: #000; }
  .nav { display: none; }
  a[href^="https://"]::after,
  a[href^="http://"]::after {
    content: " (" attr(href) ")";
    overflow-wrap: anywhere;
    word-break: break-all;
  }
}
""".strip()


class MarkdownError(Exception):
    def __init__(self, filename: str, lineno: int, detail: str) -> None:
        self.filename = filename
        self.lineno = lineno
        self.detail = detail
        super().__init__(f"{filename}:{lineno}: {detail}")


def render_inline(text: str) -> str:
    """Render inline code, bold, and links. Escape <, >, and &."""
    parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("`", i):
            end = text.find("`", i + 1)
            if end == -1:
                parts.append("`")
                i += 1
                continue
            parts.append("<code>" + html.escape(text[i + 1 : end], quote=False) + "</code>")
            i = end + 1
            continue
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end == -1:
                parts.append("**")
                i += 2
                continue
            parts.append("<strong>" + render_inline(text[i + 2 : end]) + "</strong>")
            i = end + 2
            continue
        if text[i] == "[":
            parsed = _link_at(text, i)
            if parsed is not None:
                label, dest, nxt = parsed
                rendered = render_inline(label)
                href = map_destination(dest)
                if href is None:
                    parts.append(rendered)
                else:
                    parts.append(
                        f'<a href="{html.escape(href, quote=True)}">{rendered}</a>'
                    )
                i = nxt
                continue
        j = i + 1
        while j < n and text[j] not in "`[" and not text.startswith("**", j):
            j += 1
        parts.append(html.escape(text[i:j], quote=False))
        i = j
    return "".join(parts)


def map_destination(url: str) -> str | None:
    """Return an href, or None when the link text should stand alone.

    https and http URLs keep their exact href. Links to the six source files
    become the sibling page. Any other relative link is not a link.
    """
    if url.startswith("https://") or url.startswith("http://"):
        return url
    path = url
    suffix = ""
    if "#" in path:
        path, fragment = path.split("#", 1)
        suffix = "#" + fragment
    if "?" in path:
        path, query = path.split("?", 1)
        suffix = "?" + query + suffix
    if path.startswith("./"):
        path = path[2:]
    page = SOURCE_PAGES.get(path)
    if page is None:
        return None
    return page + suffix


def render_markdown(filename: str, text: str) -> str:
    """Convert Markdown to an HTML fragment.

    On an unsupported construct, print "filename:line: ..." and exit non-zero.
    """
    try:
        return _blocks(filename, text)
    except MarkdownError as exc:
        print(f"{exc.filename}:{exc.lineno}: {exc.detail}", file=sys.stderr)
        raise SystemExit(1) from exc


def checked_phrase(text: str) -> str | None:
    """Return a checked date phrase copied from text, or None.

    The date has to be written in the source. A bare "checked" is not a date.
    """
    match = _CHECKED_DATE.search(text)
    if match:
        return match.group(0)
    for line in text.splitlines():
        if _CHECKED_LINE.fullmatch(line):
            return line.strip()
    return None


def _link_at(text: str, i: int) -> tuple[str, str, int] | None:
    if text[i] != "[":
        return None
    close = text.find("]", i + 1)
    if close == -1 or close + 1 >= len(text) or text[close + 1] != "(":
        return None
    end = text.find(")", close + 2)
    if end == -1:
        return None
    dest = text[close + 2 : end]
    if not dest or any(ch.isspace() for ch in dest):
        return None
    return text[i + 1 : close], dest, end + 1


def _mask_code(line: str) -> str:
    return _CODE_SPAN.sub("", line)


def _reject_markup(filename: str, lineno: int, line: str) -> None:
    visible = _mask_code(line)
    if _IMAGE.search(visible):
        raise MarkdownError(filename, lineno, "unsupported Markdown construct: image")
    if _TAG.search(visible) or _AUTOLINK.search(visible):
        raise MarkdownError(filename, lineno, "unsupported Markdown construct: raw HTML")


def _is_hr(line: str) -> bool:
    return _HR.fullmatch(line.strip()) is not None


def _is_table(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|")


def _is_nested(line: str) -> bool:
    return _NESTED.match(line) is not None


def _blocks(filename: str, text: str) -> str:
    lines = text.splitlines()
    parts: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("```"):
            part, i = _fence(filename, lines, i)
            parts.append(part)
            continue
        if not line.strip():
            i += 1
            continue
        if line.startswith((" ", "\t")):
            kind = "nested list" if _is_nested(line) else "unsupported indented line"
            raise MarkdownError(filename, i + 1, f"unsupported Markdown construct: {kind}")
        if _is_hr(line):
            raise MarkdownError(
                filename, i + 1, "unsupported Markdown construct: horizontal rule"
            )
        if _is_table(line):
            raise MarkdownError(filename, i + 1, "unsupported Markdown construct: table")
        if line.startswith("#"):
            parts.append(_heading(filename, i + 1, line))
            i += 1
            continue
        if line.startswith(">"):
            part, i = _blockquote(filename, lines, i)
            parts.append(part)
            continue
        if line.startswith(TASK_PREFIX):
            part, i = _tasks(filename, lines, i)
            parts.append(part)
            continue
        if line.startswith("- "):
            part, i = _plain_list(filename, lines, i)
            parts.append(part)
            continue
        if _ORDERED.match(line):
            part, i = _ordered(filename, lines, i)
            parts.append(part)
            continue
        part, i = _paragraph(filename, lines, i)
        parts.append(part)
    return "\n".join(parts)


def _heading(filename: str, lineno: int, line: str) -> str:
    match = _HEADING.match(line)
    if not match:
        raise MarkdownError(filename, lineno, "unsupported Markdown construct: heading")
    level = len(match.group(1))
    body = match.group(2)
    _reject_markup(filename, lineno, body)
    return f"<h{level}>{render_inline(body)}</h{level}>"


def _blockquote(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    paras: list[str] = []
    while i < len(lines) and lines[i].startswith(">"):
        content = lines[i][1:]
        if content.startswith(" "):
            content = content[1:]
        _reject_markup(filename, i + 1, content)
        paras.append(f"<p>{render_inline(content)}</p>")
        i += 1
    return "<blockquote>\n" + "\n".join(paras) + "\n</blockquote>", i


def _tasks(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    items: list[str] = []
    while i < len(lines) and lines[i].startswith(TASK_PREFIX):
        body = lines[i][len(TASK_PREFIX) :]
        _reject_markup(filename, i + 1, body)
        items.append(
            '<li class="check"><span class="box" aria-hidden="true"></span>'
            f'<span class="check-text">{render_inline(body)}</span></li>'
        )
        i += 1
    return '<ul class="checks">\n' + "\n".join(items) + "\n</ul>", i


def _plain_list(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    items: list[str] = []
    while i < len(lines) and lines[i].startswith("- ") and not lines[i].startswith(TASK_PREFIX):
        body = lines[i][2:]
        _reject_markup(filename, i + 1, body)
        items.append(f"<li>{render_inline(body)}</li>")
        i += 1
    return "<ul>\n" + "\n".join(items) + "\n</ul>", i


def _ordered(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    numbers: list[int] = []
    bodies: list[str] = []
    while i < len(lines):
        match = _ORDERED.match(lines[i])
        if not match:
            break
        numbers.append(int(match.group(1)))
        body = match.group(2)
        _reject_markup(filename, i + 1, body)
        bodies.append(render_inline(body))
        i += 1
    if numbers == list(range(1, len(numbers) + 1)):
        open_tag = "<ol>"
        items = [f"<li>{body}</li>" for body in bodies]
    elif numbers == list(range(numbers[0], numbers[0] + len(numbers))):
        open_tag = f'<ol start="{numbers[0]}">'
        items = [f"<li>{body}</li>" for body in bodies]
    else:
        open_tag = "<ol>"
        items = [f'<li value="{number}">{body}</li>' for number, body in zip(numbers, bodies)]
    return open_tag + "\n" + "\n".join(items) + "\n</ol>", i


def _paragraph(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    chunks: list[str] = []
    while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
        _reject_markup(filename, i + 1, lines[i])
        chunks.append(lines[i])
        i += 1
    return f"<p>{render_inline(' '.join(chunks))}</p>", i


def _starts_block(line: str) -> bool:
    if line.startswith(("```", "#", ">", "- ")):
        return True
    if _ORDERED.match(line):
        return True
    if _is_hr(line) or _is_table(line) or line.startswith((" ", "\t")):
        return True
    return False


def _fence(filename: str, lines: list[str], i: int) -> tuple[str, int]:
    match = _FENCE_OPEN.match(lines[i])
    if not match:
        raise MarkdownError(filename, i + 1, "unsupported Markdown construct: code fence")
    info = match.group(1).strip()
    if info and not re.fullmatch(r"[A-Za-z0-9_-]+", info):
        raise MarkdownError(filename, i + 1, "unsupported Markdown construct: code fence")
    content: list[str] = []
    j = i + 1
    while j < len(lines) and lines[j] != "```":
        content.append(lines[j])
        j += 1
    if j >= len(lines):
        raise MarkdownError(filename, i + 1, "unsupported Markdown construct: unclosed code fence")
    text = "\n".join(content)
    if content:
        text += "\n"
    return f"<pre><code>{html.escape(text, quote=False)}</code></pre>", j + 1


def _affiliation_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("This project is independent and is not affiliated with "):
            return line
    return None


def _readme_bits() -> tuple[str, str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    licence = None
    affiliation = None
    for line in text.splitlines():
        if line.startswith("The Markdown documents and CSV files are [CC BY 4.0]("):
            licence = line
        elif line.startswith("This project is independent and is not affiliated with "):
            affiliation = line
    if licence is None or affiliation is None:
        raise SystemExit("README.md: licence line or affiliation paragraph not found")
    for label, url in TOOLS:
        needle = f"[{label}]({url})"
        if needle not in text:
            raise SystemExit(f"README.md: missing tool link {needle}")
    return licence, affiliation


def _tools_html() -> str:
    items = [
        f'<li><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></li>'
        for label, url in TOOLS
    ]
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def footer_html(
    source_name: str | None,
    checked: str | None,
    affiliation: str,
    licence_html: str,
) -> str:
    if source_name:
        generated = (
            "Generated from <code>"
            + html.escape(source_name)
            + "</code> in this repository."
        )
    else:
        generated = "Generated from the checklist files in this repository."
    parts = [f"<p>{licence_html}</p>", f"<p>{generated}</p>"]
    if checked:
        parts.append(f"<p>{html.escape(checked)}</p>")
    parts.append(f"<p>{html.escape(affiliation)}</p>")
    parts.append(_tools_html())
    return "\n".join(parts)


def _require_lengths(title: str, description: str) -> None:
    if not title or len(title) > 70:
        raise SystemExit(f"title length out of range ({len(title)}): {title}")
    if not 120 <= len(description) <= 155:
        raise SystemExit(
            f"description length out of range ({len(description)}): {description}"
        )


def wrap_page(
    title: str,
    description: str,
    body: str,
    footer: str,
    *,
    nav: bool = False,
) -> str:
    _require_lengths(title, description)
    if body.count("<h1>") != 1 or footer.count("<h1>") != 0:
        raise SystemExit(f"expected one h1 in {title}")
    if nav:
        body = (
            '<p class="nav"><a href="index.html">All printable checklists</a></p>\n' + body
        )
    page = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n"
        f'<meta name="description" content="{html.escape(description, quote=True)}">\n'
        "<style>\n"
        f"{CSS}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        f"{body}\n"
        "</main>\n"
        "<footer>\n"
        f"{footer}\n"
        "</footer>\n"
        "</body>\n"
        "</html>\n"
    )
    for token in ("<script", "src=", "<link", "<img", "<iframe", "<form", "url(", "@import"):
        if token in page:
            raise SystemExit(f"forbidden token {token!r} in {title}")
    return page


def _check_count(source: str) -> int:
    text = (ROOT / source).read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith(TASK_PREFIX))


def _index_body() -> str:
    pages = {source: (target, title) for source, target, title, _description in PAGES}
    items: list[str] = []
    for source, (export_name, csv_name) in PLATFORM_EXPORTS.items():
        target, title = pages[source]
        label = title.removesuffix(" (printable)")
        count = _check_count(source)
        csv_href = "tracker-import/" + csv_name
        items.append(
            "<li>"
            f'<a href="{html.escape(target, quote=True)}">{html.escape(label)}</a><br>\n'
            f"{html.escape(export_name)}. The matching tracker file is "
            f'<a href="{html.escape(csv_href, quote=True)}">{html.escape(csv_href)}</a> '
            f"({count} checks)."
            "</li>"
        )
    _spot_source, spot_target, spot_title, _spot_description = next(
        page for page in PAGES if page[1] == "spot-checks.html"
    )
    spot_label = spot_title.removesuffix(" (printable)")
    csv_items = [
        "<li>"
        f'<a href="tracker-import/{html.escape(name, quote=True)}">{html.escape(name)}</a>'
        "</li>"
        for name in TRACKER_CSVS
    ]
    return (
        "<h1>Printable checklists</h1>\n"
        "<p>These are printable copies of the migration checklists in this repository, "
        "generated from the Markdown files, free to print or save as PDF from the browser. "
        "Download a file and open it in a browser, then print or save as PDF "
        "from the browser.</p>\n"
        "<h2>Checklists by source platform</h2>\n"
        "<ul>\n" + "\n".join(items) + "\n</ul>\n"
        "<h2>Spot checks and sampling worksheet</h2>\n"
        "<p>"
        f'<a href="{html.escape(spot_target, quote=True)}">{html.escape(spot_label)}</a> '
        "explains how to count products, variants and SKUs in an export. "
        "It ends with a worksheet that shows, as arithmetic on assumed examples, "
        "how likely a random sample is to contain a wrong row.</p>\n"
        "<h2>Tracker import files</h2>\n"
        "<p>The files in tracker-import/ are plain CSV with the columns Phase, Check, "
        "Details, and Source. They are generated from the checklist files and are under "
        'the same <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> '
        "licence. Most trackers and spreadsheets can import a CSV.</p>\n"
        "<ul>\n" + "\n".join(csv_items) + "\n</ul>\n"
        "<h2>Free tools</h2>\n"
        "<ul>\n"
        f'<li><a href="{html.escape(IMPORT_CHECK_URL, quote=True)}">Free import check</a>. '
        "A free tool from the same author as this checklist, for checking a Shopify "
        "product CSV before import.</li>\n"
        f'<li><a href="{html.escape(SAMPLE_REPORTS_URL, quote=True)}">Sample reports</a>. '
        "Example reports from the same author's free tools.</li>\n"
        "</ul>"
    )


def build_outputs() -> dict[Path, str | bytes]:
    for _source, (_export_name, csv_name) in PLATFORM_EXPORTS.items():
        if csv_name not in TRACKER_CSVS:
            raise SystemExit(f"tracker csv not listed: {csv_name}")
    licence_line, readme_affiliation = _readme_bits()
    licence_html = render_inline(licence_line)
    outputs: dict[Path, str | bytes] = {}
    for source, target, title, description in PAGES:
        text = (ROOT / source).read_text(encoding="utf-8")
        body = render_markdown(source, text)
        affiliation = _affiliation_line(text) or readme_affiliation
        footer = footer_html(source, checked_phrase(text), affiliation, licence_html)
        outputs[DOCS / target] = wrap_page(title, description, body, footer, nav=True)
    index_footer = footer_html(None, None, readme_affiliation, licence_html)
    outputs[DOCS / "index.html"] = wrap_page(
        INDEX_TITLE, INDEX_DESCRIPTION, _index_body(), index_footer
    )
    outputs[DOCS / ".nojekyll"] = ""
    for name in TRACKER_CSVS:
        source_csv = ROOT / "tracker-import" / name
        if not source_csv.is_file():
            raise SystemExit(f"missing tracker csv: tracker-import/{name}")
        outputs[DOCS / "tracker-import" / name] = source_csv.read_bytes()
    return outputs


def apply_outputs(outputs: dict[Path, str | bytes], check: bool) -> int:
    differed: list[Path] = []
    for path, content in outputs.items():
        data = content.encode("utf-8") if isinstance(content, str) else content
        if check:
            current = path.read_bytes() if path.is_file() else None
            if current != data:
                differed.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if differed:
        for path in differed:
            print(f"out of date: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--check"]):
        print("Usage: python3 scripts/make-printable.py [--check]", file=sys.stderr)
        return 2
    return apply_outputs(build_outputs(), check=args == ["--check"])


if __name__ == "__main__":
    sys.exit(main())
