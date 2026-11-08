/**
 * User Prediction History Management
 * Created by Hemanth_Kumar
 */

let allHistoryRecords = [];

document.addEventListener("DOMContentLoaded", () => {
  loadPredictionHistory();
  initHistoryFilters();
  initExportCsv();
  initClearHistory();
});

async function loadPredictionHistory() {
  const loadingEl = document.getElementById("historyLoading");
  const emptyEl = document.getElementById("historyEmpty");
  const tableWrap = document.getElementById("historyTableWrapper");
  const totalCountEl = document.getElementById("historyTotalCount");

  loadingEl.style.display = "block";
  emptyEl.style.display = "none";
  tableWrap.style.display = "none";

  try {
    const res = await fetch("/api/history?limit=100");
    const data = await res.json();

    loadingEl.style.display = "none";

    if (data.success && data.records) {
      allHistoryRecords = data.records;
      totalCountEl.textContent = data.total_count;

      if (data.records.length === 0) {
        emptyEl.style.display = "block";
      } else {
        tableWrap.style.display = "block";
        populateSubdivisionFilter(data.records);
        renderHistoryTable(data.records);
      }
    } else {
      emptyEl.style.display = "block";
    }
  } catch (err) {
    loadingEl.style.display = "none";
    emptyEl.style.display = "block";
    console.error("Failed to load history:", err);
  }
}

function populateSubdivisionFilter(records) {
  const select = document.getElementById("historyFilterRegion");
  if (!select) return;

  const currentVal = select.value;
  const uniqueSubs = Array.from(new Set(records.map(r => r.region))).sort();

  select.innerHTML = '<option value="">All Subdivisions</option>';
  uniqueSubs.forEach(sub => {
    const opt = document.createElement("option");
    opt.value = sub;
    opt.textContent = sub;
    select.appendChild(opt);
  });

  select.value = currentVal;
}

function renderHistoryTable(records) {
  const tbody = document.getElementById("historyTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";

  records.forEach(r => {
    const tr = document.createElement("tr");
    const pct = (r.rain_probability * 100).toFixed(1);
    const isRain = r.predicted_rain === 1;

    let badgeClass = "badge-emerald";
    if (pct >= 75) badgeClass = "badge-cyan";
    else if (pct >= 45) badgeClass = "badge-teal";

    tr.innerHTML = `
      <td style="color: var(--text-muted); font-size: 0.85rem; font-family: monospace;">
        ${r.created_at || "Recent"}
      </td>
      <td style="font-weight: 600; color: var(--text-primary);">
        ${r.region}
      </td>
      <td>
        <span class="badge badge-teal">${r.season}</span>
      </td>
      <td style="color: var(--text-secondary); font-size: 0.85rem;">
        ${r.model_used}
      </td>
      <td>
        <span class="metric-pill">${pct}%</span>
      </td>
      <td>
        <span class="badge ${badgeClass}">${r.rainfall_category || (isRain ? 'Rain' : 'Dry')}</span>
      </td>
      <td style="font-family: monospace; color: var(--accent-cyan);">
        ${isRain ? 'Precipitation Likely' : 'Dry / Normal'}
      </td>
      <td style="text-align: right;">
        <button class="btn btn-danger btn-sm" onclick="deleteHistoryItem(${r.id})" title="Delete Record">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

function initHistoryFilters() {
  const select = document.getElementById("historyFilterRegion");
  if (!select) return;

  select.addEventListener("change", () => {
    const val = select.value;
    if (!val) {
      renderHistoryTable(allHistoryRecords);
    } else {
      const filtered = allHistoryRecords.filter(r => r.region === val);
      renderHistoryTable(filtered);
    }
  });
}

window.deleteHistoryItem = async function(id) {
  if (!confirm("Are you sure you want to delete this prediction log?")) return;

  try {
    const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
    const data = await res.json();

    if (data.success) {
      showToast("Log entry deleted successfully", "success");
      loadPredictionHistory();
    } else {
      showToast(data.error || "Failed to delete log entry", "error");
    }
  } catch (err) {
    showToast("Network error deleting item", "error");
  }
};

function initClearHistory() {
  const clearBtn = document.getElementById("clearHistoryBtn");
  if (!clearBtn) return;

  clearBtn.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to permanently clear all your prediction logs? This action cannot be undone.")) return;

    try {
      const res = await fetch("/api/history", { method: "DELETE" });
      const data = await res.json();

      if (data.success) {
        showToast(data.message, "success");
        loadPredictionHistory();
      } else {
        showToast(data.error || "Failed to clear history", "error");
      }
    } catch (err) {
      showToast("Network error clearing history", "error");
    }
  });
}

function initExportCsv() {
  const exportBtn = document.getElementById("exportCsvBtn");
  if (!exportBtn) return;

  exportBtn.addEventListener("click", () => {
    if (allHistoryRecords.length === 0) {
      showToast("No records available to export", "info");
      return;
    }

    const headers = ["ID", "Created_At", "Subdivision", "Month", "Model_Used", "Rain_Probability_Pct", "Category", "Predicted_Rain"];
    const rows = allHistoryRecords.map(r => [
      r.id,
      r.created_at,
      `"${r.region}"`,
      r.season,
      `"${r.model_used}"`,
      (r.rain_probability * 100).toFixed(1),
      `"${r.rainfall_category || ''}"`,
      r.predicted_rain
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `rainfall_analysis_history_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  });
}
