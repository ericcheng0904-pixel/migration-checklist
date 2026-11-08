#!/usr/bin/env python3
"""Check Markdown links in this repository.

Official documentation links are the URLs listed in SOURCES.md. They must
return HTTP 200 at their own URL. Any redirect of an official link, and any
permanent redirect of another link, must be listed in
scripts/known-redirects.txt. Other redirects are printed.

A failing external URL is fetched once more. The longer Cloudflare retry
loop runs only while the page says it is verifying the connection.
A bot challenge (HTTP 403 or 503 with a Cloudflare challenge page) does not
show that the link is dead, so it is a warning, "could not verify (bot
challenge)", and does not fail the run. A problem on the
catalog-signoff.pages.dev host, including a redirect, is also a warning. An
official link that returns 404 is reported by the name used in SOURCES.md.
Each URL is reported once, with the number of other places that use it.
Requests to the same host are spaced out by a short delay.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
SIGNOFF_HOST = "catalog-signoff.pages.dev"
CHALLENGE = "Verifying your connection"
CHALLENGE_STATUSES = {"403", "503"}
CHALLENGE_MARKERS = ("verifying your connection", "just a moment", "cf-chl")
CHALLENGE_WARNING = "could not verify (bot challenge)"
DEFINITIVE = {"400", "401", "404", "405", "410", "451"}
HOST_DELAY = 0.75
BODY_LIMIT = 200_000
REDIRECTS_PATH = ROOT / "scripts" / "known-redirects.txt"


@dataclass(frozen=True)
class FetchResult:
    status: str
    final_url: str
    note: str
    hops: tuple[tuple[str, str], ...] = ()
    challenge: bool = False


def is_bot_challenge(status: str, body: str) -> bool:
    """True for an HTTP 403 or 503 whose body is a Cloudflare challenge page."""
    if status not in CHALLENGE_STATUSES:
        return False
    lowered = body.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


@dataclass(frozen=True)
class Verdict:
    kind: str
    message: str = ""
    redirect: str = ""
    documented_redirect: str = ""
    official_404_name: str = ""


def normalize(url: str) -> str:
    url, _fragment = urldefrag(url.strip())
    return url.rstrip("/")


def official_names() -> dict[str, str]:
    text = (ROOT / "SOURCES.md").read_text(encoding="utf-8")
    names: dict[str, str] = {}
    for match in LINK.finditer(text):
        label, raw = match.group(1), match.group(2)
        url, _fragment = urldefrag(raw)
        if url.startswith("http"):
            names.setdefault(normalize(url), label.strip())
    return names


def markdown_links() -> list[tuple[Path, str, str]]:
    rows = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            rows.append((path, match.group(1), match.group(2)))
    return rows


def load_known_redirects(path: Path) -> dict[tuple[str, str], str]:
    """Map (from-url, to-url) to the date checked. Both URLs are normalized."""
    if not path.is_file():
        raise SystemExit(f"missing known redirects file: {path}")
    found: dict[tuple[str, str], str] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 3:
            raise SystemExit(f"{path}:{lineno}: expected from-url to-url YYYY-MM-DD")
        source, target, checked = parts
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked):
            raise SystemExit(f"{path}:{lineno}: date must be YYYY-MM-DD")
        found[(normalize(source), normalize(target))] = checked
    return found


def parse_hops(header_blob: str) -> tuple[tuple[str, str], ...]:
    hops: list[tuple[str, str]] = []
    status = ""
    location = ""
    saw = False
    for line in header_blob.splitlines():
        if line.startswith("HTTP/"):
            if saw:
                hops.append((status, location))
            parts = line.split()
            status = parts[1] if len(parts) > 1 else ""
            location = ""
            saw = True
            continue
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
    if saw:
        hops.append((status, location))
    return tuple(hops)


def is_signoff(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    return host == SIGNOFF_HOST


def classify_local(markdown: Path, url: str) -> str | None:
    """Return an error, or None when url is a file or directory inside the repo."""
    local = (markdown.parent / url).resolve()
    try:
        local.relative_to(ROOT.resolve())
    except ValueError:
        return "link points outside the repository"
    if local.is_file() or local.is_dir():
        return None
    return "missing file"


def judge(
    *,
    where: str,
    raw: str,
    fetched: FetchResult,
    names: dict[str, str],
    allowed: dict[tuple[str, str], str],
) -> Verdict:
    url, _fragment = urldefrag(raw)
    key = normalize(url)
    name = names.get(key, "")
    label = f"{name} — " if name else ""
    final_key = normalize(fetched.final_url)
    if fetched.challenge:
        return Verdict("warning", f"{CHALLENGE_WARNING} {label}{where}")
    if fetched.status != "200":
        message = f"{fetched.status} {label}{where} ({fetched.note})"
        if is_signoff(url):
            return Verdict("warning", message)
        official_404_name = name if fetched.status == "404" and name else ""
        return Verdict("failure", message, official_404_name=official_404_name)

    if final_key == key:
        return Verdict("ok")

    hop_codes = [code for code, _location in fetched.hops if code and code != "200"]
    hop = ",".join(hop_codes) if hop_codes else "redirect"
    pair = (key, final_key)
    if is_signoff(url):
        message = f"redirect {label}{where} => {fetched.final_url} ({hop})"
        return Verdict("warning", message)
    if name or any(code in {"301", "308"} for code in hop_codes):
        if pair in allowed:
            note = f"{key} -> {fetched.final_url} (documented {allowed[pair]})"
            return Verdict("ok", documented_redirect=note)
        if name:
            message = f"official link moved {label}{where} => {fetched.final_url}"
            return Verdict("failure", message)
        message = (
            f"permanent redirect {label}{where} => {fetched.final_url} "
            "(not in scripts/known-redirects.txt)"
        )
        return Verdict("failure", message)
    return Verdict("ok", redirect=f"{key} -> {fetched.final_url} ({hop})")


_last_request_end: dict[str, float] = {}


def _host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower().rstrip(".")


def wait_for_host(url: str) -> None:
    """Sleep so that requests to one host start at least HOST_DELAY apart from the last one's end."""
    ended = _last_request_end.get(_host_of(url))
    if ended is None:
        return
    remaining = HOST_DELAY - (time.monotonic() - ended)
    if remaining > 0:
        time.sleep(remaining)


def curl_fetch(url: str) -> FetchResult:
    wait_for_host(url)
    try:
        return _curl_once(url)
    finally:
        _last_request_end[_host_of(url)] = time.monotonic()


def _curl_once(url: str) -> FetchResult:
    with tempfile.TemporaryDirectory() as tmp:
        body_path = Path(tmp) / "body"
        header_path = Path(tmp) / "headers"
        completed = subprocess.run(
            [
                "curl",
                "-sS",
                "-L",
                "--http2",
                "--compressed",
                "--max-redirs",
                "5",
                "--max-time",
                "30",
                "-A",
                UA,
                "-H",
                # text/csv is first so the Wix product template, which is a
                # file download, returns the CSV. Preferring text/html makes
                # that URL answer 302 to a sign-in page.
                "Accept: text/csv,text/html;q=0.9,application/xhtml+xml;q=0.8,application/xml;q=0.8,*/*;q=0.7",
                "-H",
                "Accept-Language: en-US,en;q=0.9",
                "-H",
                "Referer: https://help.shopify.com/",
                "-D",
                str(header_path),
                "-o",
                str(body_path),
                "-w",
                "%{http_code}\t%{url_effective}\t%{num_redirects}",
                url,
            ],
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            err = completed.stderr.decode("utf-8", "replace").strip()[:200]
            return FetchResult("0", url, err or "no response")
        parts = completed.stdout.decode("utf-8", "replace").strip().split("\t")
        status = parts[0] if parts else "0"
        final = parts[1] if len(parts) > 1 else url
        redirects = parts[2] if len(parts) > 2 else "0"
        header_blob = header_path.read_text(encoding="utf-8", errors="replace") if header_path.exists() else ""
        body = ""
        if body_path.exists():
            with body_path.open("rb") as handle:
                body = handle.read(BODY_LIMIT).decode("utf-8", "replace")
        title_match = re.search(r"<title>([^<]+)", body, re.I)
        title = title_match.group(1).strip() if title_match else ""
        note = f"redirects={redirects}"
        if status != "200" or CHALLENGE in title:
            note = title or note
        return FetchResult(
            status,
            final,
            note,
            parse_hops(header_blob),
            challenge=is_bot_challenge(status, body),
        )


def fetch(url: str, attempts: int = 6) -> FetchResult:
    """Fetch one URL.

    attempts applies only while Cloudflare is verifying the connection.
    A definitive status, or any other non-200, returns after the current try.
    A challenge that does not clear is returned with challenge=True.
    """
    last = FetchResult("0", url, "no response")
    for attempt in range(attempts):
        if attempt:
            time.sleep(min(2 ** attempt, 16))
        last = curl_fetch(url)
        verifying = last.challenge or CHALLENGE in last.note
        if last.status == "200" and not verifying:
            return last
        if last.status in DEFINITIVE or not verifying:
            return last
    if last.status == "200":
        return FetchResult("403", last.final_url, last.note, last.hops, challenge=True)
    return last


def fetch_with_one_retry(url: str, fetch_fn=None) -> FetchResult:
    """Fetch url, and try once more when the first result is not HTTP 200."""
    if fetch_fn is None:
        result = fetch(url)
        if result.status == "200":
            return result
        print(f"retry {url}", flush=True)
        return fetch(url, attempts=1)
    result = fetch_fn(url)
    if result.status == "200":
        return result
    print(f"retry {url}", flush=True)
    return fetch_fn(url)


class Report:
    """Messages keyed by URL. The first place is shown; later ones are counted."""

    def __init__(self) -> None:
        self._first: dict[str, str] = {}
        self._more: dict[str, int] = {}

    def add(self, key: str, message: str) -> None:
        if key in self._first:
            self._more[key] += 1
        else:
            self._first[key] = message
            self._more[key] = 0

    def lines(self) -> list[str]:
        rows = []
        for key, message in self._first.items():
            more = self._more[key]
            if more:
                message += f" (and {more} more {'place' if more == 1 else 'places'})"
            rows.append(message)
        return rows

    def __len__(self) -> int:
        return len(self._first)


def run(fetch_fn=None, allowed: dict[tuple[str, str], str] | None = None) -> int:
    fetch_fn = fetch_fn or fetch_with_one_retry
    if allowed is None:
        allowed = load_known_redirects(REDIRECTS_PATH)
    names = official_names()
    failures = Report()
    warnings = Report()
    redirects: list[str] = []
    documented: list[str] = []
    official_404s: list[str] = []
    seen_404_names: set[str] = set()
    seen: dict[str, FetchResult] = {}

    for path, _label, raw in markdown_links():
        url, _fragment = urldefrag(raw)
        if not url or url.startswith("#") or url.startswith("mailto:"):
            continue
        where = f"{path.relative_to(ROOT)} -> {raw}"
        if url.startswith("http://") or url.startswith("https://"):
            key = normalize(url)
            if key not in seen:
                print(f"check {key}", flush=True)
                seen[key] = fetch_fn(url)
            verdict = judge(where=where, raw=raw, fetched=seen[key], names=names, allowed=allowed)
            if verdict.official_404_name and verdict.official_404_name not in seen_404_names:
                seen_404_names.add(verdict.official_404_name)
                official_404s.append(verdict.official_404_name)
            if verdict.documented_redirect and verdict.documented_redirect not in documented:
                documented.append(verdict.documented_redirect)
            elif verdict.redirect and verdict.redirect not in redirects:
                redirects.append(verdict.redirect)
            if verdict.kind == "warning":
                warnings.add(key, verdict.message)
            elif verdict.kind == "failure":
                failures.add(key, verdict.message)
            continue
        local_error = classify_local(path, url)
        if local_error:
            failures.add(where, f"{local_error} {where}")

    print()
    if documented:
        print("Documented redirects:")
        for line in documented:
            print(f"  {line}")
    if redirects:
        print("Redirects:")
        for line in redirects:
            print(f"  {line}")
    if warnings:
        print("Warnings:")
        for line in warnings.lines():
            print(f"  {line}")
    if official_404s:
        print("Official links that returned 404:")
        for name in official_404s:
            print(f"  {name}")
    if failures:
        print("Failures:")
        for line in failures.lines():
            print(f"  {line}")
        print(f"Failed. {len(failures)} failure(s). {len(seen)} web links checked.")
        return 1
    print(
        f"OK. {len(seen)} web links checked, official docs returned 200 at their own URL. "
        f"Warnings: {len(warnings)}."
    )
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
