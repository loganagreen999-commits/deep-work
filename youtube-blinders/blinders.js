/* YouTube Blinders
   The point is a search bar and a player, nothing else. YouTube is a single-page
   app, so the flags go on <html> at document_start (before first paint) and the
   URL is watched for navigations that never reload the document. */
const DEFAULTS = {
  on: true, home: true, side: true, end: true,
  shorts: true, comments: true, nav: true, chrome: true
};
const FLAGS = ["home","side","end","shorts","comments","nav","chrome"];
let cfg = { ...DEFAULTS };

function apply() {
  const el = document.documentElement;
  for (const f of FLAGS) el.setAttribute("data-blinders-" + f, cfg.on && cfg[f] ? "1" : "0");
  el.setAttribute("data-blinders", cfg.on ? "1" : "0");
  paintHome();
}

/* Replace the home feed with a full stop rather than an empty page, so landing
   on youtube.com by reflex gives you nothing to scroll and says why. */
function paintHome() {
  const onHome = location.pathname === "/" || location.pathname === "/feed/trending";
  const host = document.querySelector("ytd-browse[page-subtype='home'], ytd-browse[page-subtype='trending']");
  const existing = document.getElementById("blinders-blank");
  if (!cfg.on || !cfg.home || !onHome || !host) { if (existing) existing.remove(); return; }
  if (existing) return;
  const d = document.createElement("div");
  d.id = "blinders-blank";
  d.innerHTML =
    "<h2>No feed here</h2>" +
    "<p>You came to look something up. The search bar is at the top.</p>" +
    "<p class='k'>Blinders is on. Click the extension icon to turn it off.</p>";
  host.prepend(d);
}

/* The recommendation strip is re-rendered constantly; CSS handles the hiding,
   this only keeps the home placeholder in step with SPA navigation. */
let lastHref = location.href;
function watch() {
  if (location.href !== lastHref) { lastHref = location.href; paintHome(); }
}
setInterval(watch, 400);
document.addEventListener("yt-navigate-finish", paintHome);
new MutationObserver(paintHome).observe(document.documentElement, { childList: true, subtree: true });

chrome.storage.sync.get(DEFAULTS, v => { cfg = { ...DEFAULTS, ...v }; apply(); });
chrome.storage.onChanged.addListener(ch => {
  for (const k in ch) cfg[k] = ch[k].newValue;
  apply();
});
apply();
