/**
 * Rainfall Intelligence – Global Application JavaScript
 * Handles sidebar toggling, theme switching, global dataset selection,
 * and unified toast notifications.
 */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSidebar();
    initDatasetSelector();
});

// --- Unified Toast Notifications ---
function showToast(message, type = "info") {
    const container = document.getElementById("globalToastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-alert toast-${type}`;
    
    let bg = "#EFF6FF", border = "#2563EB", text = "#1E40AF";
    if (type === "success") { bg = "#F0FDF4"; border = "#16A34A"; text = "#166534"; }
    if (type === "warning") { bg = "#FFFBEB"; border = "#D97706"; text = "#92400E"; }
    if (type === "error" || type === "danger") { bg = "#FEF2F2"; border = "#DC2626"; text = "#991B1B"; }

    toast.style.cssText = `
        background-color: ${bg};
        border-left: 4px solid ${border};
        color: ${text};
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 10px;
        font-size: 13.5px;
        font-weight: 500;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        transition: all 0.3s ease;
    `;

    toast.innerHTML = `
        <span>${message}</span>
        <button style="background:transparent; border:none; color:inherit; cursor:pointer; font-size:16px; font-weight:bold;">&times;</button>
    `;

    toast.querySelector("button").onclick = () => toast.remove();
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// --- Theme Management (Default: LIGHT THEME) ---
function initTheme() {
    const themeBtn = document.getElementById("themeToggleBtn");
    const currentTheme = localStorage.getItem("app_theme") || "light";

    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }

    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            const isDark = document.body.classList.toggle("dark-mode");
            localStorage.setItem("app_theme", isDark ? "dark" : "light");
            showToast(`Switched to ${isDark ? "Dark" : "Light"} theme`, "info");
        });
    }
}

// --- Mobile Sidebar Drawer ---
function initSidebar() {
    const sidebar = document.getElementById("appSidebar");
    const mobileBtn = document.getElementById("mobileMenuBtn");
    const closeBtn = document.getElementById("sidebarCloseBtn");

    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener("click", () => {
            sidebar.classList.toggle("mobile-open");
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", () => {
            sidebar.classList.remove("mobile-open");
        });
    }
}

// --- Global Dataset Selector ---
function initDatasetSelector() {
    const select = document.getElementById("globalDatasetSelect");
    if (!select) return;

    const savedDataset = localStorage.getItem("selected_dataset");
    if (savedDataset) {
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === savedDataset) {
                select.selectedIndex = i;
                break;
            }
        }
    }

    select.addEventListener("change", (e) => {
        const selected = e.target.value;
        localStorage.setItem("selected_dataset", selected);
        showToast(`Active dataset set to "${selected}"`, "success");
        window.dispatchEvent(new CustomEvent("datasetChanged", { detail: { dataset: selected } }));
    });
}
