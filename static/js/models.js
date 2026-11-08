/**
 * Model Performance Benchmarks & Visualizations
 * Created by Hemanth_Kumar
 */

let barChartInstance = null;
let radarChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  loadModelBenchmarks();
  initRetrainHandler();
});

async function loadModelBenchmarks() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();

    if (data.success && data.report) {
      renderBenchmarks(data.report);
    }
  } catch (err) {
    console.error("Failed to fetch model benchmarks:", err);
  }
}

function renderBenchmarks(report) {
  const tableBody = document.getElementById("modelsTableBody");
  const selectedName = report.selected_model_name;

  if (document.getElementById("bestModelName")) {
    document.getElementById("bestModelName").textContent = selectedName;
  }

  // Populate Table
  if (tableBody) {
    tableBody.innerHTML = "";
    report.metrics.forEach(m => {
      const isSelected = m.model_name === selectedName;
      const tr = document.createElement("tr");
      if (isSelected) tr.classList.add("selected-row");

      tr.innerHTML = `
        <td style="font-weight: 600;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            ${m.model_name}
            ${isSelected ? '<span class="badge badge-cyan" style="font-size: 0.65rem;">Selected</span>' : ''}
          </div>
        </td>
        <td><span class="metric-pill">${(m.accuracy * 100).toFixed(1)}%</span></td>
        <td><span style="font-family: monospace;">${m.precision.toFixed(4)}</span></td>
        <td><span style="font-family: monospace;">${m.recall.toFixed(4)}</span></td>
        <td><strong style="color: var(--accent-cyan); font-family: monospace;">${m.f1_score.toFixed(4)}</strong></td>
        <td><strong style="color: var(--accent-teal); font-family: monospace;">${m.roc_auc.toFixed(4)}</strong></td>
        <td><span style="font-family: monospace;">${m.specificity.toFixed(4)}</span></td>
        <td><span class="badge badge-emerald" style="font-size: 0.65rem;">Trained</span></td>
      `;
      tableBody.appendChild(tr);
    });
  }

  // Render Charts
  renderBarChart(report.metrics);
  renderRadarChart(report.metrics);

  // Update Confusion Matrix for Selected Model
  const topModel = report.metrics.find(m => m.model_name === selectedName) || report.metrics[0];
  if (topModel && topModel.confusion_matrix) {
    const cm = topModel.confusion_matrix;
    document.getElementById("cmTN").textContent = cm.true_negatives.toLocaleString();
    document.getElementById("cmFP").textContent = cm.false_positives.toLocaleString();
    document.getElementById("cmFN").textContent = cm.false_negatives.toLocaleString();
    document.getElementById("cmTP").textContent = cm.true_positives.toLocaleString();
    document.getElementById("cmModelTitle").textContent = topModel.model_name;
  }
}

// Chart.js Bar Chart
function renderBarChart(metrics) {
  const canvas = document.getElementById("metricsBarChart");
  if (!canvas) return;

  const labels = metrics.map(m => m.model_name);
  const f1Scores = metrics.map(m => m.f1_score);
  const rocAucScores = metrics.map(m => m.roc_auc);
  const accuracies = metrics.map(m => m.accuracy);

  if (barChartInstance) barChartInstance.destroy();

  barChartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "F1-Score (Primary Metric)",
          data: f1Scores,
          backgroundColor: "rgba(56, 189, 248, 0.8)",
          borderRadius: 4
        },
        {
          label: "ROC-AUC Score",
          data: rocAucScores,
          backgroundColor: "rgba(45, 212, 191, 0.8)",
          borderRadius: 4
        },
        {
          label: "Accuracy",
          data: accuracies,
          backgroundColor: "rgba(129, 140, 248, 0.7)",
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#cbd5e1", font: { family: "inherit" } }
        },
        tooltip: {
          backgroundColor: "rgba(7, 13, 24, 0.95)",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1
        }
      },
      scales: {
        y: {
          min: 0.75,
          max: 1.0,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8" }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#cbd5e1", font: { size: 11 } }
        }
      }
    }
  });
}

// Chart.js Radar Chart
function renderRadarChart(metrics) {
  const canvas = document.getElementById("radarChart");
  if (!canvas) return;

  // Pick top 3 models for clean radar comparison
  const topThree = metrics.slice(0, 3);
  const radarCategories = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "Specificity"];

  const colors = [
    { border: "#38bdf8", bg: "rgba(56, 189, 248, 0.2)" },
    { border: "#2dd4bf", bg: "rgba(45, 212, 191, 0.2)" },
    { border: "#818cf8", bg: "rgba(129, 140, 248, 0.2)" }
  ];

  const datasets = topThree.map((m, idx) => ({
    label: m.model_name,
    data: [m.accuracy, m.precision, m.recall, m.f1_score, m.roc_auc, m.specificity],
    borderColor: colors[idx].border,
    backgroundColor: colors[idx].bg,
    borderWidth: 2,
    pointRadius: 3
  }));

  if (radarChartInstance) radarChartInstance.destroy();

  radarChartInstance = new Chart(canvas, {
    type: "radar",
    data: {
      labels: radarCategories,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#cbd5e1" }
        }
      },
      scales: {
        r: {
          min: 0.8,
          max: 1.0,
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          angleLines: { color: "rgba(255, 255, 255, 0.08)" },
          pointLabels: { color: "#cbd5e1", font: { size: 11 } },
          ticks: { display: false }
        }
      }
    }
  });
}

// Retrain Button Handler
function initRetrainHandler() {
  const retrainBtn = document.getElementById("retrainModelsBtn");
  const spinner = document.getElementById("retrainSpinner");
  const icon = document.getElementById("retrainIcon");

  if (!retrainBtn) return;

  retrainBtn.addEventListener("click", async () => {
    retrainBtn.disabled = true;
    spinner.style.display = "inline-block";
    icon.style.display = "none";

    try {
      showToast("Initiating stratified retraining across 49,392 records...", "info");
      const res = await fetch("/api/models/train", { method: "POST" });
      const data = await res.json();

      if (data.success && data.report) {
        renderBenchmarks(data.report);
        showToast("Models retrained and benchmarked successfully!", "success");
      } else {
        showToast(data.error || "Training failed", "error");
      }
    } catch (err) {
      showToast("Network error retraining models", "error");
    } finally {
      retrainBtn.disabled = false;
      spinner.style.display = "none";
      icon.style.display = "inline-block";
    }
  });
}
