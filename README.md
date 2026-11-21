# Shopify catalog migration checklist

A free [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) checklist for checking a product catalog after a move to Shopify, made for small agencies, freelancers, and merchants doing the move themselves.

| Checklist file | Checks | Practice catalog |
| --- | --- | --- |
| [WooCommerce](CHECKLIST.md) | 40 | [small-clean](test-catalogs/small-clean), [common-mistakes](test-catalogs/common-mistakes), [variable-products](test-catalogs/variable-products) |
| [Magento 2](MAGENTO.md) | 83 | [magento-basic](test-catalogs/magento-basic) |
| [BigCommerce](BIGCOMMERCE.md) | 60 | [bigcommerce-basic](test-catalogs/bigcommerce-basic) |
| [Squarespace](SQUARESPACE.md) | 29 | [squarespace-basic](test-catalogs/squarespace-basic) |
| [Wix](WIX.md) | 24 | [wix-basic](test-catalogs/wix-basic) |

## Practice catalogs

| Folder | Source platform | What is planted |
| --- | --- | --- |
| [small-clean](test-catalogs/small-clean) | WooCommerce | nothing; the two files match |
| [common-mistakes](test-catalogs/common-mistakes) | WooCommerce | missing variant; sale price mapped to price; dropped leading zero; draft published; lost image; duplicated handle |
| [variable-products](test-catalogs/variable-products) | WooCommerce | missing apron variant; fourth option dropped |
| [magento-basic](test-catalogs/magento-basic) | Magento 2 | special price kept past its dates |
| [bigcommerce-basic](test-catalogs/bigcommerce-basic) | BigCommerce | retail price copied into compare-at |
| [squarespace-basic](test-catalogs/squarespace-basic) | Squarespace | sale price ignored when On Sale is No; unlimited stock not tracked |
| [wix-basic](test-catalogs/wix-basic) | Wix | no error; two discount cases the Wix pages leave open (percent rounding, amount subtraction), with this file's choice labelled |

## Start in one minute

1. Open the checklist for your source platform in the table above. For WooCommerce, open [CHECKLIST.md](CHECKLIST.md).
2. Import the matching file from [tracker-import/](tracker-import/) into your project tracker.
3. Practise on the practice catalog in the table. For WooCommerce, start with [`test-catalogs/small-clean`](test-catalogs/small-clean).

This project is independent and is not affiliated with Shopify or WooCommerce. Those names are used only to describe the platforms. It is not affiliated with Adobe or Magento. It is not affiliated with BigCommerce. It is not affiliated with Squarespace. It is not affiliated with Wix.

## Related free tools from the same author

- [Checklist guide](https://catalog-signoff.pages.dev/guides/woocommerce-to-shopify-migration-checklist.html): this checklist as a web guide.
- [Free readiness scan](https://catalog-signoff.pages.dev/tools/readiness-scan.html): drop a WooCommerce product CSV in your browser and see what will cause trouble in Shopify; the catalog is not uploaded.
- [Free redirect map](https://catalog-signoff.pages.dev/tools/redirect-map.html): build a starter Shopify URL-redirect CSV from a WooCommerce product export, in your browser; the catalog is not uploaded.
- [Shopify product CSV checker](https://github.com/ericcheng0904-pixel/product-csv-lint): a command-line checker for a Shopify product CSV before import.

## How to use it

Open the checklist for your source platform in the table above. Tick the items for the phase you are in: before you start, product data, customers and orders, content, SEO, launch day, and the first week after launch. The WooCommerce list is 40 checks in 7 phases.

Practise on the files in [test-catalogs/](test-catalogs/README.md) before you touch a real export. [SPOT-CHECKS.md](SPOT-CHECKS.md) is a short set of spreadsheet and command-line checks for counts and SKUs. It is not a full comparison.

## Import into a project tracker

The files in [tracker-import/](tracker-import/) are plain CSV with the columns Phase, Check, Details, and Source. They are generated from the checklist files and are under the same [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licence. Most trackers and spreadsheets can import a CSV.

From the repository root, regenerate them with `python3 scripts/make-tracker-csv.py`.

## Printable versions

Download a file and open it in a browser, then print or save as PDF from the browser.

- [WooCommerce to Shopify](docs/woocommerce-to-shopify.html)
- [Magento 2 to Shopify](docs/magento-to-shopify.html)
- [BigCommerce to Shopify](docs/bigcommerce-to-shopify.html)
- [Squarespace to Shopify](docs/squarespace-to-shopify.html)
- [Wix to Shopify](docs/wix-to-shopify.html)
- [Spot checks](docs/spot-checks.html)

## Contents

- [Checklist](CHECKLIST.md)
- [Magento 2](MAGENTO.md)
- [BigCommerce](BIGCOMMERCE.md)
- [Squarespace](SQUARESPACE.md)
- [Wix](WIX.md)
- [Tracker import](tracker-import/)
- [Test catalogs](test-catalogs/README.md)
- [Spot checks](SPOT-CHECKS.md)
- [Sources](SOURCES.md)
- [Contributing](CONTRIBUTING.md)
- [Licence](LICENSE)
- [Citation](CITATION.cff)

## Automate the product-data part

[Catalog Signoff](https://catalog-signoff.pages.dev) compares your WooCommerce product CSV with your Shopify product CSV in the browser and lists missing products and variants and SKU and price differences. A free preview shows example findings.

## Licence

The Markdown documents and CSV files are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The scripts and tests are MIT. [LICENSE](LICENSE) says which applies to what.
