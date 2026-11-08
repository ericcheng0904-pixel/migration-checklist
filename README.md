# WooCommerce to Shopify catalog migration checklist

A free checklist for checking a product catalog after a move to Shopify from WooCommerce, Magento 2, BigCommerce, Squarespace, or Wix. The WooCommerce list is 40 checks in 7 phases, from "before you start" to "the first week after launch". The Magento 2 list is [MAGENTO.md](MAGENTO.md). The BigCommerce list is [BIGCOMMERCE.md](BIGCOMMERCE.md). The Squarespace list is [SQUARESPACE.md](SQUARESPACE.md). The Wix list is [WIX.md](WIX.md). It comes with seven fictional practice catalogs (a source export and the matching Shopify import file for each). Licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Made for small agencies, freelancers, and merchants doing the move themselves.

This project is independent and is not affiliated with Shopify or WooCommerce. Those names are used only to describe the platforms. It is not affiliated with Adobe or Magento. It is not affiliated with BigCommerce. It is not affiliated with Squarespace. It is not affiliated with Wix.

## Start in one minute

1. Copy [CHECKLIST.md](CHECKLIST.md) into your project tracker. For a Magento 2 store, copy [MAGENTO.md](MAGENTO.md). For a BigCommerce store, copy [BIGCOMMERCE.md](BIGCOMMERCE.md). For a Squarespace store, copy [SQUARESPACE.md](SQUARESPACE.md). For a Wix store, copy [WIX.md](WIX.md).
2. Practise on [`test-catalogs/small-clean`](test-catalogs/small-clean): `woocommerce.csv` is the store before the move and `shopify.csv` is the same store after. Compare them with the [spot checks](SPOT-CHECKS.md), then try `test-catalogs/common-mistakes`, which has planted errors. For Magento 2, practise on [`test-catalogs/magento-basic`](test-catalogs/magento-basic). For BigCommerce, practise on [`test-catalogs/bigcommerce-basic`](test-catalogs/bigcommerce-basic). For Squarespace, practise on [`test-catalogs/squarespace-basic`](test-catalogs/squarespace-basic). For Wix, practise on [`test-catalogs/wix-basic`](test-catalogs/wix-basic).

## Related free tools from the same author

- [Checklist guide](https://catalog-signoff.pages.dev/guides/woocommerce-to-shopify-migration-checklist.html): this checklist as a web guide.
- [Free readiness scan](https://catalog-signoff.pages.dev/tools/readiness-scan.html): drop a WooCommerce product CSV in your browser and see what will cause trouble in Shopify; the catalog is not uploaded.
- [Free redirect map](https://catalog-signoff.pages.dev/tools/redirect-map.html): build a starter Shopify URL-redirect CSV from a WooCommerce product export, in your browser; the catalog is not uploaded.

## How to use it

Copy [CHECKLIST.md](CHECKLIST.md) into your project tracker. Tick the items for the phase you are in: before you start, product data, customers and orders, content, SEO, launch day, and the first week after launch. For a Magento 2 store, use [MAGENTO.md](MAGENTO.md) for those same phases. For a BigCommerce store, use [BIGCOMMERCE.md](BIGCOMMERCE.md). For a Squarespace store, use [SQUARESPACE.md](SQUARESPACE.md). For a Wix store, use [WIX.md](WIX.md).

Practise on the files in [test-catalogs/](test-catalogs/README.md) before you touch a real export. [SPOT-CHECKS.md](SPOT-CHECKS.md) is a short set of spreadsheet and command-line checks for counts and SKUs. It is not a full comparison.

## Contents

- [Checklist](CHECKLIST.md)
- [Magento 2](MAGENTO.md)
- [BigCommerce](BIGCOMMERCE.md)
- [Squarespace](SQUARESPACE.md)
- [Wix](WIX.md)
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
