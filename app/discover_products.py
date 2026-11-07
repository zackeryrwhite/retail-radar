from app.common import load_json, api_post

def show(label, rows, idkey, titlekey):
    print("\n" + label)
    terms = ("booster bundle", "elite trainer box")
    candidates = [x for x in rows if any(t in str(x.get(titlekey, "")).lower() for t in terms)]
    if not candidates:
        print("NO SEALED TCG MATCH; returned", len(rows), "non-matching products.")
        return
    for x in candidates:
        print({
            "identifier": x.get(idkey),
            "title": x.get(titlekey),
            "upc": x.get("upc"),
            "sku": x.get("sku"),
            "dpci": x.get("dpci"),
            "is_marketplace": x.get("is_marketplace"),
            "price": x.get("price"),
            "available_quantity": x.get("available_quantity"),
            "in_stock": x.get("in_stock"),
            "availability": x.get("availability"),
            "url": x.get("url"),
        })

def main():
    products = load_json("config/products.json")
    cfg = load_json("config/stores.json")
    loc = cfg["locations"]
    for p in products:
        q = p["search_query"]
        upc = p.get("upc")
        print("\n###", p["name"], "| UPC:", upc, "| query:", q)
        searches = [
            ("walgreens", "walgreens/search",
             {"query": upc or q, "store_id": loc["walgreens"].get("store_id")},
             "product_id", "name"),
            ("dollar_general", "dollargeneral/search",
             {"query": upc or q, "store_id": loc["dollar_general"].get("store_id")},
             "upc", "title"),
            ("walmart", "walmart/search",
             {"query": q, "store_id": loc["walmart"].get("store_id"),
              "delivery_zip": cfg["postal_code"], "domain": "com"},
             "id", "title"),
            ("target", "target/search",
             {"keyword": q, "store_id": loc["target"].get("store_id")},
             "tcin", "title"),
        ]
        for retailer, route, payload, idkey, titlekey in searches:
            if not loc[retailer].get("enabled") or not loc[retailer].get("store_id"):
                continue
            try:
                data = api_post(route, payload)
                show(retailer.upper(), data.get("products", []), idkey, titlekey)
            except Exception as e:
                print("ERROR", retailer, e)
    # Walgreens assortment WICs are separate from set-specific product identifiers.
    # Positive assortment results indicate a broad category, not a specific set.
    try:
        assortments = load_json("config/walgreens_assortments.json")
        walgreens = loc["walgreens"]
        if walgreens.get("enabled") and walgreens.get("store_id"):
            print("\n### WALGREENS ASSORTMENT WATCHLIST (not set-specific)")
            for item in assortments:
                code = item["wic"]
                try:
                    data = api_post("walgreens/search", {
                        "query": code,
                        "store_id": walgreens.get("store_id"),
                    })
                    rows = data.get("products", [])
                    print({
                        "wic_query": code,
                        "category": item["category"],
                        "interpretation": item["interpretation"],
                        "matches_returned": len(rows),
                    })
                    for row in rows:
                        print({
                            "wic_query": code,
                            "product_id": row.get("product_id"),
                            "title": row.get("name"),
                            "upc": row.get("upc"),
                            "price": row.get("price"),
                            "availability": row.get("availability"),
                            "url": row.get("url"),
                        })
                    if not rows:
                        print("NO MATCHES for WIC query", code)
                except Exception as e:
                    print("WALGREENS ASSORTMENT ERROR", code, e)
    except FileNotFoundError:
        print("Walgreens assortment config not found; skipping assortment searches.")

    print("\nOnly use an identifier when the exact sealed product matches.")
    print("Walgreens: product_id; Dollar General: UPC; Walmart: item_id; Target: TCIN. Staples disabled.")

if __name__ == "__main__":
    main()
