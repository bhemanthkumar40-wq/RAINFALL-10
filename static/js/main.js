/**
 * Global JavaScript for Rainfall Analysis
 * Created by Hemanth_Kumar
 */

document.addEventListener("DOMContentLoaded", () => {
  initAmbientRain();
  initLogoutHandler();
});

// Ambient Rain Canvas Animation
function initAmbientRain() {
  const canvas = document.getElementById("ambientRainCanvas");
  if (!canvas) return;

  // Respect user preference for reduced motion
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    canvas.style.display = "none";
    return;
  }

  const ctx = canvas.getContext("2d");
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const drops = [];
  const maxDrops = Math.min(65, Math.floor(width / 25));

  for (let i = 0; i < maxDrops; i++) {
    drops.push({
      x: Math.random() * width,
      y: Math.random() * height,
      length: Math.random() * 18 + 12,
      speed: Math.random() * 3.5 + 2.5,
      opacity: Math.random() * 0.25 + 0.1
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 1.2;
    ctx.lineCap = "round";

    for (let i = 0; i < drops.length; i++) {
      const d = drops[i];
      ctx.beginPath();
      ctx.strokeStyle = `rgba(56, 189, 248, ${d.opacity})`;
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x + d.speed * 0.2, d.y + d.length);
      ctx.stroke();

      d.y += d.speed;
      d.x += d.speed * 0.2;

      if (d.y > height) {
        d.y = -d.length;
        d.x = Math.random() * width;
      }
      if (d.x > width) {
        d.x = 0;
      }
    }
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
}

// Global Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `alert alert-${type}`;
  toast.style.cssText = `
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    min-width: 280px;
    animation: fadeIn 0.3s ease;
  `;
  toast.innerHTML = `
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.4s ease";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// Logout Handler
function initLogoutHandler() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (!logoutBtn) return;

  logoutBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/auth/logout", { method: "POST" });
      if (res.ok) {
        showToast("Signed out successfully", "success");
        setTimeout(() => {
          window.location.href = "/";
        }, 500);
      }
    } catch (e) {
      window.location.href = "/";
    }
  });
}
