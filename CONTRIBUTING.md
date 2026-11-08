# Contributing

Corrections are welcome. Open a pull request.

If you change a factual claim about Shopify, WooCommerce, Magento, BigCommerce, Squarespace, or Wix, link the official page you checked and write the date in [SOURCES.md](SOURCES.md). If the docs disagree, or you are not sure, say to check the current docs rather than guess.

Do not add real stores, brands, people, affiliate links, or tracking. Examples stay fictional. This project is independent and is not affiliated with Shopify or WooCommerce. It is not affiliated with Adobe or Magento. It is not affiliated with BigCommerce. It is not affiliated with Squarespace. It is not affiliated with Wix.

From the repository root:

```bash
sh scripts/check.sh
```

You can still run the pieces on their own:

```bash
python3 scripts/make-test-catalogs.py
python3 -m unittest
python3 scripts/check_markdown_links.py
```

## Checks

`sh scripts/check.sh` runs the unit tests and checks Markdown links.

The link checker tries a failed fetch once more. A Cloudflare "verifying your connection" page can be tried a few more times. Requests to the same host are spaced out by under a second. An official link that redirects to a URL not listed in `scripts/known-redirects.txt` fails. A page that answers with a bot challenge (HTTP 403 or 503 with a Cloudflare challenge) cannot be checked from a script, so it is a warning, "could not verify (bot challenge)", and not a failure; open that link in a browser. A problem on `catalog-signoff.pages.dev`, including a redirect, is a warning too. A URL that is used in several files is listed once, with the number of other places.
