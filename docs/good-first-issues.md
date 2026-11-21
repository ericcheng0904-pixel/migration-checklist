# Good first issues

These are drafts for small issues. They have not been opened.

## Date the WordPress Tools Export screen in SOURCES.md

The sources table links the [WordPress Tools Export screen](https://wordpress.org/documentation/article/tools-export-screen/). The opening paragraph dates WooCommerce, Shopify, Adobe Commerce, BigCommerce, Squarespace, and Wix pages. It does not name that WordPress.org page.

Acceptance criteria:

- The opening paragraph or that table row states the date the page was checked, as a calendar date.
- The date is a day the page was opened for this edit. Do not guess a date.
- No other source row changes meaning.

## Add a how-to-verify clause to the WooCommerce launch-day spot-check

In CHECKLIST.md, under Launch day, the check that starts "Spot-check prices, images, variants, and stock on a handful of real products" says what goes wrong and links the WooCommerce migration guide. It does not say which columns to compare. SPOT-CHECKS.md already names WooCommerce `Sale price` and `Regular price` and Shopify `Price` and `Compare-at price`.

Acceptance criteria:

- That check gains a short how-to-verify clause for those columns, plus images and SKUs, and it still asks for one product that was on sale and one that was a draft.
- The existing source link stays, and its meaning stays the same.
- No new claim about a platform is added. If the wording of the check changes, the source links stay.

## Plant a currency symbol in one common-mistakes price

CHECKLIST.md says to keep currency symbols out of the price cells. The practice catalogs use bare numbers. None of them puts a currency symbol in a Shopify `Price` cell. `SPOON-CEDAR` in `common-mistakes` is the row that still matches, so leave it alone.

Acceptance criteria:

- One other Shopify `Price` in `test-catalogs/common-mistakes`, such as `BOWL-MOSS`, contains a currency symbol. The WooCommerce price for that SKU stays a bare number.
- `test-catalogs/README.md` names the planted case in the `common-mistakes` section. The other planted differences stay.
- `tests/test_catalogs.py` asserts the new case. `python3 scripts/make-test-catalogs.py` still writes the same bytes on a second run.
- Names and prices stay fictional. No new claim about a platform is added.
- Edit `scripts/make-test-catalogs.py`, then regenerate; do not edit the CSV files by hand.

## Add a Wix product that has options and no Variant rows

`test-catalogs/README.md` says a Product row with options and no Variant rows is one variant per option value, and then says "This file has no product like that." `wix-basic` has a product with Variant rows and two products with no options.

Acceptance criteria:

- `wix-basic` gains one fictional product with options and no Variant rows, and two option values. The 50-column header stays the same.
- The Shopify file has one row per option value, which is the mapping that README section already states, and the section says so for the new product.
- `tests/test_catalogs.py` covers the new product. A second run of `python3 scripts/make-test-catalogs.py` matches the first byte for byte.
- The store name stays Sample Harbor Goods. No real store, brand, or person.
- Edit `scripts/make-test-catalogs.py`, then regenerate; do not edit the CSV files by hand.

## Decide the WooCommerce check that has no source link

The first check under "Before you start" in CHECKLIST.md, "Freeze product edits, then take the WooCommerce product CSV you will actually import", has no Markdown link. The other checks in that file link a page, or they link one inside the sentence.

Acceptance criteria:

- The check still means: freeze product edits, and keep the export that will be imported.
- Either the line gains a documentation link that is also listed in SOURCES.md with the date that page was checked, or the line states that it is a process step.
- Do not guess a URL. No other check changes meaning.
