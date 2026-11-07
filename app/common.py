import json, os
from pathlib import Path
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "https://api.scavio.dev/api/v1"
TIMEOUT = 45

def load_json(path, default=None):
    p = ROOT / path
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def save_json(path, data):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def api_post(route, payload):
    key = os.environ.get("SCAVIO_API_KEY")
    if not key:
        raise RuntimeError("SCAVIO_API_KEY secret is missing.")
    r = requests.post(f"{API_BASE}/{route.lstrip('/')}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError(f"Unexpected API response from {route}: expected data object.")
    return body["data"]

def norm(value):
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in str(value)).split())

def flatten(value):
    if isinstance(value, dict): return " ".join(flatten(v) for v in value.values())
    if isinstance(value, list): return " ".join(flatten(v) for v in value)
    return str(value) if isinstance(value, str) else ""

def send_discord_alert(name, retailer, store, quantity, url=None):
    hook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not hook: raise RuntimeError("DISCORD_WEBHOOK_URL secret is missing.")
    embed = {"title": f"Pokémon product in stock: {name}",
        "description": "Inventory signals may be delayed or inaccurate. Confirm with the retailer before travelling.",
        "color": 3066993, "timestamp": now_iso(),
        "fields":[{"name":"Retailer","value":retailer.replace("_"," ").title(),"inline":True},
        {"name":"Store","value":store,"inline":True},
        {"name":"Reported quantity","value":str(quantity if quantity is not None else "In stock; quantity unavailable"),"inline":True}]}
    if url: embed["url"] = url
    r = requests.post(hook, json={"username":"Retail Radar","embeds":[embed]}, timeout=TIMEOUT)
    r.raise_for_status()
