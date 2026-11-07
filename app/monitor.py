from app.common import load_json, save_json, api_post, send_discord_alert, now_iso

def by_id(rows, keys, wanted):
    for row in rows:
        if any(str(row.get(k,""))==str(wanted) for k in keys): return row
    return None

def in_stock(row):
    if isinstance(row.get("in_stock"),bool): return row["in_stock"]
    s=str(row.get("availability_status") or row.get("status") or "").lower().strip()
    if s in {"in stock","available","in_stock"}: return True
    if s in {"out of stock","unavailable","out_of_stock","not available"}: return False
    target_status=str(row.get("in_store") or "").lower().strip()
    if target_status in {"in_stock","limited_stock_see_store"}: return True
    if target_status in {"out_of_stock","unavailable"}: return False
    if target_status == "not_sold_in_store": return None
    av=row.get("availability")
    if isinstance(av,dict):
        for k in ("in_store","pickup"):
            if isinstance(av.get(k),bool): return av[k]
    return None

def main():
    products=load_json("config/products.json")
    cfg=load_json("config/stores.json")
    state=load_json("data/state.json",{})
    configured = any(
      ids[retailer].get(field)
      for p in products for retailer, field in [
        ("walgreens","product_id"),("dollar_general","upc"),("walmart","item_id"),("target","tcin")]
    )
    if not configured:
      print("No product identifiers configured yet; skipping this run without writing state.")
      return
    observations=[]; errors=[]
    for p in products:
      ids=p["retailers"]
      checks=[
       ("walgreens","walgreens/stock",{"product_id":ids["walgreens"].get("product_id"),"store_ids":[cfg["locations"]["walgreens"].get("store_id")]},["store_number","store_id"],"stores"),
       ("dollar_general","dollargeneral/stores",{"zip":cfg["postal_code"],"radius":25,"upc":ids["dollar_general"].get("upc")},["store_id"],"stores"),
       ("walmart","walmart/search",{"query":p["search_query"],"store_id":cfg["locations"]["walmart"].get("store_id"),"delivery_zip":cfg["postal_code"],"domain":"com"},["id","item_id"],"products"),
       ("target","target/availability",{"tcin":ids["target"].get("tcin"),"zip":cfg["locations"]["target"].get("postal_code"),"store_id":cfg["locations"]["target"].get("store_id")},["store_id"],"stores")]
      for retailer,route,payload,idkeys,listkey in checks:
        store=cfg["locations"][retailer]
        ident=ids[retailer].get({"walgreens":"product_id","dollar_general":"upc","walmart":"item_id","target":"tcin"}[retailer])
        if not store.get("enabled") or not store.get("store_id") or not ident: continue
        try:
          data=api_post(route,payload)
          row=by_id(data.get(listkey,[]),idkeys,store["store_id"] if retailer!="walmart" else ident)
          if row is None: raise ValueError("Configured store/product was not present in response.")
          flag=in_stock(row)
          if flag is None: raise ValueError("Response did not contain a recognized stock status.")
          key=f"{retailer}:{store['store_id']}:{p['key']}"
          prev=state.get(key)
          qty=row.get("quantity",row.get("available_quantity"))
          if flag and (prev is None or prev.get("in_stock") is False):
            send_discord_alert(p["name"],retailer,store["display_name"],qty,row.get("url"))
          state[key]={"in_stock":flag,"quantity":qty,"checked_at":now_iso()}
          observations.append({"product":p["name"],"retailer":retailer,"store":store["display_name"],
            "address":store["address"],"in_stock":flag,"quantity":qty,"checked_at":now_iso(),"source":"Scavio"})
        except Exception as e: errors.append(f"{retailer} / {p['name']}: {e}")
      st=cfg["locations"]["staples"]
      observations.append({"product":p["name"],"retailer":"staples","store":st["display_name"],
        "address":st["address"],"in_stock":None,"quantity":None,"checked_at":now_iso(),
        "source":"unsupported","note":"No verified Staples store-level inventory adapter."})
    save_json("data/state.json",state)
    save_json("data/latest.json",{"generated_at":now_iso(),"status":"completed_with_errors" if errors else "completed",
      "observations":observations,"errors":errors})
    for e in errors: print("ERROR:",e)
    print(f"Finished: {len(observations)} observations; {len(errors)} errors.")

if __name__=="__main__": main()
