/**
 * Interactive Prediction Dashboard & Geospatial Map
 * Created by Hemanth_Kumar
 */

let weatherMap = null;
let mapMarkersGroup = null;
let globalSubdivisions = [];
let currentActiveMonth = "JUL";

document.addEventListener("DOMContentLoaded", async () => {
  await loadSubdivisions();
  initFormSync();
  initLeafletMap();
  executePrediction(); // Initial prediction run
});

// Load all 36 subdivisions from API
async function loadSubdivisions() {
  try {
    const res = await fetch("/api/subdivisions");
    const data = await res.json();
    if (data.success) {
      globalSubdivisions = data.subdivisions;
      populateSubdivisionDropdown(data.subdivisions);
    }
  } catch (err) {
    console.error("Failed to load subdivisions:", err);
  }
}

function populateSubdivisionDropdown(subdivisions) {
  const select = document.getElementById("subdivisionSelect");
  if (!select) return;

  select.innerHTML = "";
  subdivisions.forEach(sub => {
    const opt = document.createElement("option");
    opt.value = sub.subdivision;
    opt.textContent = `${sub.subdivision} (${sub.zone})`;
    if (sub.subdivision === "KERALA") {
      opt.selected = true;
    }
    select.appendChild(opt);
  });

  updateZoneAndHistoricalAverages();
}

function updateZoneAndHistoricalAverages() {
  const select = document.getElementById("subdivisionSelect");
  const monthSelect = document.getElementById("monthSelect");
  const zoneLabel = document.getElementById("subZoneLabel");
  const slider = document.getElementById("prevRainSlider");
  const numInput = document.getElementById("prevRainInput");
  const valDisplay = document.getElementById("prevRainVal");
  const normalText = document.getElementById("historicalNormalText");
  const seasonBadge = document.getElementById("seasonBadge");

  if (!select || !monthSelect) return;

  const currentSubName = select.value;
  const currentMonth = monthSelect.value;
  const subData = globalSubdivisions.find(s => s.subdivision === currentSubName);

  if (subData) {
    if (zoneLabel) zoneLabel.textContent = `${subData.zone} (${subData.capital})`;

    // Determine prior month
    const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const curIdx = months.indexOf(currentMonth);
    const prevIdx = curIdx > 0 ? curIdx - 1 : 11;
    const prevMonthName = months[prevIdx];
    const prevMedian = subData.monthly_medians[prevMonthName] || 50.0;

    // Prefill slider and inputs
    slider.value = Math.round(prevMedian);
    numInput.value = prevMedian.toFixed(1);
    valDisplay.textContent = prevMedian.toFixed(1);

    if (normalText) {
      normalText.textContent = `Historical ${prevMonthName} Median: ${prevMedian} mm`;
    }
  }

  // Update Season Badge
  if (["JUN", "JUL", "AUG", "SEP"].includes(currentMonth)) {
    seasonBadge.textContent = "Southwest Monsoon";
    seasonBadge.className = "badge badge-teal";
  } else if (["OCT", "NOV"].includes(currentMonth)) {
    seasonBadge.textContent = "Post-Monsoon / Northeast";
    seasonBadge.className = "badge badge-violet";
  } else if (["DEC", "JAN", "FEB"].includes(currentMonth)) {
    seasonBadge.textContent = "Winter Season";
    seasonBadge.className = "badge badge-cyan";
  } else {
    seasonBadge.textContent = "Pre-Monsoon / Summer";
    seasonBadge.className = "badge badge-amber";
  }
}

function initFormSync() {
  const select = document.getElementById("subdivisionSelect");
  const monthSelect = document.getElementById("monthSelect");
  const slider = document.getElementById("prevRainSlider");
  const numInput = document.getElementById("prevRainInput");
  const valDisplay = document.getElementById("prevRainVal");
  const predictBtn = document.getElementById("predictBtn");
  const modelSelect = document.getElementById("modelSelect");
  const modelBadge = document.getElementById("modelActiveBadge");

  select.addEventListener("change", () => {
    updateZoneAndHistoricalAverages();
    executePrediction();
  });

  monthSelect.addEventListener("change", () => {
    updateZoneAndHistoricalAverages();
    currentActiveMonth = monthSelect.value;
    updateMapData(currentActiveMonth);
    executePrediction();
  });

  modelSelect.addEventListener("change", () => {
    if (modelBadge) modelBadge.textContent = modelSelect.value;
    executePrediction();
  });

  // Two-way sync slider <-> numeric input
  slider.addEventListener("input", () => {
    const val = parseFloat(slider.value);
    numInput.value = val.toFixed(1);
    valDisplay.textContent = val.toFixed(1);
  });

  numInput.addEventListener("input", () => {
    const val = Math.max(0, Math.min(2500, parseFloat(numInput.value) || 0));
    slider.value = Math.min(1500, val);
    valDisplay.textContent = val.toFixed(1);
  });

  predictBtn.addEventListener("click", () => {
    executePrediction();
  });
}

// Execute Prediction Call
async function executePrediction() {
  const select = document.getElementById("subdivisionSelect");
  const monthSelect = document.getElementById("monthSelect");
  const numInput = document.getElementById("prevRainInput");
  const modelSelect = document.getElementById("modelSelect");
  const spinner = document.getElementById("predictBtnSpinner");
  const btnText = document.getElementById("predictBtnText");

  if (!select) return;

  const subdivision = select.value;
  const month = monthSelect.value;
  const prevRain = parseFloat(numInput.value) || 0;
  const modelName = modelSelect ? modelSelect.value : "Gradient Boosting";

  spinner.style.display = "inline-block";
  btnText.textContent = "Predicting...";

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subdivision,
        month,
        prev_month_rain_mm: prevRain,
        model_name: modelName
      })
    });
    const data = await res.json();

    if (data.success && data.prediction) {
      renderPredictionResult(data.prediction, data.persisted);
    } else {
      showToast(data.error || "Prediction request failed", "error");
    }
  } catch (err) {
    showToast("Network error executing prediction", "error");
  } finally {
    spinner.style.display = "none";
    btnText.textContent = "Calculate Rainfall Probability";
  }
}

// Render Prediction Result & Animate Gauge
function renderPredictionResult(pred, persisted) {
  const gauge = document.getElementById("gaugeProgress");
  const pctText = document.getElementById("probPercentage");
  const riskLabel = document.getElementById("probRiskLabel");
  const verdict = document.getElementById("predictionVerdict");
  const intensity = document.getElementById("intensityEstimate");
  const estMm = document.getElementById("estAmountMm");
  const monthlyNormal = document.getElementById("monthlyNormalMm");
  const annualMean = document.getElementById("annualMeanMm");
  const factorsList = document.getElementById("factorsList");
  const subtitle = document.getElementById("resultSubtitle");
  const persistedBadge = document.getElementById("persistedBadge");

  // Animate Gauge Meter (Circumference = 2 * PI * 90 = 565.48)
  const circumference = 565.48;
  const offset = circumference - (circumference * (pred.rain_probability_pct / 100));
  gauge.style.strokeDashoffset = offset;

  // Change stroke color based on probability
  if (pred.rain_probability_pct >= 75) {
    gauge.style.stroke = "var(--accent-cyan)";
  } else if (pred.rain_probability_pct >= 45) {
    gauge.style.stroke = "var(--accent-teal)";
  } else {
    gauge.style.stroke = "var(--rain-low)";
  }

  pctText.textContent = `${pred.rain_probability_pct}%`;
  riskLabel.textContent = pred.risk_level;
  verdict.textContent = pred.prediction_label;
  if (estMm) estMm.textContent = `${pred.estimated_amount_mm} mm`;
  if (intensity) intensity.innerHTML = `Projected Volume: <strong style="color: var(--accent-cyan); font-family: monospace;">${pred.estimated_amount_mm} mm</strong> &bull; ${pred.rainfall_category}`;
  if (monthlyNormal) monthlyNormal.textContent = `${pred.historical_subdivision_normal_mm} mm`;
  if (annualMean) annualMean.textContent = `${pred.annual_mean_rainfall_mm} mm`;
  if (subtitle) subtitle.textContent = `${pred.subdivision} • ${pred.month} (${pred.zone})`;

  if (persistedBadge) {
    persistedBadge.style.display = persisted ? "inline-flex" : "none";
  }

  // Render Contributing Factors
  if (factorsList) {
    factorsList.innerHTML = "";
    (pred.contributing_factors || []).forEach(f => {
      const item = document.createElement("div");
      item.style.cssText = `
        display: flex; align-items: center; justify-content: space-between;
        background: rgba(7, 13, 24, 0.6); padding: 0.5rem 0.75rem;
        border-radius: var(--radius-sm); border: 1px solid var(--surface-border);
        font-size: 0.8rem;
      `;
      const isWet = f.type === "wet";
      item.innerHTML = `
        <span style="display: flex; align-items: center; gap: 0.4rem; color: var(--text-primary);">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: ${isWet ? 'var(--accent-cyan)' : '#f59e0b'};"></span>
          ${f.factor}
        </span>
        <span style="color: ${isWet ? 'var(--accent-teal)' : '#fcd34d'}; font-size: 0.75rem;">${f.impact}</span>
      `;
      factorsList.appendChild(item);
    });
  }
}

// Initialize Leaflet Map for 36 Indian Subdivisions
function initLeafletMap() {
  const mapEl = document.getElementById("weatherMap");
  if (!mapEl) return;

  // Center of India
  weatherMap = L.map("weatherMap", {
    zoomControl: true,
    scrollWheelZoom: false
  }).setView([22.5, 79.5], 5);

  // CartoDB Dark Matter tiles (clean, high contrast, scientific)
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(weatherMap);

  mapMarkersGroup = L.layerGroup().addTo(weatherMap);

  // Bind season filter pills above map
  const pills = document.querySelectorAll(".map-month-btn");
  pills.forEach(btn => {
    btn.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const m = btn.getAttribute("data-month");
      currentActiveMonth = m;
      updateMapData(m);
    });
  });

  updateMapData("JUL");
}

// Update Map Markers with Live Model Predictions for All 36 Subdivisions
async function updateMapData(month = "JUL") {
  if (!weatherMap || !mapMarkersGroup) return;

  try {
    const res = await fetch(`/api/map-data?month=${month}`);
    const data = await res.json();

    if (data.success && data.regions) {
      mapMarkersGroup.clearLayers();

      data.regions.forEach(reg => {
        if (!reg.latitude || !reg.longitude) return;

        const pred = reg.current_model_prediction;
        const prob = pred ? pred.rain_probability_pct : 50;

        // Dynamic marker color based on probability
        let markerColor = "#10b981"; // Low rain
        if (prob >= 75) markerColor = "#38bdf8"; // High rain
        else if (prob >= 45) markerColor = "#2dd4bf"; // Moderate rain

        // Radius scaled by annual rainfall mean
        const ann = reg.annual_rainfall_mean_mm || 1000;
        const radius = Math.max(7, Math.min(16, (ann / 250)));

        const marker = L.circleMarker([reg.latitude, reg.longitude], {
          radius: radius,
          fillColor: markerColor,
          color: "#ffffff",
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.75
        });

        // Popup with climate metrics & quick load button
        const popupContent = `
          <div style="min-width: 200px; font-family: inherit;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.2rem;">
              ${reg.subdivision}
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.5rem;">
              ${reg.zone} &bull; ${reg.capital}
            </div>
            <div style="background: rgba(7, 13, 24, 0.8); padding: 0.5rem; border-radius: 6px; margin-bottom: 0.6rem; font-size: 0.8rem;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                <span style="color: #94a3b8;">${month} Rain Chance:</span>
                <strong style="color: ${markerColor};">${prob}%</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                <span style="color: #94a3b8;">Annual Normal:</span>
                <span style="color: #f8fafc; font-family: monospace;">${reg.annual_rainfall_mean_mm} mm</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: #94a3b8;">Monsoon Normal:</span>
                <span style="color: #38bdf8; font-family: monospace;">${reg.monsoon_rainfall_mean_mm} mm</span>
              </div>
            </div>
            <button class="btn btn-primary btn-sm" style="width: 100%; padding: 0.35rem; font-size: 0.8rem;" onclick="selectSubdivisionOnMap('${reg.subdivision}')">
              Load in Predictor
            </button>
          </div>
        `;

        marker.bindPopup(popupContent);
        mapMarkersGroup.addLayer(marker);
      });
    }
  } catch (err) {
    console.error("Failed to load map data:", err);
  }
}

// Window helper called from Leaflet popup button
window.selectSubdivisionOnMap = function(subdivisionName) {
  const select = document.getElementById("subdivisionSelect");
  if (!select) return;

  select.value = subdivisionName;
  updateZoneAndHistoricalAverages();
  executePrediction();

  // Smooth scroll to prediction form
  document.getElementById("predictionForm").scrollIntoView({ behavior: "smooth", block: "center" });
};
