import os
import json
import time
import secrets
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, deque

import requests
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "https://api.scavio.dev/api/v1"
TIMEOUT = 45
security = HTTPBasic()
app = FastAPI(title="Retail Radar API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

_requests = defaultdict(deque)

def read_json(path, default=None):
    p = ROOT / path
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def require_dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    expected = os.environ.get("DASHBOARD_PASSWORD", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Dashboard password is not configured on the server.")
    ok_user = secrets.compare_digest(credentials.username, "retail-radar")
    ok_pass = secrets.compare_digest(credentials.password, expected)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Incorrect dashboard password.", headers={"WWW-Authenticate": "Basic"})
    return True

def rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    q = _requests[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 8:
        raise HTTPException(status_code=429, detail="Too many refreshes. Wait a minute and try again.")
    q.append(now)

def api_post(route, payload):
    key = os.environ.get("SCAVIO_API_KEY")
    if not key:
        raise RuntimeError("SCAVIO_API_KEY is not configured on the server.")
    response = requests.post(
        f"{API_BASE}/{route.lstrip('/')}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError(f"Unexpected Scavio response from {route}.")
    return body["data"]

def find_row(rows, keys, wanted):
    for row in rows if isinstance(rows, list) else []:
        if any(str(row.get(k, "")) == str(wanted) for k in keys):
            return row
    return None

def stock_value(row):
    if isinstance(row.get("in_stock"), bool):
        return row["in_stock"]
    value = str(row.get("availability_status") or row.get("status") or "").lower().strip()
    if value in {"in stock", "available", "in_stock"}:
        return True
    if value in {"out of stock", "unavailable", "out_of_stock", "not available"}:
        return False
    availability = row.get("availability")
    if isinstance(availability, dict):
        for key in ("in_store", "pickup"):
            if isinstance(availability.get(key), bool):
                return availability[key]
    return None

def eligible_checks():
    products = read_json("config/products.json", [])
    config = read_json("config/stores.json", {})
    locations = config.get("locations", {})
    checks = []
    # Only retailers with a known route are considered. Walmart and Target are
    # deliberately excluded until first-party and store-level stock are verified.
    for product in products:
        identifiers = product.get("retailers", {})
        walgreens = locations.get("walgreens", {})
        product_id = identifiers.get("walgreens", {}).get("product_id")
        if walgreens.get("enabled") and walgreens.get("monitor_enabled") and walgreens.get("store_id") and product_id:
            checks.append({
                "product": product, "retailer": "walgreens", "store": walgreens,
                "route": "walgreens/stock",
                "payload": {"product_id": product_id, "store_ids": [walgreens["store_id"]]},
                "list_key": "stores", "id_keys": ["store_number", "store_id"],
                "match_id": walgreens["store_id"],
            })
        dg = locations.get("dollar_general", {})
        upc = identifiers.get("dollar_general", {}).get("upc")
        if dg.get("enabled") and dg.get("monitor_enabled") and dg.get("store_id") and upc:
            checks.append({
                "product": product, "retailer": "dollar_general", "store": dg,
                "route": "dollargeneral/stores",
                "payload": {"zip": config.get("postal_code", ""), "radius": 25, "upc": upc},
                "list_key": "stores", "id_keys": ["store_id"],
                "match_id": dg["store_id"],
            })
    return checks

@app.get("/api/health")
def health():
    return {"ok": True, "service": "Retail Radar API"}

@app.get("/api/dashboard")
def dashboard(_: bool = Depends(require_dashboard)):
    products = read_json("config/products.json", [])
    config = read_json("config/stores.json", {})
    stores = config.get("locations", {})
    eligible = eligible_checks()
    last = read_json("data/latest.json", {})
    return {
        "products": [{"key": p["key"], "name": p["name"], "upc": p.get("upc")} for p in products],
        "stores": [
            {"key": key, "name": store.get("display_name", key), "address": store.get("address", ""),
             "enabled": bool(store.get("enabled")), "monitor_enabled": bool(store.get("monitor_enabled"))}
            for key, store in stores.items()
        ],
        "eligible_checks": len(eligible),
        "last_refresh": last.get("generated_at"),
        "last_results": last.get("observations", []),
    }

@app.post("/api/refresh")
def refresh(request: Request, _: bool = Depends(require_dashboard)):
    rate_limit(request)
    checks = eligible_checks()
    started = now_iso()
    results, errors = [], []
    for check in checks:
        product, store = check["product"], check["store"]
        item = {"product": product["name"], "retailer": check["retailer"],
                "store": store.get("display_name"), "address": store.get("address"),
                "checked_at": now_iso(), "status": "unknown", "quantity": None, "url": None}
        try:
            data = api_post(check["route"], check["payload"])
            row = find_row(data.get(check["list_key"], []), check["id_keys"], check["match_id"])
            if row is None:
                raise ValueError("Configured store was not present in the retailer response.")
            flag = stock_value(row)
            item["status"] = "in_stock" if flag is True else "out_of_stock" if flag is False else "unknown"
            item["quantity"] = row.get("quantity", row.get("available_quantity"))
            item["url"] = row.get("url")
            if flag is None:
                item["note"] = "Retailer response did not include a recognized stock status."
            results.append(item)
        except Exception as exc:
            item["status"] = "error"
            item["note"] = str(exc)[:300]
            results.append(item)
            errors.append(f'{check["retailer"]} / {product["name"]}: {exc}')
    response = {
        "generated_at": now_iso(), "started_at": started,
        "status": "no_eligible_checks" if not checks else "completed_with_errors" if errors else "completed",
        "eligible_checks": len(checks), "results": results, "errors": errors,
    }
    # Render's filesystem is ephemeral; the browser retains the latest result.
    return response
