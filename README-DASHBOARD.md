# Retail Radar Dashboard

The dashboard and its authenticated API run together as one Render web service. Scavio credentials stay on the server and are never sent to the browser.

## Manual-only behavior
- The dashboard does not poll or refresh in the background.
- Inventory requests are sent only after a user presses **Refresh All**.
- The API checks only enabled retailers with `monitor_enabled: true` and a verified product identifier.
- Walmart and Target are intentionally excluded from live checks pending validated first-party and store-level inventory integrations.
- The API has a password gate and a per-IP refresh limit.

## Deploy
1. Open the [Render one-click deployment page](https://render.com/deploy?repo=https://github.com/zackeryrwhite/retail-radar).
2. Connect GitHub and review the `retail-radar-api` service from `render.yaml`.
3. Enter your existing `SCAVIO_API_KEY` as the secret value and create a strong `DASHBOARD_PASSWORD`. These values are stored by Render, not committed to GitHub.
4. Deploy. Render will provide one HTTPS URL; open it to use the dashboard.

The service is configured on Render's free plan. It may sleep while idle, so the first visit or refresh after a period of inactivity can take longer. No paid database or persistent disk is required for the initial manual dashboard.

## Current retailer eligibility
At present, the product watchlist has no verified retailer-specific product IDs and the current retailer configurations have monitoring disabled. Therefore **Refresh All will initially report zero eligible checks** rather than spend API credits on unverified matches. Once a retailer's exact product match and stock response have been independently validated, set its `monitor_enabled` flag to `true` in `config/stores.json` and populate the corresponding product identifier in `config/products.json`. The dashboard will then include those checks automatically on the next deploy.

Only Walgreens and Dollar General adapters are currently implemented in the dashboard API. Walmart remains paused; Target remains discovery-only; Staples is unsupported.

## API routes
- `GET /api/health` public health check
- `GET /api/dashboard` authenticated configuration and latest committed snapshot
- `POST /api/refresh` authenticated manual refresh

The dashboard password is sent only over HTTPS using HTTP Basic authentication. Rotate it by changing `DASHBOARD_PASSWORD` in the Render service environment.

## Notes
- No scheduled inventory checks, background polling, or Discord notifications are triggered by this dashboard.
- The initial API response is displayed in the browser session; Render's free filesystem is ephemeral, so the service does not promise durable refresh history.
- Inventory can be delayed or inaccurate; confirm with the retailer before travelling.
