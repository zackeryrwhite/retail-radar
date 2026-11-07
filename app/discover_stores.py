from app.common import load_json, save_json, api_post, flatten, norm

def main():
    cfg = load_json("config/stores.json")
    for retailer, route, payload, id_key in [
        ("walgreens","walgreens/stores",{"zip":cfg["postal_code"],"limit":25},"store_number"),
        ("dollar_general","dollargeneral/stores",{"zip":cfg["postal_code"],"radius":25},"store_id"),
        ("walmart","walmart/stores",{"zipcode":cfg["postal_code"],"domain":"com"},"store_id")]:
        target = cfg["locations"][retailer]
        try:
            data = api_post(route,payload)
            rows = data.get("stores",[])
            needle = norm(target["street_match"])
            matches = [x for x in rows if needle in norm(flatten(x))]
            if len(matches)==1 and matches[0].get(id_key):
                target["store_id"] = str(matches[0][id_key])
                print(f"MATCH {retailer}: {target['address']} => {target['store_id']}")
            else:
                print(f"REVIEW {retailer}: expected one exact street match, got {len(matches)}")
                for row in rows: print(row)
        except Exception as e: print(f"ERROR {retailer}: {e}")
    save_json("config/stores.json",cfg)
    print("Staples remains disabled pending a verified inventory integration.")

if __name__=="__main__": main()
