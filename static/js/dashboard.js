/**
 * Rainfall Intelligence – Dashboard Chart.js Visualizations
 * Professional, clean light-themed interactive charts.
 */

let monthlyChart = null;
let yearlyChart = null;
let distributionChart = null;
let regionalChart = null;
let actualVsPredChart = null;
let seasonalChart = null;

// Light theme Chart.js global defaults
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = "#64748B";
Chart.defaults.plugins.tooltip.backgroundColor = "#172033";
Chart.defaults.plugins.tooltip.titleColor = "#FFFFFF";
Chart.defaults.plugins.tooltip.bodyColor = "#F1F5F9";
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;

document.addEventListener("DOMContentLoaded", () => {
    loadDashboardVisualizations();

    window.addEventListener("datasetChanged", (e) => {
        loadDashboardVisualizations(e.detail.dataset);
    });
});

async function loadDashboardVisualizations(datasetName) {
    const activeDataset = datasetName || localStorage.getItem("selected_dataset") || "Subdivision Rainfall (1901-2015)";

    try {
        // Fetch visualization aggregations
        const vizResp = await fetch(`/api/datasets/visualizations?dataset=${encodeURIComponent(activeDataset)}`);
        const vizJson = await vizResp.json();

        // Fetch model benchmark data
        const modelResp = await fetch(`/api/models?dataset=${encodeURIComponent(activeDataset)}`);
        const modelJson = await modelResp.json();

        if (vizJson.success) {
            renderMonthlyTrends(vizJson.data.monthly_trends);
            renderYearlyTrends(vizJson.data.yearly_trends);
            renderDistribution(vizJson.data.distribution_bins);
            renderRegionalComparison(vizJson.data.regional_data);
            renderSeasonalDoughnut(vizJson.data.seasonal_data);
        }

        if (modelJson.success) {
            renderActualVsPredicted(modelJson.report);
            updateDashboardStats(modelJson.report, activeDataset);
        }
    } catch (err) {
        console.error("Failed to load dashboard data:", err);
    }
}

function updateDashboardStats(report, datasetName) {
    if (report && report.best_model) {
        const bestModelEl = document.getElementById("statBestModel");
        if (bestModelEl) bestModelEl.textContent = report.best_model;

        const bestMetric = report.metrics.find(m => m.model_name === report.best_model);
        const metricEl = document.getElementById("statBestMetric");
        if (metricEl && bestMetric) {
            metricEl.textContent = `R² = ${bestMetric.r2_score}`;
        }
    }
}

// 1. Monthly Rainfall Trends (Line / Area Chart)
function renderMonthlyTrends(trends) {
    const ctx = document.getElementById("monthlyTrendChart");
    if (!ctx) return;

    if (monthlyChart) monthlyChart.destroy();

    const labels = Object.keys(trends || {});
    const values = Object.values(trends || {});

    monthlyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Median Rainfall (mm)",
                data: values,
                borderColor: "#2563EB",
                backgroundColor: "rgba(37, 99, 235, 0.08)",
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: "#2563EB",
                pointBorderColor: "#FFFFFF",
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748B", font: { weight: 500 } }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}

// 2. 115-Year Rainfall Analysis Timeline
function renderYearlyTrends(yearlyData) {
    const ctx = document.getElementById("yearlyTrendChart");
    if (!ctx) return;

    if (yearlyChart) yearlyChart.destroy();

    const labels = (yearlyData || []).map(d => d.year);
    const values = (yearlyData || []).map(d => d.rainfall_mm);

    yearlyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Annual Mean Rainfall (mm)",
                data: values,
                borderColor: "#0D9488",
                backgroundColor: "rgba(13, 148, 136, 0.08)",
                borderWidth: 2.2,
                fill: true,
                tension: 0.25,
                pointBackgroundColor: "#0D9488",
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 12, color: "#64748B" }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}

// 3. Rainfall Distribution Histogram
function renderDistribution(bins) {
    const ctx = document.getElementById("distributionChart");
    if (!ctx) return;

    if (distributionChart) distributionChart.destroy();

    const labels = (bins || []).map(b => b.range);
    const values = (bins || []).map(b => b.count);

    distributionChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Record Frequency",
                data: values,
                backgroundColor: "#3B82F6",
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45, minRotation: 25, color: "#64748B", font: { size: 11 } }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}

// 4. Regional Rainfall Comparison (Bar Chart)
function renderRegionalComparison(regionalData) {
    const ctx = document.getElementById("regionalChart");
    if (!ctx) return;

    if (regionalChart) regionalChart.destroy();

    const labels = (regionalData || []).map(r => r.region);
    const values = (regionalData || []).map(r => r.rainfall_mm);

    regionalChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Average Annual Rainfall (mm)",
                data: values,
                backgroundColor: values.map(v => v > 2000 ? "#2563EB" : (v < 600 ? "#F59E0B" : "#0D9488")),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: "#172033", font: { size: 11, weight: 600 } }
                }
            }
        }
    });
}

// 5. Actual vs Predicted Comparison
function renderActualVsPredicted(report) {
    const ctx = document.getElementById("actualVsPredChart");
    if (!ctx) return;

    if (actualVsPredChart) actualVsPredChart.destroy();

    const actual = report.actual_samples || [];
    const predicted = report.predicted_samples || [];
    const sampleLabels = actual.map((_, i) => `#${i + 1}`);

    actualVsPredChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: sampleLabels,
            datasets: [
                {
                    label: "Actual Rainfall (mm)",
                    data: actual,
                    borderColor: "#172033",
                    backgroundColor: "transparent",
                    borderWidth: 2,
                    pointRadius: 3,
                    tension: 0.1
                },
                {
                    label: `Predicted (${report.best_model || "ML Model"})`,
                    data: predicted,
                    borderColor: "#2563EB",
                    backgroundColor: "transparent",
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: { color: "#172033", font: { weight: 600 } }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 15, color: "#64748B" }
                },
                y: {
                    grid: { color: "#F1F5F9" },
                    ticks: { color: "#64748B" }
                }
            }
        }
    });
}

// 6. Seasonal Contribution Doughnut
function renderSeasonalDoughnut(seasonalData) {
    const ctx = document.getElementById("seasonalChart");
    if (!ctx) return;

    if (seasonalChart) seasonalChart.destroy();

    const labels = Object.keys(seasonalData || {});
    const values = Object.values(seasonalData || {});

    seasonalChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#60A5FA", // Jan-Feb
                    "#34D399", // Mar-May
                    "#2563EB", // Jun-Sep (Monsoon)
                    "#F59E0B"  // Oct-Dec
                ],
                borderWidth: 2,
                borderColor: "#FFFFFF"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#172033", font: { size: 11, weight: 500 }, padding: 12 }
                }
            },
            cutout: "65%"
        }
    });
}
