/* Baraka Market Mini App — light PWA cache (admin/api ga tegmaydi). */
const CACHE = "baraka-mini-v1";
const PRECACHE = [
  "/",
  "/index.html",
  "/styles.css?v=47",
  "/app.js?v=47",
  "/manifest.webmanifest",
  "/pwa-192.png",
  "/pwa-512.png",
  "/favicon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function shouldBypass(url) {
  const p = url.pathname || "";
  return (
    p.startsWith("/admin") ||
    p.startsWith("/api") ||
    p.startsWith("/chek") ||
    p.startsWith("/shajara") ||
    p.startsWith("/ingliz") ||
    p.startsWith("/arduino") ||
    p.startsWith("/slayd") ||
    p.startsWith("/kichkintoy") ||
    p.startsWith("/jadval")
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (shouldBypass(url)) return;

  // HTML — network first
  if (req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("/", copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match("/") || caches.match("/index.html"))
    );
    return;
  }

  // Static — cache first
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      });
    })
  );
});
