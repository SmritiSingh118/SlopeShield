"use strict";

/* ==========================================================
   SlopeShield frontend logic

   Flow:  loadData() -> drawMap() -> user picks places -> findRoute() -> drawRoute()
   The backend (python main.py --serve --port 8000) does all the maths.
   This file only fetches JSON and draws it.
   ========================================================== */

// ---- 1. Settings ------------------------------------------------------
// Change this if your backend runs on another address or port.
const API_BASE = "http://127.0.0.1:8000";
// If the backend does not answer within this time, show an error instead of loading forever.
const API_TIMEOUT_MS = 5000;

// Same colours as the CSS variables in style.css
const COLORS = { Low: "#2f9e5b", Moderate: "#e0a800", High: "#ee7d1a", Critical: "#d1322f" };
// Size of the soft "risk zone" circle around each town (metres)
const ZONE_RADIUS_M = { Low: 8000, Moderate: 12000, High: 17000, Critical: 23000 };

// Real road shapes: the backend only knows town positions, so the page asks the free
// OpenStreetMap routing service (OSRM) for the actual road between two towns.
const OSRM_URL = "https://router.project-osrm.org/route/v1/driving";
const OSRM_TIMEOUT_MS = 8000;
const NO_ROAD_SNAP_M = 1500; // if the nearest road is further than this from a town, treat the last part as "on foot"

// The two what-if buttons. These values come from the backend's own test cases.
const HAZARDS = {
  cloudburst: { type: "NODE", target: "RUDR", score: 77.08, level: "Critical", label: "Cloudburst at Rudraprayag" },
  gorge:      { type: "EDGE", target: "R10",  score: 82.0,  level: "Critical", label: "Rudraprayag–Chamoli road blocked" },
};

// The 7 standard journeys shown in the corridors table.
// We fetch each one with /api/route, which only reads data.
// (Do NOT use /api/routes here: that endpoint re-saves data/route_output.json on every call,
//  and VS Code Live Server reloads the page whenever a file changes, causing an endless reload loop.)
const CORRIDORS = [["RISH", "BADR"], ["RISH", "KEDN"], ["RISH", "GANG"], ["KEDN", "BADR"], ["RISH", "UTTK"], ["DEHR", "MUSS"], ["CHAM", "MALP"]];

// ---- 2. App state -----------------------------------------------------
const state = {
  locations: [],     // towns from /api/locations
  roads: [],         // roads from /api/roads
  routes: {},        // the 7 corridor comparisons (from /api/route)
  hazards: [],       // hazards the user has switched on (kept so we can show them)
  offline: false,    // true when the backend can't be reached and we use saved data
  lastPair: null,    // [from, to] of the last route shown, so we can redraw it
};

// ---- 3. Small helpers -------------------------------------------------
const $ = (selector) => document.querySelector(selector);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// The backend handles one connection at a time, so we are gentle with it:
// requests go out ONE AT A TIME (a queue), and a request that times out is retried once.
let apiQueue = Promise.resolve();

async function fetchJson(path) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(API_BASE + path, { signal: ctrl.signal });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
  } catch (err) {
    if (err && err.name === "AbortError") throw new Error("the backend did not answer within " + API_TIMEOUT_MS / 1000 + " seconds");
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function api(path) {
  const run = async () => {
    try { return await fetchJson(path); }
    catch (err) {
      await new Promise((r) => setTimeout(r, 400)); // short pause, then one more try
      return fetchJson(path);
    }
  };
  const result = apiQueue.then(run, run);
  apiQueue = result.catch(() => {});
  return result;
}

// Notices: small messages shown in the yellow/red bar above the planner.
// Each has a key, so different problems (map, data, script) can show at once.
const notices = {};
const RETRY = ' <button class="btn btn-quiet" type="button" data-retry>Reload page</button>';
function setNotice(key, html, isError) {
  if (html) notices[key] = { html, isError: Boolean(isError) };
  else delete notices[key];
  const el = $("#banner");
  const items = Object.values(notices);
  el.innerHTML = items.map((n) => `<div>${n.html}</div>`).join("");
  el.classList.toggle("error", items.some((n) => n.isError));
  el.hidden = items.length === 0;
}

// Attach an event listener, but don't crash the whole page if an element is missing.
function on(selector, eventName, handler) {
  const el = $(selector);
  if (!el) { console.warn("SlopeShield: element not found:", selector); return; }
  el.addEventListener(eventName, handler);
}

// Show any unexpected script error on the page, so problems are never silent.
window.addEventListener("error", (e) => {
  setNotice("script", `Script error: <code>${esc(e.message)}</code> (app.js line ${esc(e.lineno)}). Press F12 and open the Console tab for details.`, true);
});
window.addEventListener("unhandledrejection", (e) => {
  const msg = e.reason && e.reason.message ? e.reason.message : String(e.reason);
  setNotice("script", `Script error: <code>${esc(msg)}</code>. Press F12 and open the Console tab for details.`, true);
});

const km = (n) => Number(n).toFixed(1) + " km";
const nameOf = (id) => (state.locations.find((l) => l.location_id === id) || {}).name || id;

// ---- 4. Hero animation (cloudburst scenario) --------------------------
const SCENARIO_TEXT = {
  normal: "Normal day: Rishikesh to Kedarnath goes through Rudraprayag, 233 km.",
  cloudburst: "Cloudburst at Rudraprayag: the safest route switches to Uttarkashi, 88 km longer but 79.8% lower risk.",
};
let scenarioTimer = null;

function setScenario(name) {
  $("#scenario").dataset.state = name;
  $("#scenario-text").textContent = SCENARIO_TEXT[name];
}
function playScenario() {
  clearTimeout(scenarioTimer);
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) { setScenario("cloudburst"); return; }
  setScenario("normal");
  scenarioTimer = setTimeout(() => setScenario("cloudburst"), 1800);
}

// ---- 5a. Real road shapes (OSRM) ---------------------------------------
// The backend gives us only the towns' positions. Joining them with straight lines
// cuts across forests and mountains, so for each pair of neighbouring towns we fetch the
// real road shape once, and keep it (in memory and in localStorage) so it loads instantly next time.
const GEOM_STORAGE_KEY = "slopeshield_road_shapes_v1";
let geomStore = {};
try { geomStore = JSON.parse(localStorage.getItem(GEOM_STORAGE_KEY) || "{}"); } catch (err) { geomStore = {}; }
function saveGeomStore() {
  try { localStorage.setItem(GEOM_STORAGE_KEY, JSON.stringify(geomStore)); } catch (err) { /* storage full or blocked: fine */ }
}

let osrmDown = false;      // becomes true after repeated failures, so we stop retrying
let osrmFailures = 0;
let osrmQueue = Promise.resolve();
const round4 = (n) => Math.round(n * 10000) / 10000;
const townById = (id) => state.locations.find((l) => l.location_id === id);

// Run network lookups one at a time with a short gap (the public service is shared, so be polite).
function queueOsrm(task) {
  const result = osrmQueue.then(task, task);
  osrmQueue = result.catch(() => {}).then(() => new Promise((r) => setTimeout(r, 120)));
  return result;
}

async function requestRoadShape(first, second) {
  const a = townById(first), b = townById(second);
  if (!a || !b) return null;
  const url = `${OSRM_URL}/${a.lon},${a.lat};${b.lon},${b.lat}?overview=full&geometries=geojson`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), OSRM_TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.code !== "Ok" || !data.routes || !data.routes.length) throw new Error("no road found");
    return {
      c: data.routes[0].geometry.coordinates.map(([lon, lat]) => [round4(lat), round4(lon)]),
      s: Math.round(data.waypoints[0].distance), // metres from the first town to the nearest road
      e: Math.round(data.waypoints[1].distance), // metres from the second town to the nearest road
    };
  } finally {
    clearTimeout(timer);
  }
}

// Returns { coords, snapStart, snapEnd } for the road from town idA to town idB, or null if unavailable.
async function roadShape(idA, idB) {
  const [first, second] = idA < idB ? [idA, idB] : [idB, idA];
  const key = first + "|" + second;
  if (!geomStore[key]) {
    if (osrmDown) return null;
    try {
      const rec = await queueOsrm(async () => geomStore[key] || requestRoadShape(first, second));
      if (!rec) return null;
      geomStore[key] = rec;
      saveGeomStore();
      osrmFailures = 0;
    } catch (err) {
      osrmFailures += 1;
      if (osrmFailures >= 2) osrmDown = true;
      return null;
    }
  }
  const rec = geomStore[key];
  return idA === first
    ? { coords: rec.c, snapStart: rec.s, snapEnd: rec.e }
    : { coords: [...rec.c].reverse(), snapStart: rec.e, snapEnd: rec.s };
}

// Turn a list of town ids into one continuous line that follows the roads.
// Also returns "gaps": short links where a town has no road nearby (reached on foot).
async function buildRoadLine(pathIds) {
  const coords = [], gaps = [];
  let approximate = false;
  for (let i = 0; i < pathIds.length - 1; i++) {
    const a = townById(pathIds[i]), b = townById(pathIds[i + 1]);
    if (!a || !b) continue;
    const shape = await roadShape(pathIds[i], pathIds[i + 1]);
    if (!shape) {                       // service unavailable: fall back to a straight line
      approximate = true;
      if (!coords.length) coords.push([a.lat, a.lon]);
      coords.push([b.lat, b.lon]);
      continue;
    }
    if (shape.snapStart > NO_ROAD_SNAP_M) gaps.push([[a.lat, a.lon], shape.coords[0]]);
    if (shape.snapEnd > NO_ROAD_SNAP_M) gaps.push([[b.lat, b.lon], shape.coords[shape.coords.length - 1]]);
    for (const p of (coords.length ? shape.coords.slice(1) : shape.coords)) coords.push(p);
  }
  return { coords, gaps, approximate };
}

function setMapNote(text) {
  const el = $(".map-note");
  if (!el) return;
  el.textContent = text || (osrmDown
    ? "Road shapes are not available right now (the routing service could not be reached), so lines join towns directly and are only approximate."
    : "Road shapes come from OpenStreetMap (via the OSRM routing service). Thin lines show each road's risk level. A dotted link means there is no road, so that part is on foot.");
}

// ---- 5. Map setup -----------------------------------------------------
let map, roadLayer, zoneLayer, townLayer, routeLayer;

// Leaflet is loaded from unpkg in index.html. If that fails (slow or blocked network),
// try two other CDNs before giving up.
const LEAFLET_MIRRORS = [
  ["https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css", "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"],
  ["https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css", "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"],
];
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error("could not load " + src));
    document.head.appendChild(s);
  });
}
function loadCss(href) {
  const l = document.createElement("link");
  l.rel = "stylesheet";
  l.href = href;
  document.head.appendChild(l);
}
async function ensureLeaflet() {
  if (typeof L !== "undefined") return true;
  for (const [css, js] of LEAFLET_MIRRORS) {
    try {
      loadCss(css);
      await loadScript(js);
      if (typeof L !== "undefined") return true;
    } catch (err) { /* try the next mirror */ }
  }
  return false;
}

// Never throws. Returns true if the map is ready.
async function setupMap() {
  try {
    if (!(await ensureLeaflet())) throw new Error("the Leaflet map library could not be downloaded");
    initMap();
    return true;
  } catch (err) {
    map = null;
    setNotice("map", `The map could not start: <code>${esc(err.message)}</code>. Check your internet connection and reload. Route comparison below still works without the map.`, true);
    return false;
  }
}

function initMap() {
  map = L.map("map", { scrollWheelZoom: false }).setView([30.45, 79.3], 8);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  // Road shapes arrive a little later than the towns, so give them their own "panes"
  // (drawing levels): roads at the bottom, then zones and towns, then routes on top.
  map.createPane("roads");  map.getPane("roads").style.zIndex = 380;
  map.createPane("routes"); map.getPane("routes").style.zIndex = 450;
  roadLayer = L.layerGroup().addTo(map);
  zoneLayer = L.layerGroup().addTo(map);
  townLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);

  // Don't hijack page scrolling: wheel-zoom only after the map is clicked.
  map.on("click", () => map.scrollWheelZoom.enable());
  map.on("mouseout", () => map.scrollWheelZoom.disable());

  // If Leaflet's stylesheet failed to load, the map looks blank. Load a backup copy.
  try {
    const pane = document.querySelector(".leaflet-pane");
    if (pane && window.getComputedStyle(pane).position !== "absolute") loadCss(LEAFLET_MIRRORS[0][0]);
  } catch (err) { /* ignore */ }
}

// A hazard on a town overrides its colour locally, because /api/locations
// does not report node hazards back.
function effectiveTown(town) {
  const hazard = state.hazards.find((h) => h.type === "NODE" && h.target === town.location_id);
  if (!hazard) return { ...town, simulated: false };
  return { ...town, risk_level: hazard.level, risk_score: hazard.score, simulated: true };
}

function popupHtml(t) {
  const w = t.weather || {};
  const rows = [
    ["Risk", `<span class="badge ${esc(t.risk_level)}">${esc(t.risk_level)}</span> ${Number(t.risk_score).toFixed(1)} / 100${t.simulated ? " (simulated)" : ""}`],
    ["Elevation", t.elevation_m != null ? Math.round(t.elevation_m) + " m" : "n/a"],
    ["Slope", t.slope_deg != null ? t.slope_deg + "°" : "n/a"],
    ["Past landslides", t.historical_count ?? "n/a"],
    ["Road condition", t.road_condition ?? "n/a"],
  ];
  if (w.current_rain_mm != null) {
    rows.push(["Rain now", w.current_rain_mm + " mm"], ["Forecast 24h", w.forecast_24h_mm + " mm"]);
  }
  const body = rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${k === "Risk" ? v : esc(v)}</td></tr>`).join("");
  return `<div class="popup"><h4>${esc(t.name)}</h4><table>${body}</table></div>`;
}

function drawMap() {
  if (!map) return;
  roadLayer.clearLayers();
  zoneLayer.clearLayers();
  townLayer.clearLayers();

  const byId = {};
  state.locations.forEach((l) => { byId[l.location_id] = l; });

  // Roads are drawn after their real shapes arrive (see drawRoads below).
  drawRoads();

  // Risk zones (soft circles) and town markers
  state.locations.map(effectiveTown).forEach((t) => {
    const colour = COLORS[t.risk_level] || "#888";
    L.circle([t.lat, t.lon], {
      radius: ZONE_RADIUS_M[t.risk_level] || 8000, color: colour, weight: 0, fillColor: colour, fillOpacity: 0.2,
      interactive: false,
    }).addTo(zoneLayer);

    L.circleMarker([t.lat, t.lon], {
      radius: 9, color: "#fff", weight: 2.5, fillColor: colour, fillOpacity: 1,
    }).bindPopup(popupHtml(t))
      .bindTooltip(t.name, { permanent: true, direction: "right", offset: [8, 0], className: "town-label" })
      .addTo(townLayer);
  });
}

let roadsToken = 0;
async function drawRoads() {
  const token = ++roadsToken;           // a newer drawRoads() call cancels this one
  const byId = {};
  state.locations.forEach((l) => { byId[l.location_id] = l; });

  // The API may list a road in both directions, so skip duplicates.
  const seen = new Set();
  const roads = state.roads.filter((r) => {
    const key = [r.from_id, r.to_id].sort().join("-");
    if (seen.has(key) || !byId[r.from_id] || !byId[r.to_id]) return false;
    seen.add(key);
    return true;
  });
  if (roads.length) setMapNote("Loading road shapes…");

  for (const r of roads) {
    const shape = await roadShape(r.from_id, r.to_id);
    if (token !== roadsToken) return;
    const a = byId[r.from_id], b = byId[r.to_id];
    const points = shape ? shape.coords : [[a.lat, a.lon], [b.lat, b.lon]];
    L.polyline(points, {
      pane: "roads", color: COLORS[r.edge_risk_level] || "#888", weight: 3, opacity: 0.8,
      dashArray: shape ? null : "6 6",
    }).bindTooltip(`${esc(r.highway)}: ${r.distance_km} km, ${esc(r.edge_risk_level)} risk`, { sticky: true })
      .addTo(roadLayer);
  }
  if (token === roadsToken) setMapNote();
}

function fitToTowns() {
  if (!map) return;
  const pts = state.locations.map((l) => [l.lat, l.lon]);
  if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.12));
}

// ---- 6. Routes --------------------------------------------------------
let routeToken = 0;
async function drawRoute(r) {
  if (!map) return;
  const token = ++routeToken;           // if the user clicks again while shapes load, ignore the old one
  routeLayer.clearLayers();
  const safe = r.safest_route, short = r.shortest_route;
  if (!safe || !safe.found) return;

  const safeLine = await buildRoadLine(safe.path);
  const shortLine = (!r.is_identical && short && short.found) ? await buildRoadLine(short.path) : null;
  if (token !== routeToken) return;

  const gapStyle = { pane: "routes", color: "#6b7788", weight: 3, dashArray: "2 8", lineCap: "round" };
  const drawGaps = (line) => line.gaps.forEach((g) =>
    L.polyline(g, gapStyle).bindTooltip("No road here: reached on foot", { sticky: true }).addTo(routeLayer));

  if (shortLine) {
    L.polyline(shortLine.coords, { pane: "routes", color: "#6b7788", weight: 5, opacity: 0.95, dashArray: "2 10", lineCap: "round" })
      .bindTooltip("Shortest route: " + km(short.total_distance_km), { sticky: true })
      .addTo(routeLayer);
    drawGaps(shortLine);
  }
  // white outline first, then the teal line on top, so it stays visible on any map colour
  L.polyline(safeLine.coords, { pane: "routes", color: "#fff", weight: 11, opacity: 0.9 }).addTo(routeLayer);
  L.polyline(safeLine.coords, { pane: "routes", color: "#0a8f8a", weight: 6, opacity: 1 })
    .bindTooltip("Safest route: " + km(safe.total_distance_km), { sticky: true })
    .addTo(routeLayer);
  drawGaps(safeLine);

  map.fitBounds(L.latLngBounds(safeLine.coords.concat(...safeLine.gaps)).pad(0.2));
  setMapNote();
}

function renderResult(r) {
  const box = $("#result");
  const safe = r.safest_route, short = r.shortest_route;

  if (!safe || !safe.found) {
    box.innerHTML = `<p class="result-head">No route found between these places.</p>`;
    return;
  }

  const pathText = (route) => esc((route.path_names || route.path).join(" → "));
  const badge = (lvl) => `<span class="badge ${esc(lvl)}">${esc(lvl)}</span>`;

  let headline, facts = "";
  if (r.is_identical) {
    headline = `<p class="result-head same">${esc(r.recommendation)}</p>`;
  } else {
    headline = `<p class="result-head">${esc(r.recommendation)}</p>`;
    facts = `<ul class="facts">
      <li>Extra distance: <strong>+${Number(r.distance_diff_km).toFixed(1)} km</strong></li>
      <li>Risk reduced by: <strong>${Number(r.risk_reduction_pct).toFixed(1)}%</strong></li>
    </ul>`;
  }

  box.innerHTML = `
    ${headline}
    <table class="compare">
      <thead><tr><th></th><th scope="col">Shortest</th><th scope="col" class="safe-col">Safest</th></tr></thead>
      <tbody>
        <tr><th scope="row">Distance</th><td>${km(short.total_distance_km)}</td><td class="safe-col">${km(safe.total_distance_km)}</td></tr>
        <tr><th scope="row">Risk cost</th><td>${Number(short.total_risk_cost).toFixed(0)}</td><td class="safe-col">${Number(safe.total_risk_cost).toFixed(0)}</td></tr>
        <tr><th scope="row">Highest risk</th><td>${badge(short.max_risk_level)}</td><td>${badge(safe.max_risk_level)}</td></tr>
        <tr><th scope="row">Route</th><td class="path">${pathText(short)}</td><td class="path">${pathText(safe)}</td></tr>
      </tbody>
    </table>
    ${facts}`;
}

async function findRoute(from, to) {
  const box = $("#result");
  if (!from || !to || from === to) {
    box.innerHTML = `<p class="result-head">Choose two different places.</p>`;
    return;
  }
  state.lastPair = [from, to];
  box.innerHTML = `<p class="empty">Finding routes…</p>`;

  try {
    let r;
    if (state.offline) {
      // Offline: only the saved corridors exist
      r = state.routes[`${from}_to_${to}`] || state.routes[`${to}_to_${from}`];
      if (!r) {
        box.innerHTML = `<p class="result-head">Offline mode only has the seven saved corridors.</p>
          <p class="small">Start the backend to compare any two places.</p>`;
        if (map) routeLayer.clearLayers();
        return;
      }
    } else {
      r = await api(`/api/route?source=${encodeURIComponent(from)}&dest=${encodeURIComponent(to)}`);
    }
    renderResult(r);
    drawRoute(r);
  } catch (err) {
    box.innerHTML = `<p class="result-head">Couldn't load this route.</p>
      <p class="small">Check that the backend is running at ${esc(API_BASE)}, then try again.</p>`;
  }
}

// ---- 7. Hazard simulator ----------------------------------------------
function renderHazards() {
  const el = $("#active-hazards");
  if (state.hazards.length === 0) {
    el.textContent = "No hazards active.";
    el.classList.remove("on");
  } else {
    el.textContent = "Active: " + state.hazards.map((h) => h.label).join("; ") + ".";
    el.classList.add("on");
  }
}

async function loadCorridors() {
  const routes = {};
  for (const [s, d] of CORRIDORS) {            // one by one, not all at once
    routes[`${s}_to_${d}`] = await api(`/api/route?source=${s}&dest=${d}`);
  }
  return routes;
}

// Fetch everything the page needs from the backend, one request at a time.
async function fetchLiveData() {
  const loc = await api("/api/locations");
  const roads = await api("/api/roads");
  const routes = await loadCorridors();
  return { locations: loc.locations, roads: roads.roads, routes };
}

async function refreshMapData() {
  const data = await fetchLiveData();
  state.locations = data.locations;
  state.roads = data.roads;
  state.routes = data.routes;
  drawMap();
  renderCorridors();
}

async function applyHazard(key) {
  const h = HAZARDS[key];
  if (state.hazards.some((x) => x.target === h.target)) return; // already on
  try {
    await api(`/api/simulate?override_type=${h.type}&target=${h.target}&score=${h.score}&level=${h.level}`);
    setNotice("action", "");
    state.hazards.push(h);
    renderHazards();
    await refreshMapData();
    if (state.lastPair) await findRoute(...state.lastPair);
  } catch (err) {
    setNotice("action", `Couldn't apply the hazard: <code>${esc(err.message)}</code>. Check that the backend is running.`, true);
  }
}

async function resetHazards() {
  try {
    await api("/api/simulate/reset");
    state.hazards = [];
    renderHazards();
    await refreshMapData();
    if (state.lastPair) await findRoute(...state.lastPair);
  } catch (err) {
    setNotice("action", `Couldn't reset the hazards: <code>${esc(err.message)}</code>. Check that the backend is running.`, true);
  }
}

// ---- 8. Corridor table -------------------------------------------------
function renderCorridors() {
  const body = $("#corridor-rows");
  const list = Object.values(state.routes);
  if (list.length === 0) {
    body.innerHTML = `<tr><td colspan="6" class="empty">No corridors available.</td></tr>`;
    return;
  }
  body.innerHTML = list.map((r) => {
    const names = r.shortest_route.path_names || [];
    const title = `${names[0] || r.source_id} to ${names[names.length - 1] || r.dest_id}`;
    const extra = r.is_identical ? "None" : "+" + Number(r.distance_diff_km).toFixed(1) + " km";
    const risk = r.is_identical ? "Already safest" : Number(r.risk_reduction_pct).toFixed(1) + "%";
    return `<tr>
      <td>${esc(title)}</td>
      <td class="num">${km(r.shortest_route.total_distance_km)}</td>
      <td class="num">${km(r.safest_route.total_distance_km)}</td>
      <td class="num">${esc(extra)}</td>
      <td class="num ${r.is_identical ? "" : "good"}">${esc(risk)}</td>
      <td><button class="row-btn" type="button" data-from="${esc(r.source_id)}" data-to="${esc(r.dest_id)}">Show on map</button></td>
    </tr>`;
  }).join("");
}

// ---- 9. Loading data ---------------------------------------------------
async function loadData() {
  try {
    const data = await fetchLiveData();
    state.locations = data.locations;
    state.roads = data.roads;
    state.routes = data.routes;
    state.offline = false;
    setNotice("data", "");
  } catch (err) {
    // Backend not reachable: fall back to the saved file in frontend/data/
    try {
      const res = await fetch("data/route_output.json");
      if (!res.ok) throw new Error("no saved data");
      const saved = await res.json();
      state.locations = Object.values(saved.all_locations);
      state.roads = [];
      state.routes = saved.routes;
      state.offline = true;
      setNotice("data", `Couldn't reach the backend (<code>${esc(err.message)}</code>), so this page is showing saved results. Start it with <code>python main.py --serve --port 8000</code> and reload for live routes and hazard tests.${RETRY}`, false);
    } catch (err2) {
      setNotice("data", `Couldn't reach the backend at <code>${esc(API_BASE)}</code> (<code>${esc(err.message)}</code>). Start it with <code>python main.py --serve --port 8000</code>, then reload this page.${RETRY}`, true);
      throw err2;
    }
  }
}

function fillSelects() {
  const sorted = [...state.locations].sort((a, b) => a.name.localeCompare(b.name));
  const options = sorted.map((l) => `<option value="${esc(l.location_id)}">${esc(l.name)}</option>`).join("");
  ["#from", "#to"].forEach((id) => { $(id).innerHTML = options; $(id).disabled = false; });
  $("#from").value = "RISH";
  $("#to").value = "KEDN";
  $("#go").disabled = false;
}

// ---- 10. Wire up the page ----------------------------------------------
function bindEvents() {
  on("#replay", "click", playScenario);
  on("#banner", "click", (e) => { if (e.target.closest("[data-retry]")) location.reload(); });

  on("#route-form", "submit", (e) => {
    e.preventDefault();
    findRoute($("#from").value, $("#to").value);
  });
  on("#swap", "click", () => {
    const a = $("#from").value;
    $("#from").value = $("#to").value;
    $("#to").value = a;
    findRoute($("#from").value, $("#to").value);
  });
  document.querySelectorAll("[data-hazard]").forEach((btn) => {
    btn.addEventListener("click", () => applyHazard(btn.dataset.hazard));
  });
  on("#reset", "click", resetHazards);

  // "Show on map" buttons in the corridor table
  on("#corridor-rows", "click", (e) => {
    const btn = e.target.closest("button[data-from]");
    if (!btn) return;
    $("#from").value = btn.dataset.from;
    $("#to").value = btn.dataset.to;
    findRoute(btn.dataset.from, btn.dataset.to);
    $("#planner").scrollIntoView({ behavior: "smooth" });
  });
}

async function start() {
  bindEvents();      // buttons first, so they always work
  playScenario();

  // Load the map and the data at the same time. A problem with one must not stop the other.
  const [mapOk, dataOk] = await Promise.all([
    setupMap(),
    loadData().then(() => true, () => false),
  ]);
  if (!dataOk) return; // the notice already explains what to do

  if (state.offline) {
    document.querySelectorAll("[data-hazard], #reset").forEach((b) => { b.disabled = true; });
  }
  fillSelects();
  renderCorridors();
  renderHazards();
  if (mapOk) { drawMap(); fitToTowns(); }
  findRoute("RISH", "KEDN");
}

document.addEventListener("DOMContentLoaded", start);
