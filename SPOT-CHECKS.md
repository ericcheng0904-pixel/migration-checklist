# Spot checks

These checks answer two questions: how many products and variants are in each file, and which SKUs are in one file but not the other. They are not a full comparison. Do them on a copy of the export, and import the SKU column as text so a spreadsheet does not drop a leading zero while you look.

Examples below use `test-catalogs/common-mistakes/`. The variable parent SKU `TOTE` is in the WooCommerce file and not in the Shopify file. That is expected. The missing variant is `TOTE-L`.

## Spreadsheet

1. Open both CSVs. Do not let the sheet convert SKUs to numbers.
2. On the WooCommerce sheet, pivot `Type`. Count `simple` and `variation` as sellable rows. Do not count `variable` parents as variants.
3. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL. That is the variant count. Count distinct `URL handle` values. That is the product count. A row with a handle and no SKU is an extra image, not a variant.
4. `XLOOKUP` or `VLOOKUP` the WooCommerce `SKU` against the Shopify `SKU`, then the other way. Sort the misses.
5. For a SKU that exists in both, compare WooCommerce `Sale price` and `Regular price` with Shopify `Price` and `Compare-at price`.
6. Sort SKUs and look for a short number next to a matching code that still has its leading zero.

On `common-mistakes`, the sellable WooCommerce SKUs that are absent from Shopify are `01482` and `TOTE-L`. The Shopify SKU that is absent from WooCommerce is `1482`. `SOAP-PINE` and `OIL-PINE` both come back, and they share one handle, so a SKU lookup alone will not show that mistake. Filter the Shopify sheet for duplicate `URL handle` values where `Title` is filled in.

## Python

The standard library is enough. From the repository root:

```bash
python3 - << 'PY'
import csv
from collections import Counter

def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

woo = load("test-catalogs/common-mistakes/woocommerce.csv")
shop = load("test-catalogs/common-mistakes/shopify.csv")

print("WooCommerce types", Counter(row["Type"] for row in woo))
woo_skus = {row["SKU"] for row in woo if row["Type"] != "variable" and row["SKU"]}
shop_skus = {row["SKU"] for row in shop if row["SKU"]}
handles = {row["URL handle"] for row in shop if row["URL handle"]}
print("sellable WooCommerce SKUs", len(woo_skus))
print("Shopify SKUs", len(shop_skus))
print("Shopify products", len(handles))
print("only in WooCommerce", sorted(woo_skus - shop_skus))
print("only in Shopify", sorted(shop_skus - woo_skus))
PY
```

That prints:

```text
WooCommerce types Counter({'simple': 7, 'variation': 3, 'variable': 1})
sellable WooCommerce SKUs 10
Shopify SKUs 9
Shopify products 7
only in WooCommerce ['01482', 'TOTE-L']
only in Shopify ['1482']
```

`small-clean` has 4 sellable WooCommerce SKUs, 4 Shopify SKUs, and 5 Shopify rows because the mug has a second image row. The SKU sets are equal. `variable-products` has 2 + 4 + 16 variations in WooCommerce and 2 + 3 + 8 SKUs in Shopify.

## csvkit

[csvkit](https://csvkit.readthedocs.io/) is optional. The same counts, with the variable parent still included in the WooCommerce SKU list:

```bash
csvcut -c Type test-catalogs/common-mistakes/woocommerce.csv | tail -n +2 | sort | uniq -c
csvcut -c SKU test-catalogs/common-mistakes/woocommerce.csv | tail -n +2 | sed '/^$/d' | sort > /tmp/woo-skus.txt
csvcut -c SKU test-catalogs/common-mistakes/shopify.csv | tail -n +2 | sed '/^$/d' | sort > /tmp/shop-skus.txt
comm -23 /tmp/woo-skus.txt /tmp/shop-skus.txt
comm -13 /tmp/woo-skus.txt /tmp/shop-skus.txt
```

`comm -23` prints SKUs only in the WooCommerce file (`01482`, `TOTE`, `TOTE-L`). `comm -13` prints SKUs only in the Shopify file (`1482`). Drop `TOTE` by hand, or exclude variable parents before `csvcut`:

```bash
csvgrep -c Type -r '^(simple|variation)$' test-catalogs/common-mistakes/woocommerce.csv \
  | csvcut -c SKU | tail -n +2 | sort > /tmp/woo-skus.txt
```

## Magento 2

`test-catalogs/magento-basic/` is a Magento product export (`magento.csv`), not a WooCommerce file. Count rows with `product_type` `simple` as the sellable variants. Do not count the `configurable` row. Do not count a second row that repeats a SKU with `store_view_code` set: in this file that row is another view of the same product. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the simple SKUs are `WICK-S` and `WICK-L`. Both are in the Shopify file. `WICK-LANTERN` is the configurable parent and is not a Shopify SKU. The `cove` row names the same parent `Wick Cove Lantern` and is not its own product. [MAGENTO.md](MAGENTO.md) is the checklist for a real export.

## BigCommerce

`test-catalogs/bigcommerce-basic/` is a legacy Bulk Edit export (`bigcommerce.csv`), not a WooCommerce file. For a product that has SKU rows, count the rows with Item Type `SKU` as the sellable variants and do not count its `Product` row. A product with no SKU rows is one variant, and its `Product` row holds the SKU. Do not count a `Rule` row. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the product has SKU rows, so the SKU rows are `PITCHER-S` and `PITCHER-L`. Both are in the Shopify file. `PITCHER-NETTLE` is the product SKU and is not a Shopify SKU. The Rule row repeats `PITCHER-L` and is not a second variant. [BIGCOMMERCE.md](BIGCOMMERCE.md) is the checklist for a real export.

## Squarespace

`test-catalogs/squarespace-basic/` is a Squarespace product export (`squarespace.csv`), not a WooCommerce file. Count every product row and option row, including the first product row of a product that has option rows. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the SKUs are `JAR-S`, `JAR-L`, `LADLE-FERN`, and `CLOTH-MIST`. All four are in the Shopify file. The jar's second image row has no SKU and is not a variant. [SQUARESPACE.md](SQUARESPACE.md) is the checklist for a real export.

## Wix

`test-catalogs/wix-basic/` is an older Wix Stores catalog export (`wix.csv`), not a WooCommerce file. Count `fieldType` `Variant` rows as the variants. Count a `Product` row only when that product has no options and no `Variant` rows. A `Product` row with options but no `Variant` rows is one variant per option value. Do not count a `Product` row that has `Variant` rows, and do not count by `sku`. On the Shopify sheet, count rows that carry variant details, and skip rows that carry only a handle and an image URL.

On this pair the Variant SKUs are `PITCHER-S` and `PITCHER-L`. `LADLE-REED` and `CLOTH-COVE` are Product rows with no options and no Variant rows, so each is one variant. This file has no Product row that has options without Variant rows. All four are in the Shopify file. `PITCHER-KELP` is the pitcher's Product row SKU and is not a Shopify SKU. The pitcher's second image row has no SKU and is not a variant. [WIX.md](WIX.md) is the checklist for a real export.

## Sampling worksheet

A sample of rows can show that a problem exists, and a clean sample does not show that the whole file is clean. The numbers below are arithmetic on assumed examples, not measurements of any real catalog or tool.

```text
chance of at least one wrong row in the sample = 1 - C(N-k, n) / C(N, n)
```

- `N` is the number of rows in the catalog.
- `k` is the number of wrong rows.
- `n` is the number of rows sampled.
- `C(a, b)` is the number of ways to choose b rows from a rows.

The k wrong rows are different rows, the sample is picked at random without replacement, and every row is equally likely to be picked. Real errors often come in groups (all variants of one product, for example), so a real catalog can behave differently; the table does not describe yours.

Generated by `scripts/make-sampling-table.py`; do not edit the table by hand.

```text
   N   k   n=15   n=30    n=50   n=100
 200   1   7.5%  15.0%   25.0%   50.0%
 200   5  32.6%  56.0%   76.7%   97.0%
 200  10  55.0%  81.1%   94.8%   99.9%
 200  25  87.5%  98.7%  >99.9%  >99.9%
1000   1   1.5%   3.0%    5.0%   10.0%
1000   5   7.3%  14.2%   22.7%   41.0%
1000  10  14.1%  26.4%   40.3%   65.3%
1000  25  31.8%  53.7%   72.7%   93.1%
5000   1   0.3%   0.6%    1.0%    2.0%
5000   5   1.5%   3.0%    4.9%    9.6%
5000  10   3.0%   5.8%    9.6%   18.3%
5000  25   7.3%  14.0%   22.3%   39.7%
```

With 1,000 rows, 10 of them wrong and 15 rows sampled, the chance that the sample contains at least one wrong row is 14.1%, and the chance it contains none is 85.9%.

- [ ] Write down the product count and variant count of both exports before you sample. Why it bites: N in the table is the row count you start from, and a wrong N gives a wrong chance.
- [ ] Choose the sample size from the table before you open any row. Why it bites: choosing after seeing a few rows makes the sample depend on what you saw.
- [ ] Pick sampled rows at random, for example with a spreadsheet random column, not the first rows or the best sellers. Why it bites: the table assumes every row is equally likely to be picked.
- [ ] Check the rows you already know are risky (SKUs with a leading zero, products with several options) as extra rows, not as part of the random sample. Why it bites: they are not random, so they do not count toward the chances in the table.
- [ ] Write down for each sampled row the SKU, the field you compared and the result. Why it bites: a later reader cannot tell what was looked at otherwise.
- [ ] If the sample finds no wrong row, write "none found in n of N rows", not "no errors". Why it bites: the table shows how often a sample of that size misses errors that are there.

The [Catalog Signoff guide to checking products after a Shopify migration](https://catalog-signoff.pages.dev/guides/check-products-after-shopify-migration.html) works the same arithmetic and links a two-file comparison.
