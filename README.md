# Retail Radar

Scheduled Pokémon TCG inventory checks for selected Geneva, NY stores, with Discord alerts.

## Integrations
- Walgreens: store lookup, product search, and stock lookup.
- Dollar General: store lookup, product search, and UPC-based stock lookup.
- Walmart: paused; discovery found only third-party marketplace sellers, so no Walmart stock monitoring is active.
- Target: product search by TCIN and store-level availability at Victor store 1156.
- Staples: disabled until a verified store-level inventory integration is available.

## Initial store targets
- Walgreens: 431 Hamilton St, Geneva, NY 14456
- Dollar General: 194 N Exchange St, Geneva, NY 14456
- Walmart: 990 NY-5 and 20, Geneva, NY 14456
- Target: 7500 Commons Blvd, Victor, NY 14564 (store 1156)
- Staples: 337 Hamilton St, Geneva, NY 14456 (disabled)

Store IDs are configured: Walgreens 10697, Dollar General 14405, Walmart 1731 (paused), and Target Victor 1156.

## Products
- Delta Reign Booster Bundle
- 30th Celebration Booster Bundle
- Pitch Black Booster Bundle

Product identifiers are intentionally blank until exact variants are confirmed.

## Walgreens assortment watchlist

The separate `config/walgreens_assortments.json` list searches Walgreens WIC assortment codes independently of the three set-specific products:
- 665814 — universal Pokémon pack assortment (packs, blisters, individual packs)
- 941046 — mini-tin assortment
- 300443630 — Pokémon TCG online assortment baseline
- 300425671 — third-party packaged Pokémon Trading Cards Lightning Set

These are assortment/catalog lookup codes, not verified set-specific product IDs. A match or positive assortment quantity must not be interpreted as proof that Delta Reign, 30th Celebration, or Pitch Black is in stock. Discovery prints matches for manual review; it does not configure Walgreens stock alerts from WIC codes.

## Setup
1. In **Settings → Secrets and variables → Actions**, add repository secrets:
   - `SCAVIO_API_KEY`
   - `DISCORD_WEBHOOK_URL`
2. Open **Actions → Discover Products → Run workflow**.
3. Inspect the logs for exact sealed-product matches and retailer-specific identifiers. Store IDs are already configured.
4. Confirm exact set, packaging, and variant, then fill the matching IDs in `config/products.json`:
   - Walgreens: `product_id`
   - Dollar General: `upc`
   - Walmart: `item_id`
   - Target: `tcin`
   Leave unmatched IDs as `null`.
5. Run **Actions → Inventory Monitor → Run workflow** to test. Monitoring is scheduled every 15 minutes after setup.

## Monitoring status

Retailer discovery and live inventory monitoring are controlled separately. Walmart is paused entirely after the latest discovery run returned only third-party sellers. Walgreens, Dollar General, and Target remain available for discovery, but live monitoring is disabled until exact product matches and reliable stock responses are verified. Set a retailer's `monitor_enabled` to `true` only after that verification.

## Walmart seller verification

Retail Radar only treats a Walmart listing as eligible for Walmart stock alerts when the product response explicitly identifies `seller_name` as `Walmart.com`. Marketplace listings, other sellers, and listings with missing/unverified seller identity are skipped. A listing being hosted on walmart.com, fulfilled by Walmart, or showing a Walmart URL is not by itself proof that Walmart is the seller.

## Reliability
- Alerts fire on the first positive stock observation and when a product changes from out of stock to in stock.
- Unknown stock responses are logged as errors, not treated as out of stock.
- Inventory can be delayed or inaccurate; confirm with the retailer before travelling.
- Scheduled GitHub Actions can be delayed and are not a continuously running service.
- API routes and response fields still need to be validated against your current Scavio account/docs before relying on live alerts. Review credit usage before enabling scheduled polling.

## Local use
Python 3.11+:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.discover_products
python -m app.monitor
```
