const API_BASE = "http://localhost:8000";
const btn = document.getElementById("fetchBtn");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.className = isError ? "error" : "";
}

function card(item) {
  const el = document.createElement("article");
  el.className = "card";
  const h = document.createElement("h2");
  h.textContent = item.title;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = [item.source, item.publishedAt && new Date(item.publishedAt).toLocaleString()]
    .filter(Boolean).join(" · ");
  const s = document.createElement("div");
  s.className = "summary";
  s.textContent = item.simplified;
  el.append(h, meta, s);
  if (item.url) {
    const a = document.createElement("a");
    a.href = item.url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = "Read full article →";
    el.append(a);
  }
  return el;
}

btn.addEventListener("click", async () => {
  btn.disabled = true;
  results.replaceChildren();
  setStatus("Fetching and simplifying the latest news…");
  try {
    const res = await fetch(`${API_BASE}/api/fetch-and-simplify?limit=5`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    results.append(...data.results.map(card));
    setStatus(`Showing ${data.results.length} simplified stories.`);
  } catch (e) {
    setStatus(`Error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
});
