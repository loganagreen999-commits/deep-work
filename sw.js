/* Deep Work service worker — the app must start with no network at all. */
const V = "deep-work-v1";
const SHELL = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icon-180.png", "./icon-192.png", "./icon-512.png", "./icon-512-maskable.png",
  "./fonts/Fraunces-400.woff2", "./fonts/IBMPlexSans-400.woff2",
  "./fonts/IBMPlexMono-400.woff2", "./fonts/IBMPlexMono-500.woff2"
];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  if (req.mode === "navigate") {
    e.respondWith(fetch(req)
      .then(res => { const c = res.clone(); caches.open(V).then(x => x.put("./index.html", c)); return res })
      .catch(() => caches.match("./index.html").then(r => r || caches.match("./"))));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res && res.status === 200) { const c = res.clone(); caches.open(V).then(x => x.put(req, c)) }
    return res;
  })));
});
