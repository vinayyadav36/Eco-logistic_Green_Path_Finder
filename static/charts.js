/**
 * charts.js — Plotly chart rendering for Eco-Logistics Planner
 * Renders CO₂ comparison bar chart and Green Score radar/bar chart.
 */

/* ------------------------------------------------------------------ */
/* Shared Plotly layout defaults                                        */
/* ------------------------------------------------------------------ */
const PLOTLY_FONT = {
  family: "'Inter', 'Segoe UI', system-ui, sans-serif",
  size: 12,
  color: '#4b5563',
};

const PLOTLY_LAYOUT_BASE = {
  font: PLOTLY_FONT,
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor:  'rgba(0,0,0,0)',
  margin: { t: 30, r: 20, b: 60, l: 55 },
  showlegend: false,
  xaxis: {
    tickfont: { size: 10, color: '#6b7280' },
    gridcolor: '#f3f4f6',
    linecolor: '#e5e7eb',
    tickangle: -25,
  },
  yaxis: {
    tickfont: { size: 11, color: '#6b7280' },
    gridcolor: '#f3f4f6',
    linecolor: '#e5e7eb',
    zeroline: false,
  },
  hoverlabel: {
    bgcolor: '#1f2937',
    bordercolor: '#374151',
    font: { color: '#f9fafb', size: 12 },
  },
};

const PLOTLY_CONFIG = {
  responsive: true,
  displayModeBar: false,
  scrollZoom: false,
};

/* ------------------------------------------------------------------ */
/* Chart 1: CO₂ Emissions Comparison Bar Chart                         */
/* ------------------------------------------------------------------ */
function renderCO2Chart(results) {
  const el = document.getElementById('co2Chart');
  if (!el || !results || results.length === 0) return;

  const labels = results.map(r => r.mode_name);
  const values = results.map(r => r.co2_kg);
  const colors = results.map(r => r.color);

  // Add subtle gradient-like colour adjustment per bar
  const trace = {
    x: labels,
    y: values,
    type: 'bar',
    marker: {
      color: colors,
      opacity: 0.88,
      line: { color: colors.map(c => c), width: 1.5 },
    },
    hovertemplate: '<b>%{x}</b><br>CO₂: %{y:.3f} kg<extra></extra>',
    text: values.map(v => v.toFixed(3) + ' kg'),
    textposition: 'outside',
    textfont: { size: 10, color: '#374151' },
    cliponaxis: false,
  };

  const layout = {
    ...PLOTLY_LAYOUT_BASE,
    title: { text: '', font: { size: 13 } },
    yaxis: {
      ...PLOTLY_LAYOUT_BASE.yaxis,
      title: { text: 'CO₂ (kg)', font: { size: 11 }, standoff: 8 },
    },
    bargap: 0.35,
  };

  Plotly.newPlot(el, [trace], layout, PLOTLY_CONFIG);
}

/* ------------------------------------------------------------------ */
/* Chart 2: Green Score Horizontal Bar Chart                           */
/* ------------------------------------------------------------------ */
function renderGreenScoreChart(results) {
  const el = document.getElementById('greenScoreChart');
  if (!el || !results || results.length === 0) return;

  // Sort ascending for horizontal bar (bottom = best)
  const sorted = [...results].sort((a, b) => a.green_score - b.green_score);
  const labels = sorted.map(r => `${r.mode_icon} ${r.mode_name}`);
  const values = sorted.map(r => r.green_score);
  const colors = sorted.map(r => r.color);

  const trace = {
    y: labels,
    x: values,
    type: 'bar',
    orientation: 'h',
    marker: {
      color: colors,
      opacity: 0.88,
      line: { color: colors, width: 1 },
    },
    hovertemplate: '<b>%{y}</b><br>Green Score: %{x:.1f}<extra></extra>',
    text: values.map(v => v.toFixed(1)),
    textposition: 'outside',
    textfont: { size: 10, color: '#374151' },
    cliponaxis: false,
  };

  const layout = {
    ...PLOTLY_LAYOUT_BASE,
    margin: { t: 30, r: 60, b: 40, l: 130 },
    xaxis: {
      ...PLOTLY_LAYOUT_BASE.xaxis,
      title: { text: 'Green Score (0–100)', font: { size: 11 }, standoff: 8 },
      tickangle: 0,
      range: [0, Math.max(...values) * 1.18],
    },
    yaxis: {
      ...PLOTLY_LAYOUT_BASE.yaxis,
      tickfont: { size: 10, color: '#374151' },
    },
    bargap: 0.30,
  };

  Plotly.newPlot(el, [trace], layout, PLOTLY_CONFIG);
}

/* ------------------------------------------------------------------ */
/* Chart 3: Cost vs CO₂ Scatter (bonus insight)                        */
/* ------------------------------------------------------------------ */
function renderCostVsCO2Chart(results) {
  const el = document.getElementById('costCO2Chart');
  if (!el || !results || results.length === 0) return;

  const trace = {
    x: results.map(r => r.co2_kg),
    y: results.map(r => r.cost_inr),
    mode: 'markers+text',
    type: 'scatter',
    marker: {
      color: results.map(r => r.color),
      size: 14,
      opacity: 0.9,
      line: { color: '#fff', width: 1.5 },
    },
    text: results.map(r => r.mode_icon),
    textposition: 'top center',
    textfont: { size: 14 },
    hovertemplate: results.map(r =>
      `<b>${r.mode_name}</b><br>CO₂: ${r.co2_kg.toFixed(3)} kg<br>Cost: ₹${r.cost_inr.toFixed(0)}<extra></extra>`
    ),
  };

  const layout = {
    ...PLOTLY_LAYOUT_BASE,
    xaxis: {
      ...PLOTLY_LAYOUT_BASE.xaxis,
      title: { text: 'CO₂ Emissions (kg)', font: { size: 11 }, standoff: 8 },
      tickangle: 0,
    },
    yaxis: {
      ...PLOTLY_LAYOUT_BASE.yaxis,
      title: { text: 'Cost (₹)', font: { size: 11 }, standoff: 8 },
    },
  };

  Plotly.newPlot(el, [trace], layout, PLOTLY_CONFIG);
}

/* ------------------------------------------------------------------ */
/* Chart 4: Travel Time Comparison                                      */
/* ------------------------------------------------------------------ */
function renderTimeChart(results) {
  const el = document.getElementById('timeChart');
  if (!el || !results || results.length === 0) return;

  const labels = results.map(r => r.mode_name);
  const values = results.map(r => r.duration_min);
  const colors = results.map(r => r.color);

  const trace = {
    x: labels,
    y: values,
    type: 'bar',
    marker: {
      color: colors,
      opacity: 0.85,
      line: { color: colors, width: 1 },
    },
    hovertemplate: '<b>%{x}</b><br>Time: %{y:.0f} min<extra></extra>',
    text: values.map(v => {
      const h = Math.floor(v / 60);
      const m = Math.round(v % 60);
      return h > 0 ? `${h}h ${m}m` : `${m}m`;
    }),
    textposition: 'outside',
    textfont: { size: 10, color: '#374151' },
    cliponaxis: false,
  };

  const layout = {
    ...PLOTLY_LAYOUT_BASE,
    yaxis: {
      ...PLOTLY_LAYOUT_BASE.yaxis,
      title: { text: 'Duration (min)', font: { size: 11 }, standoff: 8 },
    },
    bargap: 0.35,
  };

  Plotly.newPlot(el, [trace], layout, PLOTLY_CONFIG);
}

/* ------------------------------------------------------------------ */
/* Render all charts                                                    */
/* ------------------------------------------------------------------ */
function renderAllCharts(results) {
  renderCO2Chart(results);
  renderGreenScoreChart(results);
  renderCostVsCO2Chart(results);
  renderTimeChart(results);
}
