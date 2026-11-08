from app.common import load_json, save_json, api_post, now_iso

def find_store(rows, store_id, keys):
    for row in rows if isinstance(rows, list) else []:
        if any(str(row.get(key, "")) == str(store_id) for key in keys):
            return row
    return None

def stock_flag(row):
    if isinstance(row.get("in_stock"), bool):
        return row["in_stock"]
    status = str(row.get("availability_status") or row.get("status") or "").lower().strip()
    if status in {"in stock", "available", "in_stock"}:
        return True
    if status in {"out of stock", "unavailable", "out_of_stock", "not available"}:
        return False
    in_store = str(row.get("in_store") or "").lower().strip()
    if in_store in {"in_stock", "limited_stock_see_store"}:
        return True
    if in_store in {"out_of_stock", "unavailable"}:
        return False
    if in_store == "not_sold_in_store":
        return None
    availability = row.get("availability")
    if isinstance(availability, dict):
        for key in ("in_store", "pickup"):
            if isinstance(availability.get(key), bool):
                return availability[key]
    return None

def main():
    products = load_json("config/products.json", [])
    config = load_json("config/stores.json", {})
    locations = config.get("locations", {})
    results, errors = [], []
    eligible = 0

    for product in products:
        retailer_ids = product.get("retailers", {})

        store = locations.get("walgreens", {})
        product_id = retailer_ids.get("walgreens", {}).get("product_id")
        if store.get("enabled") and store.get("monitor_enabled") and store.get("store_id") and product_id:
            eligible += 1
            results.append(check(
                product, "walgreens", store, "walgreens/stock",
                {"product_id": product_id, "store_ids": [store["store_id"]]},
                "stores", ["store_number", "store_id"], store["store_id"], errors
            ))

        store = locations.get("dollar_general", {})
        upc = retailer_ids.get("dollar_general", {}).get("upc")
        if store.get("enabled") and store.get("monitor_enabled") and store.get("store_id") and upc:
            eligible += 1
            results.append(check(
                product, "dollar_general", store, "dollargeneral/stores",
                {"zip": config.get("postal_code", ""), "radius": 25, "upc": upc},
                "stores", ["store_id"], store["store_id"], errors
            ))

    generated_at = now_iso()
    payload = {
        "generated_at": generated_at,
        "status": "no_eligible_checks" if eligible == 0 else ("completed_with_errors" if errors else "completed"),
        "eligible_checks": eligible,
        "results": results,
        "errors": errors,
        "message": "No verified, monitor-enabled product/store combinations are configured." if eligible == 0 else None,
    }

    # Append each manual run and its observations. Keep bounded history so the
    # GitHub Pages artifact stays small and repository commits remain manageable.
    history = load_json("data/history.json", {"runs": [], "observations": []})
    runs = history.get("runs", [])
    observations = history.get("observations", [])
    runs.append({
        "generated_at": generated_at,
        "status": payload["status"],
        "eligible_checks": eligible,
        "result_count": len(results),
        "error_count": len(errors),
    })
    for result in results:
        observations.append({
            **result,
            "run_at": generated_at,
            "observation_key": "|".join([
                result.get("retailer", ""),
                result.get("store", ""),
                result.get("product", ""),
            ]),
        })
    history["runs"] = runs[-250:]
    history["observations"] = observations[-1000:]
    history["retention"] = {"max_runs": 250, "max_observations": 1000}

    save_json("data/latest.json", payload)
    save_json("data/history.json", history)
    print(f"Dashboard refresh complete: {eligible} eligible checks, {len(errors)} errors; history now has {len(history['observations'])} observations.")

def check(product, retailer, store, route, request_payload, list_key, id_keys, store_id, errors):
    result = {
        "product": product["name"],
        "retailer": retailer,
        "store": store.get("display_name", retailer),
        "address": store.get("address", ""),
        "checked_at": now_iso(),
        "status": "unknown",
        "quantity": None,
        "url": None,
        "note": None,
    }
    try:
        data = api_post(route, request_payload)
        row = find_store(data.get(list_key, []), store_id, id_keys)
        if row is None:
            raise ValueError("Configured store was not present in the retailer response.")
        flag = stock_flag(row)
        result["status"] = "in_stock" if flag is True else "out_of_stock" if flag is False else "unknown"
        result["quantity"] = row.get("quantity", row.get("available_quantity"))
        result["url"] = row.get("url")
        if flag is None:
            result["note"] = "Retailer response did not contain a recognized stock status."
    except Exception as exc:
        result["status"] = "error"
        result["note"] = str(exc)[:300]
        errors.append(f"{retailer} / {product['name']}: {exc}")
    return result

if __name__ == "__main__":
    main()
