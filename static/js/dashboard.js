/*
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
  const subData = globalSubdivisions.find(
    s => s.subdivision === currentSubName
  );

  if (subData) {
    if (zoneLabel) {
      zoneLabel.textContent = `${subData.zone} (${subData.capital})`;
    }

    const months = [
      "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
      "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
    ];
    const curIdx = months.indexOf(currentMonth);
    const prevIdx = curIdx > 0 ? curIdx - 1 : 11;
    const prevMonthName = months[prevIdx];
    const prevMedian = subData.monthly_medians[prevMonthName] || 50.0;

    if (slider) slider.value = Math.round(prevMedian);
    if (numInput) numInput.value = prevMedian.toFixed(1);
    if (valDisplay) valDisplay.textContent = prevMedian.toFixed(1);

    if (normalText) {
      normalText.textContent =
        `Historical ${prevMonthName} Median: ${prevMedian} mm`;
    }
  }

  if (!seasonBadge) return;

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

  if (!select || !monthSelect || !slider || !numInput || !predictBtn) {
    console.error("Prediction form elements are missing.");
    return;
  }

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

  if (modelSelect) {
    modelSelect.addEventListener("change", () => {
      if (modelBadge) modelBadge.textContent = modelSelect.value;
      executePrediction();
    });
  }

  // Keep the rainfall slider and numeric input synchronized.
  slider.addEventListener("input", () => {
    const val = parseFloat(slider.value);
    if (valDisplay) valDisplay.textContent = val.toFixed(1);
    numInput.value = val.toFixed(1);
  });

  numInput.addEventListener("input", () => {
    const val = Math.max(0, Math.min(2500, parseFloat(numInput.value) || 0));
    slider.value = Math.min(1500, val);
    if (valDisplay) valDisplay.textContent = val.toFixed(1);
  });

  predictBtn.addEventListener("click", executePrediction);
}

// Execute prediction call
async function executePrediction() {
  const select = document.getElementById("subdivisionSelect");
  const monthSelect = document.getElementById("monthSelect");
  const numInput = document.getElementById("prevRainInput");
  const modelSelect = document.getElementById("modelSelect");
  const spinner = document.getElementById("predictBtnSpinner");
  const btnText = document.getElementById("predictBtnText");

  if (!select || !monthSelect || !numInput) return;

  const subdivision = select.value;
  const month = monthSelect.value;
  const prevRain = parseFloat(numInput.value) || 0;
  const modelName = modelSelect
    ? modelSelect.value
    : "Gradient Boosting";

  if (spinner) spinner.style.display = "inline-block";
  if (btnText) btnText.textContent = "Predicting...";

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
    console.error("Prediction request failed:", err);
    showToast("Network error executing prediction", "error");
  } finally {
    if (spinner) spinner.style.display = "none";
    if (btnText) {
      btnText.textContent = "Calculate Rainfall Probability";
    }
  }
}

// Render contributing factors and animate the result gauge.
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

  if (!pred) return;

  // Gauge circumference: 2 * PI * 90.
  const circumference = 2 * Math.PI * 90;
  const probability = Math.max(
    0,
    Math.min(100, Number(pred.rain_probability_pct) || 0)
  );
  const offset = circumference - (circumference * probability / 100);

  if (gauge) gauge.style.strokeDashoffset = offset;

  if (gauge) {
    if (probability >= 75) {
      gauge.style.stroke = "var(--accent-cyan)";
    } else if (probability >= 45) {
      gauge.style.stroke = "var(--accent-teal)";
    } else {
      gauge.style.stroke = "var(--rain-low)";
    }
  }

  if (pctText) pctText.textContent = `${probability}%`;
  if (riskLabel) riskLabel.textContent = pred.risk_level || "";
  if (verdict) verdict.textContent = pred.prediction_label || "";

  if (estMm) {
    estMm.textContent = `${pred.estimated_amount_mm ?? "—"} mm`;
  }

  if (intensity) {
    intensity.innerHTML =
      `Projected Volume: <strong style="color: var(--accent-cyan); font-family: monospace;">` +
      `${pred.estimated_amount_mm ?? "—"} mm</strong> &bull; ` +
      `${pred.rainfall_category || ""}`;
  }

  if (monthlyNormal) {
    monthlyNormal.textContent =
      `${pred.historical_subdivision_normal_mm ?? "—"} mm`;
  }

  if (annualMean) {
    annualMean.textContent =
      `${pred.annual_mean_rainfall_mm ?? "—"} mm`;
  }

  if (subtitle) {
    subtitle.textContent =
      `${pred.subdivision || ""} • ${pred.month || ""} (${pred.zone || ""})`;
  }

  if (persistedBadge) {
    persistedBadge.style.display = persisted ? "inline-flex" : "none";
  }

  if (factorsList) {
    factorsList.innerHTML = "";

    (pred.contributing_factors || []).forEach(f => {
      const item = document.createElement("div");
      item.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(7, 13, 24, 0.6);
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-sm);
        border: 1px solid var(--surface-border);
        font-size: 0.8rem;
      `;

      const isWet = f.type === "wet";
      item.innerHTML = `
        <span style="display: flex; align-items: center; gap: 0.4rem; color: var(--text-primary);">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: ${isWet ? "var(--accent-cyan)" : "#f59e0b"};"></span>
          ${f.factor || ""}
        </span>
        <span style="color: ${isWet ? "var(--accent-teal)" : "#fcd34d"}; font-size: 0.75rem;">
          ${f.impact || ""}
        </span>
      `;

      factorsList.appendChild(item);
    });
  }
}

// Initialize the Leaflet map for Indian rainfall subdivisions.
function initLeafletMap() {
  const mapEl = document.getElementById("weatherMap");
  if (!mapEl) return;

  if (typeof L === "undefined") {
    console.error(
      "Leaflet is missing. Load Leaflet CSS and JavaScript before dashboard.js."
    );
    mapEl.textContent = "Map library failed to load. Please refresh the page.";
    return;
  }

  weatherMap = L.map(mapEl, {
    zoomControl: true,
    scrollWheelZoom: false
  }).setView([22.5, 79.5], 5);

  // Public OpenStreetMap raster tiles; no API key is required.
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(weatherMap);

  mapMarkersGroup = L.layerGroup().addTo(weatherMap);

  const pills = document.querySelectorAll(".map-month-btn");
  pills.forEach(btn => {
    btn.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");

      const month = btn.getAttribute("data-month");
      if (!month) return;

      currentActiveMonth = month;
      updateMapData(month);
    });
  });

  updateMapData(currentActiveMonth);

  // Correct map sizing if the dashboard layout finishes rendering afterward.
  window.setTimeout(() => weatherMap.invalidateSize(), 100);
}

// Load predictions and add markers for all subdivisions.
async function updateMapData(month = "JUL") {
  if (!weatherMap || !mapMarkersGroup) return;

  try {
    const res = await fetch(
      `/api/map-data?month=${encodeURIComponent(month)}`
    );
    if (!res.ok) {
      throw new Error(`Map data request failed (${res.status})`);
    }

    const data = await res.json();

    if (!data.success || !Array.isArray(data.regions)) {
      throw new Error(data.error || "Map data response was invalid.");
    }

    mapMarkersGroup.clearLayers();

    data.regions.forEach(reg => {
      const latitude = Number(reg.latitude);
      const longitude = Number(reg.longitude);

      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return;

      const pred = reg.current_model_prediction;
      const probability = pred
        ? Number(pred.rain_probability_pct) || 0
        : 50;

      let markerColor = "#10b981";
      if (probability >= 75) markerColor = "#38bdf8";
      else if (probability >= 45) markerColor = "#2dd4bf";

      const annualRain = Number(reg.annual_rainfall_mean_mm) || 1000;
      const radius = Math.max(7, Math.min(16, annualRain / 250));

      const marker = L.circleMarker([latitude, longitude], {
        radius,
        fillColor: markerColor,
        color: "#ffffff",
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.75
      });

      // Build popup DOM safely instead of interpolating server text into HTML.
      const popup = document.createElement("div");
      popup.style.minWidth = "200px";
      popup.style.fontFamily = "inherit";

      const title = document.createElement("div");
      title.textContent = reg.subdivision || "Subdivision";
      title.style.cssText =
        "font-size: .95rem; font-weight: 700; margin-bottom: .2rem;";

      const details = document.createElement("div");
      details.textContent =
        `${reg.zone || ""} • ${reg.capital || ""}`;
      details.style.cssText =
        "font-size: .75rem; color: #64748b; margin-bottom: .5rem;";

      const stats = document.createElement("div");
      stats.style.cssText =
        "padding: .5rem; border-radius: 6px; margin-bottom: .6rem; font-size: .8rem;";

      const rainLine = document.createElement("div");
      rainLine.textContent = `${month} rain chance: ${probability}%`;

      const annualLine = document.createElement("div");
      annualLine.textContent =
        `Annual normal: ${reg.annual_rainfall_mean_mm ?? "—"} mm`;

      const monsoonLine = document.createElement("div");
      monsoonLine.textContent =
        `Monsoon normal: ${reg.monsoon_rainfall_mean_mm ?? "—"} mm`;

      stats.append(rainLine, annualLine, monsoonLine);

      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-primary btn-sm";
      button.textContent = "Load in Predictor";
      button.style.cssText =
        "width: 100%; padding: .35rem; font-size: .8rem;";
      button.addEventListener("click", () => {
        selectSubdivisionOnMap(reg.subdivision);
      });

      popup.append(title, details, stats, button);
      marker.bindPopup(popup);
      mapMarkersGroup.addLayer(marker);
    });
  } catch (err) {
    console.error("Failed to load map data:", err);
  }
}

// Select a subdivision from a map popup.
window.selectSubdivisionOnMap = function(subdivisionName) {
  const select = document.getElementById("subdivisionSelect");
  if (!select) return;

  select.value = subdivisionName;
  updateZoneAndHistoricalAverages();
  executePrediction();

  const form = document.getElementById("predictionForm");
  if (form) {
    form.scrollIntoView({ behavior: "smooth", block: "center" });
  }
};