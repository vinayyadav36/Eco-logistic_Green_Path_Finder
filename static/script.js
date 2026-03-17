/**
 * script.js — Main frontend logic for Eco-Logistics Planner
 * Handles form submission, result rendering, map display, CSV export.
 */

'use strict';

/* ------------------------------------------------------------------ */
/* State                                                               */
/* ------------------------------------------------------------------ */
let currentResults = null;
let currentOrigin  = '';
let currentDest    = '';
let leafletMap     = null;
let routeLayer     = null;
let markersLayer   = null;

/* ------------------------------------------------------------------ */
/* DOM References                                                      */
/* ------------------------------------------------------------------ */
const form           = document.getElementById('routeForm');
const originInput    = document.getElementById('origin');
const destInput      = document.getElementById('destination');
const calcBtn        = document.getElementById('calcBtn');
const exportBtn      = document.getElementById('exportBtn');
const loadingEl      = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const errorAlert     = document.getElementById('errorAlert');
const errorMsg       = document.getElementById('errorMsg');
const kpiBest        = document.getElementById('kpiBestMode');
const kpiDistance    = document.getElementById('kpiDistance');
const kpiMinCO2      = document.getElementById('kpiMinCO2');
const kpiTopScore    = document.getElementById('kpiTopScore');
const kpiSavings     = document.getElementById('kpiSavings');
const resultsGrid    = document.getElementById('resultsGrid');
const resultsBody    = document.getElementById('resultsBody');
const offsetIcon     = document.getElementById('offsetIcon');
const offsetTrees    = document.getElementById('offsetTrees');
const offsetDesc     = document.getElementById('offsetDesc');

/* ------------------------------------------------------------------ */
/* Leaflet map initialisation                                          */
/* ------------------------------------------------------------------ */
function initMap(centerLat = 20.5937, centerLng = 78.9629, zoom = 5) {
  if (leafletMap) return;   // already initialised

  leafletMap = L.map('map', {
    center: [centerLat, centerLng],
    zoom: zoom,
    zoomControl: true,
    attributionControl: true,
  });

  // OpenStreetMap tiles (free, no key required)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(leafletMap);

  routeLayer   = L.layerGroup().addTo(leafletMap);
  markersLayer = L.layerGroup().addTo(leafletMap);
}

/* Custom marker icon factory */
function makeIcon(color, label) {
  return L.divIcon({
    className: '',
    html: `<div style="
      background:${color};
      color:#fff;
      border-radius:50%;
      width:30px;height:30px;
      display:flex;align-items:center;justify-content:center;
      font-size:12px;font-weight:700;
      border:2px solid #fff;
      box-shadow:0 2px 6px rgba(0,0,0,.4);
    ">${label}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

/* Decode Google encoded polyline */
function decodePolyline(encoded) {
  const pts = [];
  let index = 0, lat = 0, lng = 0;
  while (index < encoded.length) {
    let b, shift = 0, result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; }
    while (b >= 0x20);
    lat += (result & 1) ? ~(result >> 1) : result >> 1;
    shift = 0; result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; }
    while (b >= 0x20);
    lng += (result & 1) ? ~(result >> 1) : result >> 1;
    pts.push([lat / 1e5, lng / 1e5]);
  }
  return pts;
}

/* Draw route on map */
function drawRoute(results) {
  if (!leafletMap) return;

  routeLayer.clearLayers();
  markersLayer.clearLayers();

  // Find best (first) result with origin/dest coords
  const best = results[0];
  if (!best) return;

  const origin = best.origin_point;
  const dest   = best.destination_point;

  if (origin) {
    markersLayer.addLayer(
      L.marker([origin.lat, origin.lng], { icon: makeIcon('#16a34a', 'A') })
        .bindPopup(`<b>📍 ${currentOrigin}</b>`)
    );
  }

  if (dest) {
    markersLayer.addLayer(
      L.marker([dest.lat, dest.lng], { icon: makeIcon('#dc2626', 'B') })
        .bindPopup(`<b>🏁 ${currentDest}</b>`)
    );
  }

  // Draw polyline for road modes
  const roadResult = results.find(r => r.category === 'road' && r.polyline);
  if (roadResult) {
    const pts = decodePolyline(roadResult.polyline);
    const poly = L.polyline(pts, {
      color: '#16a34a',
      weight: 5,
      opacity: 0.75,
      dashArray: null,
      smoothFactor: 2,
    });
    routeLayer.addLayer(poly);

    // Fit map to route
    leafletMap.fitBounds(poly.getBounds().pad(0.12));
  } else if (origin && dest) {
    // Draw straight dashed line for transit-only results
    const line = L.polyline(
      [[origin.lat, origin.lng], [dest.lat, dest.lng]],
      { color: '#3b82f6', weight: 3, dashArray: '8 6', opacity: 0.65 }
    );
    routeLayer.addLayer(line);
    leafletMap.fitBounds(line.getBounds().pad(0.15));
  }
}

/* ------------------------------------------------------------------ */
/* CO₂ colour helper                                                   */
/* ------------------------------------------------------------------ */
function co2Class(co2, maxCO2) {
  const ratio = co2 / maxCO2;
  if (ratio < 0.35) return 'co2-low';
  if (ratio < 0.70) return 'co2-medium';
  return 'co2-high';
}

/* ------------------------------------------------------------------ */
/* Format duration                                                     */
/* ------------------------------------------------------------------ */
function fmtDuration(min) {
  const totalMin = Math.round(min);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} h`;
  return `${h} h ${m} m`;
}

/* ------------------------------------------------------------------ */
/* Render result cards                                                 */
/* ------------------------------------------------------------------ */
function renderCards(results, bestKey) {
  if (!resultsGrid) return;
  resultsGrid.innerHTML = '';

  results.forEach((r, idx) => {
    const isBest = r.mode_key === bestKey;
    const card = document.createElement('div');
    card.className = `result-card fade-in${isBest ? ' best' : ''}`;
    card.style.animationDelay = `${idx * 0.06}s`;

    card.innerHTML = `
      <div class="result-card-header">
        <div class="result-mode-name">
          <span class="result-mode-icon">${r.mode_icon}</span>
          <span>${r.mode_name}</span>
        </div>
        ${isBest ? '<span class="best-badge">🌿 Greenest</span>' : ''}
      </div>
      <div class="result-card-body">
        <div class="result-metrics">
          <div class="metric-item">
            <span class="metric-label">Distance</span>
            <span class="metric-value">${r.distance_km.toFixed(1)} km</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Duration</span>
            <span class="metric-value">${fmtDuration(r.duration_min)}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">CO₂</span>
            <span class="metric-value">${r.co2_kg.toFixed(3)} kg</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Cost</span>
            <span class="metric-value">₹${r.cost_inr.toFixed(0)}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Fuel / Energy</span>
            <span class="metric-value" style="font-size:.85rem">${r.fuel_energy_label}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">🌳 Trees/yr</span>
            <span class="metric-value">${r.trees_to_offset.toFixed(2)}</span>
          </div>
        </div>
        <div class="score-bar-container">
          <div class="score-bar-label">
            <span class="score-bar-title">Green Score</span>
            <span class="score-bar-value">${r.green_score.toFixed(1)}</span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" data-score="${r.green_score}" style="width:0; background: linear-gradient(90deg, ${r.color}, ${r.color}aa)"></div>
          </div>
        </div>
      </div>
    `;
    resultsGrid.appendChild(card);
  });

  // Animate score bars
  requestAnimationFrame(() => {
    document.querySelectorAll('.score-bar-fill').forEach(bar => {
      const score = parseFloat(bar.dataset.score);
      bar.style.width = `${score}%`;
    });
  });
}

/* ------------------------------------------------------------------ */
/* Render comparison table                                             */
/* ------------------------------------------------------------------ */
function renderTable(results, bestKey) {
  if (!resultsBody) return;
  resultsBody.innerHTML = '';

  const maxCO2 = Math.max(...results.map(r => r.co2_kg));

  results.forEach(r => {
    const isBest = r.mode_key === bestKey;
    const tr = document.createElement('tr');
    if (isBest) tr.className = 'best-row';

    tr.innerHTML = `
      <td><div class="cell-mode">${r.mode_icon} ${r.mode_name}</div></td>
      <td>${r.distance_km.toFixed(1)} km</td>
      <td>${fmtDuration(r.duration_min)}</td>
      <td>
        <span class="co2-pill ${co2Class(r.co2_kg, maxCO2)}">
          ${r.co2_kg.toFixed(3)} kg
        </span>
      </td>
      <td>${r.fuel_energy_label}</td>
      <td>₹${r.cost_inr.toFixed(0)}</td>
      <td><strong>${r.green_score.toFixed(1)}</strong></td>
      <td>🌳 ${r.trees_to_offset.toFixed(2)}</td>
    `;
    resultsBody.appendChild(tr);
  });
}

/* ------------------------------------------------------------------ */
/* Render KPI cards                                                    */
/* ------------------------------------------------------------------ */
function renderKPIs(results, bestKey) {
  const best   = results.find(r => r.mode_key === bestKey) || results[0];
  const worst  = results[results.length - 1];
  const minCO2 = results.reduce((m, r) => r.co2_kg < m.co2_kg ? r : m, results[0]);

  if (kpiBest)     kpiBest.textContent     = `${best.mode_icon} ${best.mode_name}`;
  if (kpiDistance) kpiDistance.textContent = `${best.distance_km.toFixed(1)} km`;
  if (kpiMinCO2)   kpiMinCO2.textContent   = `${minCO2.co2_kg.toFixed(3)} kg`;
  if (kpiTopScore) kpiTopScore.textContent = `${best.green_score.toFixed(1)}`;

  // CO₂ savings vs worst
  if (kpiSavings && results.length > 1) {
    const saved = (worst.co2_kg - minCO2.co2_kg).toFixed(3);
    kpiSavings.textContent = `${saved} kg`;
  }
}

/* ------------------------------------------------------------------ */
/* Render offset section                                               */
/* ------------------------------------------------------------------ */
function renderOffset(results) {
  const best = results[0];
  if (!best || !offsetTrees) return;

  const trees = best.trees_to_offset;
  offsetTrees.textContent = trees.toFixed(2);

  if (offsetDesc) {
    offsetDesc.textContent =
      `To neutralise the ${best.co2_kg.toFixed(3)} kg CO₂ emitted by the greenest option ` +
      `(${best.mode_name}), you would need to plant and maintain ${Math.ceil(trees)} tree${trees >= 2 ? 's' : ''} ` +
      `for one full year. Choose rail or metro to minimise your footprint! 🌿`;
  }
}

/* ------------------------------------------------------------------ */
/* Show / hide error                                                   */
/* ------------------------------------------------------------------ */
function showError(message) {
  if (errorAlert) errorAlert.classList.remove('hidden');
  if (errorMsg)   errorMsg.textContent = message;
}

function clearError() {
  if (errorAlert) errorAlert.classList.add('hidden');
  if (errorMsg)   errorMsg.textContent = '';
}

/* ------------------------------------------------------------------ */
/* Main form submission                                                */
/* ------------------------------------------------------------------ */
async function handleSubmit(event) {
  event.preventDefault();
  clearError();

  const origin = originInput ? originInput.value.trim() : '';
  const dest   = destInput   ? destInput.value.trim()   : '';

  if (!origin || !dest) {
    showError('Please enter both origin and destination.');
    return;
  }
  if (origin.toLowerCase() === dest.toLowerCase()) {
    showError('Origin and destination must be different locations.');
    return;
  }

  // UI: loading state
  if (calcBtn)  { calcBtn.disabled = true; calcBtn.innerHTML = '<span class="spinner"></span> Calculating…'; }
  if (loadingEl) loadingEl.classList.add('active');
  if (resultsSection) resultsSection.classList.remove('active');

  try {
    const res = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest, modes: [] }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || 'An unexpected error occurred.');
      return;
    }

    // Assign state
    currentResults = data.results;
    currentOrigin  = data.origin;
    currentDest    = data.destination;

    // Render core results first
    renderKPIs(currentResults, data.best_mode_key);
    renderCards(currentResults, data.best_mode_key);
    renderTable(currentResults, data.best_mode_key);
    renderOffset(currentResults);

    // Show results section immediately
    if (resultsSection) {
      resultsSection.classList.add('active');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Enable export
    if (exportBtn) exportBtn.disabled = false;

    // Charts (only if Plotly loaded)
    if (typeof renderAllCharts === 'function' && typeof Plotly !== 'undefined') {
      try { renderAllCharts(currentResults); } catch(e) { console.warn('Charts unavailable:', e.message); }
    }

    // Map (only if Leaflet loaded)
    if (typeof L !== 'undefined') {
      try { initMap(); drawRoute(currentResults); } catch(e) { console.warn('Map unavailable:', e.message); }
    }

  } catch (err) {
    showError('Network error. Please check your connection and try again.');
    console.error(err);
  } finally {
    if (calcBtn)  { calcBtn.disabled = false; calcBtn.innerHTML = '🔍 Find Green Routes'; }
    if (loadingEl) loadingEl.classList.remove('active');
  }
}

/* ------------------------------------------------------------------ */
/* CSV Export                                                          */
/* ------------------------------------------------------------------ */
async function handleExport() {
  if (!currentOrigin || !currentDest) return;

  const res = await fetch('/api/export/csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: currentOrigin,
      destination: currentDest,
      modes: [],
    }),
  });

  if (!res.ok) {
    showError('Failed to export CSV.');
    return;
  }

  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `eco_logistics_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------ */
/* Event listeners                                                     */
/* ------------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', () => {
  // Form submit
  if (form)      form.addEventListener('submit', handleSubmit);
  if (exportBtn) exportBtn.addEventListener('click', handleExport);

  // Enter key on inputs
  [originInput, destInput].forEach(inp => {
    if (inp) {
      inp.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (form) form.requestSubmit();
        }
      });
    }
  });

  // Initialise map with India centre view (lazy: only when needed)
  // Map init is deferred to first search to avoid blank tile flash

  // Disable export btn until results ready
  if (exportBtn) exportBtn.disabled = true;
});
