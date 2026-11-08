# Retail Radar Dashboard

The dashboard is a static GitHub Pages frontend with a small authenticated API service. Scavio credentials stay on the API server and are never sent to the browser.

## Manual-only behavior
- The dashboard does not poll or refresh in the background.
- Inventory requests are sent only after a user presses **Refresh All**.
- The API checks only enabled retailers with `monitor_enabled: true` and a verified product identifier.
- Walmart and Target are intentionally excluded from live checks pending validated first-party/store-level inventory integrations.
- The API has a basic password gate and a per-IP refresh limit.

## Deployment
1. Deploy this repository to Render using the Blueprint at `render.yaml`.
2. During deployment, set the existing `SCAVIO_API_KEY` secret and choose a strong `DASHBOARD_PASSWORD`. Do not put either value in GitHub files or the frontend.
3. After Render provides the service URL, set `window.RETAIL_RADAR_API` in `docs/config.js` to that URL (include https://, no trailing slash), and commit.
4. In GitHub repository Settings → Pages, select **GitHub Actions** as the build/deploy source. The Pages workflow publishes the `docs` directory.
5. Open the Pages URL and enter the dashboard password.

Render free services may sleep when idle; the first request after inactivity can take a little longer. Render's free filesystem is ephemeral, so the dashboard displays the latest results in the current browser session rather than treating the service filesystem as permanent history.

## API routes
- `GET /api/health` public health check
- `GET /api/dashboard` authenticated configuration and latest available server snapshot
- `POST /api/refresh` authenticated manual refresh

The browser sends the password over HTTPS using HTTP Basic authentication. The API uses it only to authorize dashboard requests. Rotate it by changing `DASHBOARD_PASSWORD` in Render.
