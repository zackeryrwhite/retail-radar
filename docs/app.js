(() => {
const $ = (id) => document.getElementById(id);
const stamp = () => Date.now();
function fmt(value) {
  if (!value) return "—";
  const d = new Date(value);
  return isNaN(d) ? "—" : d.toLocaleString([], {month:"short",day:"numeric",year:"numeric",hour:"numeric",minute:"2-digit"});
}
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function renderProducts(products) {
  $("productCount").textContent = products.length;
  $("products").innerHTML = products.map((p,i) =>
    '<article class="product"><span class="product-index">WATCHLIST / '+String(i+1).padStart(2,"0")+
    '</span><h3>'+esc(p.name)+'</h3><div class="upc">UPC '+esc(p.upc || "Not set")+
    '</div><div class="status-line">Manual inventory checks only</div></article>').join("");
}
function renderStores(config) {
  const locations = config.locations || {};
  $("stores").innerHTML = Object.entries(locations).map(([key,s]) => {
    const enabled = !!(s.enabled && s.monitor_enabled);
    const status = enabled ? "MONITOR ENABLED" : (s.enabled ? "DISCOVERY ONLY" : "PAUSED");
    return '<article class="store"><div><strong>'+esc(s.display_name || key)+'</strong><small>'+
      esc(s.address || "")+'</small></div><span class="store-state '+(enabled?"ready":"")+'">'+status+'</span></article>';
  }).join("");
}
function resultStatus(r) {
  return r.status || (r.in_stock === true ? "in_stock" : r.in_stock === false ? "out_of_stock" : "unknown");
}
function renderResults(data) {
  const results = data.results || data.observations || [];
  $("resultCount").textContent = results.length + " results";
  if (!results.length) {
    const message = data.message || "No eligible retailer checks were configured at the time of the last refresh. No unverified inventory lookups were attempted.";
    $("results").innerHTML = '<div class="empty">'+esc(message)+'</div>';
    return;
  }
  $("results").innerHTML = results.map(r => {
    const status = resultStatus(r);
    const detail = r.note || ("Checked "+fmt(r.checked_at)+(r.quantity !== null && r.quantity !== undefined ? " · Quantity "+r.quantity : ""));
    return '<article class="result"><div><strong>'+esc(r.product)+' · '+esc(r.store)+
      '</strong><small>'+esc(detail)+'</small></div><span class="pill '+esc(status)+'">'+
      esc(status.replaceAll("_"," ").toUpperCase())+'</span></article>';
  }).join("");
}
function renderHistory(history) {
  const observations = (history.observations || []).slice().sort((a,b) =>
    new Date(a.checked_at || a.run_at) - new Date(b.checked_at || b.run_at));
  const runs = history.runs || [];
  $("historyCount").textContent = observations.length + " observations";
  $("runCount").textContent = runs.length + " manual runs";
  if (!observations.length) {
    $("historySummary").innerHTML = '<div class="empty">No inventory observations have been recorded yet. History begins after a retailer/product combination is verified and enabled for monitoring.</div>';
    $("historyLog").innerHTML = '<div class="empty">No observation log yet.</div>';
    return;
  }
  const groups = new Map();
  for (const obs of observations) {
    const key = obs.observation_key || [obs.retailer,obs.store,obs.product].join("|");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(obs);
  }
  const cards = [];
  for (const items of groups.values()) {
    const valid = items.filter(x => ["in_stock","out_of_stock"].includes(resultStatus(x)));
    if (!valid.length) continue;
    const last = valid[valid.length-1];
    const lastIn = [...valid].reverse().find(x => resultStatus(x)==="in_stock");
    const lastOut = [...valid].reverse().find(x => resultStatus(x)==="out_of_stock");
    let transition = "Not enough stock changes observed yet";
    if (resultStatus(last)==="out_of_stock" && lastOut) {
      const priorIn = [...valid].reverse().find(x => resultStatus(x)==="in_stock" && new Date(x.checked_at)<new Date(lastOut.checked_at));
      if (priorIn) transition = "Possible sell-through window: "+fmt(priorIn.checked_at)+" → "+fmt(lastOut.checked_at);
    } else if (resultStatus(last)==="in_stock" && lastIn) {
      const priorOut = [...valid].reverse().find(x => resultStatus(x)==="out_of_stock" && new Date(x.checked_at)<new Date(lastIn.checked_at));
      if (priorOut) transition = "Possible restock window: "+fmt(priorOut.checked_at)+" → "+fmt(lastIn.checked_at);
    }
    cards.push('<article class="history-card"><div class="history-card-top"><div><strong>'+esc(last.product)+'</strong><small>'+esc(last.store)+'</small></div><span class="pill '+esc(resultStatus(last))+'">'+esc(resultStatus(last).replaceAll("_"," ").toUpperCase())+'</span></div>'+
      '<div class="history-facts"><div><span>LAST SEEN IN STOCK</span><b>'+fmt(lastIn?.checked_at)+'</b></div><div><span>LAST SEEN OUT OF STOCK</span><b>'+fmt(lastOut?.checked_at)+'</b></div></div>'+
      '<p class="transition">'+esc(transition)+'</p></article>');
  }
  $("historySummary").innerHTML = cards.length ? cards.join("") : '<div class="empty">No confirmed in-stock or out-of-stock observations yet. Unknown and error responses are retained in the log but are not treated as stock events.</div>';
  const recent = observations.slice().reverse().slice(0,20);
  $("historyLog").innerHTML = recent.map(o => {
    const status = resultStatus(o);
    const quantity = o.quantity === null || o.quantity === undefined ? "Quantity unavailable" : "Reported quantity: "+o.quantity;
    return '<article class="history-event"><div><strong>'+esc(o.product)+' · '+esc(o.store)+'</strong><small>'+fmt(o.checked_at || o.run_at)+' · '+esc(quantity)+(o.note?" · "+esc(o.note):"")+'</small></div><span class="pill '+esc(status)+'">'+esc(status.replaceAll("_"," ").toUpperCase())+'</span></article>';
  }).join("");
}
async function loadDashboard() {
  try {
    const [productsResponse, storesResponse, latestResponse, historyResponse] = await Promise.all([
      fetch("products.json?v="+stamp(), {cache:"no-store"}),
      fetch("stores.json?v="+stamp(), {cache:"no-store"}),
      fetch("latest.json?v="+stamp(), {cache:"no-store"}),
      fetch("history.json?v="+stamp(), {cache:"no-store"})
    ]);
    if (!productsResponse.ok || !storesResponse.ok || !latestResponse.ok || !historyResponse.ok) throw new Error("Dashboard data is not published yet. Wait for the first GitHub Pages deployment.");
    const [products, stores, latest, history] = await Promise.all([
      productsResponse.json(), storesResponse.json(), latestResponse.json(), historyResponse.json()
    ]);
    renderProducts(products);
    renderStores(stores);
    $("eligibleCount").textContent = latest.eligible_checks ?? "—";
    $("lastRefresh").textContent = fmt(latest.generated_at);
    $("productNote").textContent = latest.eligible_checks ? latest.eligible_checks+" eligible product/store checks" : "No verified live checks configured yet";
    renderResults(latest);
    renderHistory(history);
    if (latest.status === "no_eligible_checks") {
      $("refreshHint").textContent = "No verified product/store combinations are enabled yet. You can still run Refresh All; it will safely report zero checks.";
    }
  } catch (error) {
    $("products").innerHTML = '<div class="empty error">'+esc(error.message)+'</div>';
  }
}
loadDashboard();
})();
