# Retail Radar Dashboard

The dashboard is a static GitHub Pages site. Inventory checks run in GitHub Actions only when you manually start the **Retail Radar Dashboard** workflow.

## How Refresh All works
1. Press **Refresh All** on the dashboard.
2. GitHub opens its authenticated workflow page. Press **Run workflow**.
3. GitHub Actions runs the Python checker using the repository's `SCAVIO_API_KEY` secret.
4. The workflow publishes the new inventory snapshot to GitHub Pages.
5. Return to the dashboard and reload it to see the latest results.

A public static webpage cannot safely contain a GitHub token, so the GitHub confirmation step is intentional. No token or API key is stored in browser code.

## Publish the dashboard
1. In the repository, open **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. The `.github/workflows/dashboard.yml` workflow publishes the `docs` folder on changes and after manual refresh runs.
4. Open the Pages URL shown in **Settings → Pages**.

## Secrets
The existing `SCAVIO_API_KEY` Actions repository secret is used by the manual refresh workflow. The workflow does not use the Discord webhook and does not send Discord alerts.

## Retailer safety and eligibility
Only retailers with an implemented, validated inventory adapter, an enabled store, `monitor_enabled: true`, a store ID, and a retailer-specific product identifier are checked.

- Walgreens: adapter present; currently disabled for monitoring and no verified set-specific product IDs.
- Dollar General: adapter present; currently disabled for monitoring. UPC search did not produce verified exact matches.
- Walmart: paused; discovery found only third-party marketplace listings.
- Target: discovery only; no validated first-party store-level stock adapter.
- Staples: unsupported.

Consequently, the current watchlist has zero eligible live checks. Refresh All will publish that status without spending Scavio credits on unverified products or retailers.

## Manual-only guarantees
- No scheduled inventory polling.
- No automatic browser refresh or polling.
- No Discord notifications from the dashboard refresh workflow.
- Refreshes are started only through GitHub's authenticated Actions UI.
