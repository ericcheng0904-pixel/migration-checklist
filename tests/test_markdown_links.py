#!/usr/bin/env python3
"""Offline tests for Markdown link checks, retries, and known redirects."""

from __future__ import annotations

import tempfile
import shutil
import contextlib
import importlib.util
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_markdown_links.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_markdown_links", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_markdown_links"] = module
    spec.loader.exec_module(module)
    return module


mod = load_checker()


class LinkCheckerTests(unittest.TestCase):
    def test_known_redirects_file_parses(self) -> None:
        allowed = mod.load_known_redirects(ROOT / "scripts" / "known-redirects.txt")
        self.assertIsInstance(allowed, dict)
        for (source, target), checked in allowed.items():
            self.assertTrue(source.startswith("http"))
            self.assertTrue(target.startswith("http"))
            self.assertRegex(checked, r"^\d{4}-\d{2}-\d{2}$")

    def test_known_redirects_rejects_a_bad_line(self) -> None:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "bad-redirects.txt"
        path.write_text("https://old.example.test https://new.example.test not-a-date\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            mod.load_known_redirects(path)

    def test_parse_hops_reads_status_and_location(self) -> None:
        blob = (
            "HTTP/2 302 \n"
            "location: https://csvkit.readthedocs.io/en/latest/\n"
            "\n"
            "HTTP/2 200 \n"
            "content-type: text/html\n"
        )
        self.assertEqual(
            mod.parse_hops(blob),
            (("302", "https://csvkit.readthedocs.io/en/latest/"), ("200", "")),
        )

    def test_local_directory_is_accepted_and_escapes_are_not(self) -> None:
        readme = ROOT / "README.md"
        self.assertIsNone(mod.classify_local(readme, "test-catalogs/small-clean"))
        self.assertIsNone(mod.classify_local(readme, "CHECKLIST.md"))
        self.assertIsNotNone(mod.classify_local(readme, "test-catalogs/missing-pair"))
        self.assertIsNotNone(mod.classify_local(readme, "../outside-the-repo"))

    def test_permanent_redirect_uses_the_allow_list(self) -> None:
        fetched = mod.FetchResult(
            "200",
            "https://help.shopify.com/en/manual/moved",
            "redirects=1",
            (("301", "https://help.shopify.com/en/manual/moved"), ("200", "")),
        )
        raw = "https://help.shopify.com/en/manual/old"
        blocked = mod.judge(
            where=f"CHECKLIST.md -> {raw}",
            raw=raw,
            fetched=fetched,
            names={raw: "Old page"},
            allowed={},
        )
        self.assertEqual(blocked.kind, "failure")
        self.assertIn("Old page", blocked.message)
        self.assertIn("official link moved", blocked.message)
        allowed = {(raw, "https://help.shopify.com/en/manual/moved"): "2026-10-25"}
        documented = mod.judge(
            where=f"CHECKLIST.md -> {raw}",
            raw=raw,
            fetched=fetched,
            names={raw: "Old page"},
            allowed=allowed,
        )
        self.assertEqual(documented.kind, "ok")
        self.assertIn("2026-10-25", documented.documented_redirect)

    def test_official_307_to_a_hub_page_fails(self) -> None:
        raw = "https://help.shopify.com/en/manual/this-page-does-not-exist-xyz"
        fetched = mod.FetchResult(
            "200",
            "https://help.shopify.com/en",
            "redirects=1",
            (("307", "https://help.shopify.com/en"), ("200", "")),
        )
        verdict = mod.judge(
            where=f"SOURCES.md -> {raw}",
            raw=raw,
            fetched=fetched,
            names={raw: "Retired page"},
            allowed={},
        )
        self.assertEqual(verdict.kind, "failure")
        self.assertIn("official link moved", verdict.message)
        self.assertIn("Retired page", verdict.message)
        self.assertIn("https://help.shopify.com/en", verdict.message)

    def test_signoff_308_is_a_warning(self) -> None:
        raw = "https://catalog-signoff.pages.dev/tools/readiness-scan.html"
        fetched = mod.FetchResult(
            "200",
            "https://catalog-signoff.pages.dev/tools/readiness-scan",
            "redirects=1",
            (("308", raw.replace(".html", "")), ("200", "")),
        )
        verdict = mod.judge(
            where=f"README.md -> {raw}",
            raw=raw,
            fetched=fetched,
            names={},
            allowed={},
        )
        self.assertEqual(verdict.kind, "warning")
        self.assertIn("redirect", verdict.message)
        self.assertIn("readiness-scan", verdict.message)

    def test_unlisted_permanent_redirect_fails(self) -> None:
        raw = "https://example.test/old"
        fetched = mod.FetchResult(
            "200",
            "https://example.test/new",
            "redirects=1",
            (("301", "https://example.test/new"), ("200", "")),
        )
        verdict = mod.judge(
            where=f"SPOT-CHECKS.md -> {raw}",
            raw=raw,
            fetched=fetched,
            names={},
            allowed={},
        )
        self.assertEqual(verdict.kind, "failure")
        self.assertIn("permanent redirect", verdict.message)
        self.assertIn("known-redirects.txt", verdict.message)

    def test_temporary_redirect_is_not_a_failure(self) -> None:
        fetched = mod.FetchResult(
            "200",
            "https://csvkit.readthedocs.io/en/latest",
            "redirects=1",
            (("302", "https://csvkit.readthedocs.io/en/latest/"), ("200", "")),
        )
        verdict = mod.judge(
            where="SPOT-CHECKS.md -> https://csvkit.readthedocs.io/",
            raw="https://csvkit.readthedocs.io/",
            fetched=fetched,
            names={},
            allowed={},
        )
        self.assertEqual(verdict.kind, "ok")
        self.assertIn("302", verdict.redirect)

    def test_official_404_is_reported_by_name_and_signoff_is_a_warning(self) -> None:
        names = mod.official_names()
        target, name = next(iter(names.items()))

        def fake_official(url: str) -> mod.FetchResult:
            key = mod.normalize(urldefrag(url)[0])
            if key == target:
                return mod.FetchResult("404", url, "missing")
            return mod.FetchResult("200", url, "redirects=0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = mod.run(fetch_fn=fake_official, allowed={})
        text = output.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("Official links that returned 404:", text)
        self.assertIn(name, text)

        def fake_signoff(url: str) -> mod.FetchResult:
            host = (urlparse(url).hostname or "").lower()
            if host == mod.SIGNOFF_HOST:
                return mod.FetchResult("404", url, "missing")
            return mod.FetchResult("200", url, "redirects=0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = mod.run(fetch_fn=fake_signoff, allowed={})
        text = output.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("Warnings:", text)
        self.assertIn("/tools/readiness-scan.html", text)
        self.assertNotIn("Official links that returned 404:", text)

    def test_failing_urls_are_retried_once_and_successes_are_not(self) -> None:
        calls = {"n": 0}

        def fail_then_ok(url: str) -> mod.FetchResult:
            calls["n"] += 1
            if calls["n"] == 1:
                return mod.FetchResult("404", url, "missing")
            return mod.FetchResult("200", url, "redirects=0")

        with contextlib.redirect_stdout(io.StringIO()):
            result = mod.fetch_with_one_retry("https://example.test/once", fail_then_ok)
        self.assertEqual(result.status, "200")
        self.assertEqual(calls["n"], 2)

        calls["n"] = 0

        def always_fail(url: str) -> mod.FetchResult:
            calls["n"] += 1
            return mod.FetchResult("404", url, "missing")

        with contextlib.redirect_stdout(io.StringIO()):
            result = mod.fetch_with_one_retry("https://example.test/twice", always_fail)
        self.assertEqual(result.status, "404")
        self.assertEqual(calls["n"], 2)

        calls["n"] = 0

        def always_ok(url: str) -> mod.FetchResult:
            calls["n"] += 1
            return mod.FetchResult("200", url, "redirects=0")

        with contextlib.redirect_stdout(io.StringIO()):
            mod.fetch_with_one_retry("https://example.test/ok", always_ok)
        self.assertEqual(calls["n"], 1)

    def test_transient_statuses_make_two_curl_calls(self) -> None:
        for status in ("404", "403", "500", "0"):
            with self.subTest(status=status):
                calls = {"n": 0}

                def fake_curl(url: str, status: str = status) -> mod.FetchResult:
                    calls["n"] += 1
                    return mod.FetchResult(status, url, "missing")

                with mock.patch.object(mod, "curl_fetch", fake_curl), mock.patch.object(
                    mod.time, "sleep", side_effect=AssertionError("sleep")
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        result = mod.fetch_with_one_retry("https://example.test/flaky")
                self.assertEqual(result.status, status)
                self.assertEqual(calls["n"], 2)

    def test_cloudflare_challenge_keeps_the_longer_loop(self) -> None:
        calls = {"n": 0}

        def fake_curl(url: str) -> mod.FetchResult:
            calls["n"] += 1
            return mod.FetchResult("200", url, mod.CHALLENGE)

        with mock.patch.object(mod, "curl_fetch", fake_curl), mock.patch.object(mod.time, "sleep"):
            with contextlib.redirect_stdout(io.StringIO()):
                result = mod.fetch_with_one_retry("https://example.test/challenge")
        self.assertEqual(result.status, "403")
        self.assertEqual(calls["n"], 7)

    def test_bot_challenge_classification_on_synthetic_responses(self) -> None:
        page = "<html><head><title>{}</title></head><body>{}</body></html>"
        challenges = (
            ("403", page.format("Verifying your connection...", "")),
            ("403", page.format("Just a moment...", "")),
            ("503", page.format("Just a moment...", "")),
            ("503", page.format("Attention", '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1?ray=1" data-cf-chl-opt>')),
            ("403", page.format("Access", "<div id='cf-chl-widget'></div>")),
            ("403", page.format("access", "JUST A MOMENT while we check your browser")),
        )
        for status, body in challenges:
            with self.subTest(status=status, body=body[:60]):
                self.assertTrue(mod.is_bot_challenge(status, body))
        not_challenges = (
            ("403", page.format("403 Forbidden", "You do not have access.")),
            ("503", page.format("Service Unavailable", "Back soon.")),
            ("404", page.format("Just a moment...", "")),
            ("200", page.format("Verifying your connection...", "")),
            ("500", page.format("Just a moment...", "")),
            ("0", ""),
        )
        for status, body in not_challenges:
            with self.subTest(status=status, body=body[:60]):
                self.assertFalse(mod.is_bot_challenge(status, body))

    def test_curl_fetch_flags_a_challenge_from_a_synthetic_curl_response(self) -> None:
        def fake_curl(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            accepts = [cmd[i + 1] for i, part in enumerate(cmd) if part == "-H" and cmd[i + 1].startswith("Accept:")]
            self.assertEqual(len(accepts), 1)
            self.assertLess(accepts[0].find("text/csv"), accepts[0].find("text/html"))
            Path(cmd[cmd.index("-D") + 1]).write_text("HTTP/2 403 \r\ncontent-type: text/html\r\n\r\n")
            Path(cmd[cmd.index("-o") + 1]).write_text(
                "<html><head><title>Just a moment...</title></head><body>cf-chl</body></html>"
            )
            return subprocess.CompletedProcess(cmd, 0, stdout=b"403\thttps://example.test/page\t0", stderr=b"")

        self.addCleanup(mod._last_request_end.clear)
        with mock.patch.object(mod.subprocess, "run", fake_curl), mock.patch.object(mod.time, "sleep"):
            result = mod.curl_fetch("https://example.test/page")
        self.assertEqual(result.status, "403")
        self.assertTrue(result.challenge)
        self.assertEqual(result.note, "Just a moment...")

        def fake_forbidden(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            Path(cmd[cmd.index("-D") + 1]).write_text("HTTP/2 403 \r\n\r\n")
            Path(cmd[cmd.index("-o") + 1]).write_text("<title>403 Forbidden</title>")
            return subprocess.CompletedProcess(cmd, 0, stdout=b"403\thttps://example.test/page\t0", stderr=b"")

        with mock.patch.object(mod.subprocess, "run", fake_forbidden), mock.patch.object(mod.time, "sleep"):
            result = mod.curl_fetch("https://example.test/page")
        self.assertEqual(result.status, "403")
        self.assertFalse(result.challenge)

    def test_bot_challenge_is_a_warning_with_the_url(self) -> None:
        raw = "https://help.shopify.com/en/manual/products/import"
        challenged = mod.FetchResult("403", raw, "Just a moment...", challenge=True)
        verdict = mod.judge(
            where=f"CHECKLIST.md -> {raw}",
            raw=raw,
            fetched=challenged,
            names={raw: "Product CSV"},
            allowed={},
        )
        self.assertEqual(verdict.kind, "warning")
        self.assertIn("could not verify (bot challenge)", verdict.message)
        self.assertIn(raw, verdict.message)
        self.assertIn("Product CSV", verdict.message)
        self.assertEqual(verdict.official_404_name, "")

        plain = mod.judge(
            where=f"CHECKLIST.md -> {raw}",
            raw=raw,
            fetched=mod.FetchResult("403", raw, "403 Forbidden"),
            names={raw: "Product CSV"},
            allowed={},
        )
        self.assertEqual(plain.kind, "failure")

    def test_persistent_challenge_keeps_the_longer_loop_and_stays_flagged(self) -> None:
        calls = {"n": 0}

        def fake_curl(url: str) -> mod.FetchResult:
            calls["n"] += 1
            return mod.FetchResult("403", url, "Just a moment...", challenge=True)

        with mock.patch.object(mod, "curl_fetch", fake_curl), mock.patch.object(mod.time, "sleep"):
            with contextlib.redirect_stdout(io.StringIO()):
                result = mod.fetch_with_one_retry("https://example.test/challenge")
        self.assertEqual(result.status, "403")
        self.assertTrue(result.challenge)
        self.assertEqual(calls["n"], 7)

        calls["n"] = 0

        def clears_on_third_try(url: str) -> mod.FetchResult:
            calls["n"] += 1
            if calls["n"] < 3:
                return mod.FetchResult("403", url, "Just a moment...", challenge=True)
            return mod.FetchResult("200", url, "redirects=0")

        with mock.patch.object(mod, "curl_fetch", clears_on_third_try), mock.patch.object(mod.time, "sleep"):
            with contextlib.redirect_stdout(io.StringIO()):
                result = mod.fetch_with_one_retry("https://example.test/clears")
        self.assertEqual(result.status, "200")
        self.assertEqual(calls["n"], 3)

    def test_run_reports_challenged_links_as_warnings_once_per_url(self) -> None:
        challenged_host = "help.shopify.com"
        rows = [
            raw
            for _path, _label, raw in mod.markdown_links()
            if raw.startswith("http") and (urlparse(raw).hostname or "") == challenged_host
        ]
        self.assertGreater(len(rows), len({mod.normalize(urldefrag(raw)[0]) for raw in rows}))

        def fake(url: str) -> mod.FetchResult:
            if (urlparse(url).hostname or "") == challenged_host:
                return mod.FetchResult("403", url, "Just a moment...", challenge=True)
            return mod.FetchResult("200", url, "redirects=0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = mod.run(fetch_fn=fake, allowed={})
        text = output.getvalue()
        self.assertEqual(code, 0, text)
        self.assertNotIn("Failures:", text)
        self.assertIn("Warnings:", text)
        self.assertIn("could not verify (bot challenge)", text)
        distinct = {mod.normalize(urldefrag(raw)[0]) for raw in rows}
        warned = [line for line in text.splitlines() if "could not verify (bot challenge)" in line]
        self.assertEqual(len(warned), len(distinct))
        self.assertIn(f"Warnings: {len(distinct)}.", text)

    def test_a_failing_url_used_in_several_places_is_listed_once_with_a_count(self) -> None:
        counts: dict[str, int] = {}
        for _path, _label, raw in mod.markdown_links():
            if raw.startswith("http"):
                key = mod.normalize(urldefrag(raw)[0])
                counts[key] = counts.get(key, 0) + 1
        target, uses = max(counts.items(), key=lambda item: item[1])
        self.assertGreater(uses, 1)

        def fake(url: str) -> mod.FetchResult:
            if mod.normalize(urldefrag(url)[0]) == target:
                return mod.FetchResult("500", url, "server error")
            return mod.FetchResult("200", url, "redirects=0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = mod.run(fetch_fn=fake, allowed={})
        text = output.getvalue()
        self.assertEqual(code, 1)
        lines = [line for line in text.splitlines() if line.startswith("  500 ")]
        self.assertEqual(len(lines), 1, text)
        self.assertIn(f"(and {uses - 1} more", lines[0])
        self.assertIn("Failed. 1 failure(s).", text)

    def test_requests_to_the_same_host_are_spaced_out(self) -> None:
        self.assertGreaterEqual(mod.HOST_DELAY, 0.5)
        self.assertLessEqual(mod.HOST_DELAY, 1.0)
        clock = {"now": 100.0}
        sleeps: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleeps.append(seconds)
            clock["now"] += seconds

        def fake_once(url: str) -> mod.FetchResult:
            clock["now"] += 0.2
            return mod.FetchResult("200", url, "redirects=0")

        self.addCleanup(mod._last_request_end.clear)
        mod._last_request_end.clear()
        with mock.patch.object(mod, "_curl_once", fake_once), mock.patch.object(
            mod.time, "sleep", fake_sleep
        ), mock.patch.object(mod.time, "monotonic", lambda: clock["now"]):
            mod.curl_fetch("https://a.example.test/one")
            self.assertEqual(sleeps, [])
            mod.curl_fetch("https://a.example.test/two")
            self.assertEqual(len(sleeps), 1)
            self.assertAlmostEqual(sleeps[0], mod.HOST_DELAY, places=6)
            mod.curl_fetch("https://b.example.test/one")
            self.assertEqual(len(sleeps), 1)
            clock["now"] += 5
            mod.curl_fetch("https://a.example.test/three")
            self.assertEqual(len(sleeps), 1)

    def test_offline_tree_accepts_local_links_when_fetches_succeed(self) -> None:
        def fake(url: str) -> mod.FetchResult:
            return mod.FetchResult("200", url, "redirects=0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = mod.run(fetch_fn=fake, allowed={})
        text = output.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("official docs returned 200 at their own URL", text)


if __name__ == "__main__":
    unittest.main()
