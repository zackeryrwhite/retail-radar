# Retail Radar

Pokémon TCG product discovery and a manual-refresh inventory dashboard for selected retailers.

## Dashboard

The dashboard is a static GitHub Pages site. Press **Refresh All**, confirm **Run workflow** on GitHub Actions, and return/reload the dashboard after the workflow publishes its results.

- No Render or other external hosting service.
- No scheduled polling or automatic browser refresh.
- Scavio API key remains in GitHub Actions secrets and is never included in browser code.
- Dashboard refresh workflow does not send Discord alerts.

See [Dashboard setup and operation](README-DASHBOARD.md).

## Watchlist
- Delta Reign Booster Bundle — UPC 196214165823
- 30th Celebration Booster Bundle — UPC 196214158849
- Pitch Black Booster Bundle — UPC 196214157484

## Store configuration
- Walgreens: 431 Hamilton St, Geneva, NY 14456 — discovery enabled; monitoring off.
- Dollar General: 194 N Exchange St, Geneva, NY 14456 — discovery enabled; monitoring off.
- Walmart: 990 NY-5 and 20, Geneva, NY 14456 — paused after discovery returned third-party marketplace sellers.
- Target: 7500 Commons Blvd, Victor, NY 14564 — discovery only; no validated first-party store-level stock adapter.
- Staples: 337 Hamilton St, Geneva, NY 14456 — disabled pending a verified inventory adapter.

## Walgreens assortment research
`config/walgreens_assortments.json` contains four broad Walgreens assortment/catalog codes:
- 665814 — universal Pokémon pack assortment
- 941046 — mini-tin assortment
- 300443630 — Pokémon TCG online assortment baseline
- 300425671 — third-party packaged Pokémon Trading Cards Lightning Set

These are assortment/catalog codes, not proof that any specific set is in stock. Discovery results must not be converted into set-specific stock alerts without exact matching.

## Discovery
Run **Actions → Discover Products → Run workflow** to research product matches. Review exact set, packaging, seller, and retailer identifiers before changing the monitoring configuration.

## Live inventory eligibility
The dashboard refresh workflow currently supports:
- Walgreens `walgreens/stock` using a verified retailer product ID.
- Dollar General `dollargeneral/stores` using a product UPC and configured store ID.

A check runs only when the retailer is enabled, `monitor_enabled` is true, a store ID exists, and the product has the matching retailer-specific identifier. Walmart and Target are deliberately excluded until their inventory integrations are verified. Unknown responses are never represented as out of stock.

At present, no product/store combination is eligible for live monitoring. Refresh All will report zero eligible checks without consuming Scavio credits on unverified product matches.

## Secrets
The dashboard refresh workflow uses the existing `SCAVIO_API_KEY` repository secret. Do not put API keys or personal access tokens in `docs/` or any browser-side JavaScript.
