(() => {
const $ = (id) => document.getElementById(id);
const stamp = () => Date.now();
function fmt(value) {
  if (!value) return "Never";
  const d = new Date(value);
  return isNaN(d) ? "—" : d.toLocaleString([], {month:"short",day:"numeric",hour:"numeric",minute:"2-digit"});
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
function renderResults(data) {
  const results = data.results || data.observations || [];
  $("resultCount").textContent = results.length + " results";
  if (!results.length) {
    const message = data.message || "No eligible retailer checks were configured at the time of the last refresh. No unverified inventory lookups were attempted.";
    $("results").innerHTML = '<div class="empty">'+esc(message)+'</div>';
    return;
  }
  $("results").innerHTML = results.map(r => {
    const status = r.status || (r.in_stock === true ? "in_stock" : r.in_stock === false ? "out_of_stock" : "unknown");
    const detail = r.note || ("Checked "+fmt(r.checked_at)+(r.quantity !== null && r.quantity !== undefined ? " · Quantity "+r.quantity : ""));
    return '<article class="result"><div><strong>'+esc(r.product)+' · '+esc(r.store)+
      '</strong><small>'+esc(detail)+'</small></div><span class="pill '+esc(status)+'">'+
      esc(status.replaceAll("_"," ").toUpperCase())+'</span></article>';
  }).join("");
}
async function loadDashboard() {
  try {
    const [productsResponse, storesResponse, latestResponse] = await Promise.all([
      fetch("products.json?v="+stamp(), {cache:"no-store"}),
      fetch("stores.json?v="+stamp(), {cache:"no-store"}),
      fetch("latest.json?v="+stamp(), {cache:"no-store"})
    ]);
    if (!productsResponse.ok || !storesResponse.ok || !latestResponse.ok) throw new Error("Dashboard data is not published yet. Wait for the first GitHub Pages deployment.");
    const [products, stores, latest] = await Promise.all([
      productsResponse.json(), storesResponse.json(), latestResponse.json()
    ]);
    renderProducts(products);
    renderStores(stores);
    $("eligibleCount").textContent = latest.eligible_checks ?? "—";
    $("lastRefresh").textContent = fmt(latest.generated_at);
    $("productNote").textContent = latest.eligible_checks ? latest.eligible_checks+" eligible product/store checks" : "No verified live checks configured yet";
    renderResults(latest);
    if (latest.status === "no_eligible_checks") {
      $("refreshHint").textContent = "No verified product/store combinations are enabled yet. You can still run Refresh All; it will safely report zero checks.";
    }
  } catch (error) {
    $("products").innerHTML = '<div class="empty error">'+esc(error.message)+'</div>';
  }
}
loadDashboard();
})();
