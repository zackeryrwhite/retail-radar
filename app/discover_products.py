from app.common import load_json, api_post

def show(label, rows, idkey, titlekey):
    print("\n"+label)
    for x in rows:
        print({"identifier":x.get(idkey),"title":x.get(titlekey),"upc":x.get("upc"),
               "sku":x.get("sku"),"price":x.get("price"),"availability":x.get("availability"),
               "url":x.get("url")})

def main():
    products=load_json("config/products.json")
    cfg=load_json("config/stores.json")
    loc=cfg["locations"]
    for p in products:
        q=p["search_query"]
        print("\n###",p["name"])
        for retailer,route,payload,idkey,titlekey in [
          ("walgreens","walgreens/search",{"query":q,"store_id":loc["walgreens"].get("store_id")},"product_id","name"),
          ("dollar_general","dollargeneral/search",{"query":q,"store_id":loc["dollar_general"].get("store_id")},"upc","title"),
          ("walmart","walmart/search",{"query":q,"store_id":loc["walmart"].get("store_id"),"delivery_zip":cfg["postal_code"],"domain":"com"},"id","title")]:
            if not loc[retailer].get("enabled") or not loc[retailer].get("store_id"): continue
            try:
                data=api_post(route,payload)
                show(retailer.upper(),data.get("products",[]),idkey,titlekey)
            except Exception as e: print("ERROR",retailer,e)
    print("\nConfirm exact set, product type, and packaging before copying identifiers.")
    print("Walgreens: product_id; Dollar General: UPC; Walmart: item_id. Staples disabled.")

if __name__=="__main__": main()
