/**
 * Rainfall Intelligence – Model Benchmarking & Comparison JavaScript
 * Renders comparison tables, error charts, and handles retraining.
 */

let r2Chart = null;
let errorChart = null;
let testTrackingChart = null;

document.addEventListener("DOMContentLoaded", () => {
    loadModelBenchmarks();

    // Retrain UI Controls
    const openBtn = document.getElementById("btnOpenRetrainModal");
    const closeBtn = document.getElementById("btnCloseRetrain");
    const retrainCard = document.getElementById("retrainCard");
    const slider = document.getElementById("splitSlider");
    const ratioDisplay = document.getElementById("splitRatioDisplay");
    const execBtn = document.getElementById("btnExecuteRetrain");

    if (openBtn) openBtn.onclick = () => retrainCard.style.display = "block";
    if (closeBtn) closeBtn.onclick = () => retrainCard.style.display = "none";

    if (slider) {
        slider.oninput = (e) => {
            const testPct = parseInt(e.target.value);
            const trainPct = 100 - testPct;
            ratioDisplay.textContent = `${trainPct}% Train / ${testPct}% Test`;
        };
    }

    if (execBtn) {
        execBtn.onclick = async () => {
            const activeDataset = localStorage.getItem("selected_dataset") || "Subdivision Rainfall (1901-2015)";
            const testSize = parseFloat(slider.value) / 100.0;
            execBtn.disabled = true;
            execBtn.textContent = "Training 7 Algorithms...";

            try {
                const resp = await fetch("/api/models/train", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dataset_name: activeDataset, test_size: testSize })
                });
                const res = await resp.json();

                if (res.success) {
                    showToast(res.message, "success");
                    retrainCard.style.display = "none";
                    loadModelBenchmarks(activeDataset);
                } else {
                    showToast(res.error || "Training failed", "error");
                }
            } catch (err) {
                showToast("Error retraining models", "error");
            } finally {
                execBtn.disabled = false;
                execBtn.textContent = "Execute Multi-Model Training";
            }
        };
    }

    window.addEventListener("datasetChanged", (e) => {
        loadModelBenchmarks(e.detail.dataset);
    });
});

async function loadModelBenchmarks(datasetName) {
    const activeDataset = datasetName || localStorage.getItem("selected_dataset") || "Subdivision Rainfall (1901-2015)";
    const badge = document.getElementById("datasetNameBadge");
    if (badge) badge.textContent = activeDataset;

    try {
        const resp = await fetch(`/api/models?dataset=${encodeURIComponent(activeDataset)}`);
        const json = await resp.json();

        if (json.success && json.report) {
            renderComparisonTable(json.report.metrics);
            updateSummaryCards(json.report);
            renderR2Chart(json.report.metrics);
            renderErrorChart(json.report.metrics);
            renderTrackingChart(json.report);
        }
    } catch (err) {
        console.error("Error loading model benchmarks:", err);
    }
}

function renderComparisonTable(metrics) {
    const tbody = document.getElementById("modelsTableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    metrics.forEach(m => {
        const tr = document.createElement("tr");
        if (m.is_best) tr.style.backgroundColor = "#F0FDF4";

        tr.innerHTML = `
            <td style="font-weight: 600; color: #172033;">
                ${m.is_best ? '⭐ ' : ''}${m.model_name}
            </td>
            <td>
                <span class="badge-clean ${m.is_best ? 'badge-green' : 'badge-blue'}" style="font-size: 13px;">
                    ${m.r2_score.toFixed(4)}
                </span>
            </td>
            <td style="font-family: monospace; font-weight: 600;">${m.mae.toFixed(2)} mm</td>
            <td style="font-family: monospace; color: var(--text-secondary);">${m.mse.toLocaleString()}</td>
            <td style="font-family: monospace; font-weight: 600;">${m.rmse.toFixed(2)} mm</td>
            <td style="font-family: monospace;">${m.mape.toFixed(2)}%</td>
            <td style="font-size: 12px; color: var(--text-secondary);">${m.training_time.toFixed(3)}s</td>
            <td>
                ${m.is_best
                    ? '<span class="badge-clean badge-green">Best Regressor</span>'
                    : '<span class="badge-clean badge-teal">Benchmark Ready</span>'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateSummaryCards(report) {
    const metrics = report.metrics || [];
    if (metrics.length === 0) return;

    const best = metrics.find(m => m.is_best) || metrics[0];
    document.getElementById("topModelName").textContent = best.model_name;
    document.getElementById("topModelR2").textContent = `R² = ${best.r2_score}`;
    document.getElementById("topModelMae").innerHTML = `${best.mae.toFixed(2)} <span style="font-size: 16px; font-weight: normal; color: var(--text-secondary);">mm</span>`;
    document.getElementById("topModelRmse").innerHTML = `${best.rmse.toFixed(2)} <span style="font-size: 16px; font-weight: normal; color: var(--text-secondary);">mm</span>`;

    // Fastest model
    const fastest = [...metrics].sort((a, b) => a.training_time - b.training_time)[0];
    if (fastest) {
        document.getElementById("fastestModel").textContent = fastest.model_name;
        document.getElementById("fastestTime").textContent = `${fastest.training_time.toFixed(3)}s`;
    }
}

function renderR2Chart(metrics) {
    const ctx = document.getElementById("r2Chart");
    if (!ctx) return;

    if (r2Chart) r2Chart.destroy();

    const sorted = [...metrics].sort((a, b) => b.r2_score - a.r2_score);
    const labels = sorted.map(m => m.model_name);
    const values = sorted.map(m => m.r2_score);

    r2Chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "R² Score",
                data: values,
                backgroundColor: sorted.map(m => m.is_best ? "#16A34A" : "#2563EB"),
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    min: 0.8,
                    max: 1.0,
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: "#172033", font: { weight: 600 } }
                }
            }
        }
    });
}

function renderErrorChart(metrics) {
    const ctx = document.getElementById("errorChart");
    if (!ctx) return;

    if (errorChart) errorChart.destroy();

    const labels = metrics.map(m => m.model_name);
    const maeValues = metrics.map(m => m.mae);
    const rmseValues = metrics.map(m => m.rmse);

    errorChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "MAE (mm)",
                    data: maeValues,
                    backgroundColor: "#0D9488",
                    borderRadius: 4
                },
                {
                    label: "RMSE (mm)",
                    data: rmseValues,
                    backgroundColor: "#F59E0B",
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 35, color: "#64748B", font: { size: 11 } }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}

function renderTrackingChart(report) {
    const ctx = document.getElementById("testTrackingChart");
    if (!ctx) return;

    if (testTrackingChart) testTrackingChart.destroy();

    const actual = report.actual_samples || [];
    const pred = report.predicted_samples || [];
    const labels = actual.map((_, i) => `Point ${i + 1}`);

    testTrackingChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Ground Truth (Actual IMD mm)",
                    data: actual,
                    borderColor: "#172033",
                    backgroundColor: "transparent",
                    borderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: `Predicted (${report.best_model})`,
                    data: pred,
                    borderColor: "#16A34A",
                    backgroundColor: "rgba(22, 163, 74, 0.05)",
                    borderWidth: 2,
                    borderDash: [4, 4],
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 20, color: "#64748B" }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}
