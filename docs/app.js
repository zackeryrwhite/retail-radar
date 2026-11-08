(() => {
const API = (window.RETAIL_RADAR_API || "").replace(/\/$/, "");
const $ = (id) => document.getElementById(id);
let password = sessionStorage.getItem("rr_password") || "";
let lastResults = [];

function authHeaders(json=false) {
  const headers = { Authorization: "Basic " + btoa("retail-radar:" + password) };
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}
async function api(path, options={}) {
  if (!API) throw new Error("Dashboard API URL has not been configured yet.");
  const response = await fetch(API + path, {...options, headers: {...authHeaders(!!options.body), ...(options.headers || {})}});
  if (response.status === 401) { sessionStorage.removeItem("rr_password"); password=""; $("login").classList.remove("hidden"); throw new Error("Password not accepted. Please reconnect."); }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "The server returned an error.");
  return body;
}
function fmt(value) { if (!value) return "Never"; const d=new Date(value); return isNaN(d)?"—":d.toLocaleString([], {month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}); }
function esc(value) { return String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function renderProducts(products) {
  $("productCount").textContent=products.length;
  $("products").innerHTML=products.map((p,i)=>'<article class="product"><span class="product-index">WATCHLIST / '+String(i+1).padStart(2,"0")+'</span><h3>'+esc(p.name)+'</h3><div class="upc">UPC '+esc(p.upc||"Not set")+'</div><div class="status-line">Manual inventory checks only</div></article>').join("");
}
function renderStores(stores) {
  $("stores").innerHTML=stores.map(s=>'<article class="store"><div><strong>'+esc(s.name)+'</strong><small>'+esc(s.address)+'</small></div><span class="store-state '+(s.monitor_enabled&&s.enabled?"ready":"")+'">'+(s.monitor_enabled&&s.enabled?"ENABLED":"DISCOVERY ONLY")+'</span></article>').join("");
}
function renderResults(results) {
  lastResults=results||[];
  $("resultCount").textContent=lastResults.length+" results";
  if (!lastResults.length) { $("results").innerHTML='<div class="empty">No retailer checks were eligible. The dashboard will not guess at product matches or query unverified inventory routes.</div>'; return; }
  $("results").innerHTML=lastResults.map(r=>'<article class="result"><div><strong>'+esc(r.product)+' · '+esc(r.store)+'</strong><small>'+esc(r.note||("Checked "+fmt(r.checked_at)+(r.quantity!==null&&r.quantity!==undefined?" · Quantity "+r.quantity:"")))+'</small></div><span class="pill '+esc(r.status)+'">'+esc(r.status.replaceAll("_"," ").toUpperCase())+'</span></article>').join("");
}
async function loadDashboard() {
  const data=await api("/api/dashboard");
  renderProducts(data.products||[]); renderStores(data.stores||[]);
  $("eligibleCount").textContent=data.eligible_checks ?? "—";
  $("lastRefresh").textContent=fmt(data.last_refresh);
  $("productNote").textContent=data.eligible_checks ? data.eligible_checks+" eligible product/store checks" : "No verified live checks configured yet";
  if (data.last_results?.length) renderResults(data.last_results);
}
async function refreshAll() {
  const button=$("refreshAll"); button.disabled=true; button.innerHTML="<span>↻</span> Checking…";
  $("progress").hidden=false; $("refreshHint").textContent="Contacting eligible retailer endpoints. This only happens because you clicked.";
  try {
    const data=await api("/api/refresh",{method:"POST",body:"{}"});
    renderResults(data.results||[]);
    $("lastRefresh").textContent=fmt(data.generated_at);
    $("eligibleCount").textContent=data.eligible_checks;
    $("refreshHint").textContent=data.status==="no_eligible_checks"?"No eligible retailer checks are configured.":"Finished "+data.eligible_checks+" checks; "+(data.errors||[]).length+" errors.";
    $("productNote").textContent=data.eligible_checks ? data.eligible_checks+" eligible product/store checks" : "No verified live checks configured yet";
  } catch(e) { $("refreshHint").textContent=e.message; $("results").innerHTML='<div class="empty error">'+esc(e.message)+'</div>'; }
  finally {button.disabled=false;button.innerHTML="<span>↻</span> Refresh All";$("progress").hidden=true;}
}
$("refreshAll").addEventListener("click",refreshAll);
$("loginForm").addEventListener("submit",async e=>{
  e.preventDefault(); password=$("password").value; $("loginError").textContent="";
  try { await loadDashboard(); sessionStorage.setItem("rr_password",password); $("login").classList.add("hidden"); }
  catch(err) { $("loginError").textContent=err.message; }
});
if (password) { $("password").value=password; loadDashboard().then(()=>$("login").classList.add("hidden")).catch(()=>{}); }
if (!API) $("loginError").textContent="Deployment setup is required: set the API URL in docs/config.js.";
})();