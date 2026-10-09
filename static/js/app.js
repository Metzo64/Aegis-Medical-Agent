/**
 * Aegis-RL EHR Hospital Access Control
 * Core Application Framework & State Manager
 */

const AppState = {
  currentUser: {
    user_id: 709,
    username: "user_001",
    full_name: "Dr. Vishnu Pandey",
    role: "DOCTOR",
    role_normalized: "DOCTOR",
    department_name: "Cardiology",
    department_id: 1,
    usual_location: "INTERNAL_HOSPITAL"
  },
  activePage: "dashboard",
  usersCache: [],
  patientsCache: [],
  systemStats: null,
  activeTargetPatient: null,
  activeTargetRecord: null
};

// SVG Icon Provider for high-DPI retina rendering
const Icons = {
  shield: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  activity: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  users: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  cpu: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`,
  database: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  alertTriangle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  checkCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  xCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  clock: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  search: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  zap: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  crosshair: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>`,
  fileText: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
};

/**
 * Toast Notification Dispatcher
 */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-hub");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  let icon = Icons.activity;
  if (type === "success") icon = Icons.checkCircle;
  if (type === "error") icon = Icons.xCircle;
  if (type === "warning") icon = Icons.alertTriangle;

  toast.innerHTML = `
    <div style="width:20px;height:20px;color:currentColor;flex-shrink:0;">${icon}</div>
    <div style="flex:1;font-size:0.84rem;color:#F8FAFC;font-weight:500;">${message}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 250);
  }, 4200);
}

/**
 * Animated Number Counter
 */
function animateValue(elementOrId, start, end, duration = 800, suffix = "", prefix = "") {
  const el = typeof elementOrId === "string" ? document.getElementById(elementOrId) : elementOrId;
  if (!el) return;

  const startTime = performance.now();
  const isFloat = end % 1 !== 0;

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease-out cubic
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * easeProgress;

    el.innerText = `${prefix}${isFloat ? current.toFixed(2) : Math.round(current).toLocaleString()}${suffix}`;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

/**
 * Unified API Client
 */
async function apiRequest(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errData.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

/**
 * Page Navigation Controller
 */
function navigateTo(pageId) {
  const targetId = `view-${pageId}`;
  const targetEl = document.getElementById(targetId);
  if (!targetEl) return;

  // Update Navigation Active State
  document.querySelectorAll(".nav-link").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-page") === pageId);
  });

  // Switch Active View
  document.querySelectorAll(".view").forEach(page => {
    page.classList.remove("active");
  });
  targetEl.classList.add("active");

  // Update Breadcrumbs & Topbar
  AppState.activePage = pageId;
  const pageTitles = {
    dashboard: "Hospital Staff Dashboard",
    admin: "Security Administrator Dashboard",
    patients: "Patient Health Records",
    access: "Adaptive RL Decision Engine",
    simulator: "Cyber Attack Simulator & Ops",
    history: "System Access & Audit History"
  };

  const titleEl = document.getElementById("topbarTitle");
  if (titleEl) {
    titleEl.innerText = pageTitles[pageId] || "Aegis-RL EHR";
  }
  const breadcrumbEl = document.getElementById("topbarBreadcrumb");
  if (breadcrumbEl) {
    breadcrumbEl.innerText = `Aegis-RL / ${pageTitles[pageId] || pageId}`;
  }

  // Trigger page-specific initializers
  if (pageId === "dashboard" && typeof loadStaffDashboard === "function") {
    loadStaffDashboard();
  } else if (pageId === "admin" && typeof loadAdminDashboard === "function") {
    loadAdminDashboard();
  } else if (pageId === "patients" && typeof loadPatientsPage === "function") {
    loadPatientsPage();
  } else if (pageId === "access" && typeof initAccessPage === "function") {
    initAccessPage();
  } else if (pageId === "simulator" && typeof initSimulatorPage === "function") {
    initSimulatorPage();
  } else if (pageId === "history" && typeof loadHistoryPage === "function") {
    loadHistoryPage();
  }

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Persona / User Switcher Controller
 */
async function loadUsersForSwitcher() {
  try {
    const data = await apiRequest("/api/users?limit=40");
    AppState.usersCache = data.users || [];
    renderUserSwitcherList();
  } catch (e) {
    console.warn("Could not load users list:", e);
  }
}

function renderUserSwitcherList() {
  const container = document.getElementById("personaPillsList");
  if (!container) return;

  container.innerHTML = AppState.usersCache.map(u => {
    const isSelected = u.user_id === AppState.currentUser.user_id;
    return `
      <div class="persona-pill ${isSelected ? 'selected' : ''}" onclick="selectUser(${u.user_id})">
        <div class="user-chip-avatar" style="flex-shrink:0">${(u.full_name||'?').split(' ').map(n=>n[0]).slice(0,2).join('')}</div>
        <div style="flex:1;min-width:0">
          <div class="persona-name">${u.full_name}</div>
          <div class="persona-role">${u.role} &middot; ${u.department_name}</div>
        </div>
        <span class="sens-badge">${u.role_normalized}</span>
      </div>
    `;
  }).join("");
}

function selectUser(userId) {
  const found = AppState.usersCache.find(u => u.user_id === userId);
  if (!found) return;

  AppState.currentUser = found;
  updateUserInterfaceProfile();
  renderUserSwitcherList();

  closeLoginModal();
  showToast(`Active Session: ${found.full_name} (${found.role} - ${found.department_name})`, "success");

  // Refresh current view if needed
  if (AppState.activePage === "dashboard") {
    loadStaffDashboard();
  }
}

function updateUserInterfaceProfile() {
  const u = AppState.currentUser;
  const nameEls = document.querySelectorAll(".current-user-name");
  const roleEls = document.querySelectorAll(".current-user-role");
  const deptEls = document.querySelectorAll(".current-user-dept");
  const avatarEls = document.querySelectorAll(".current-user-avatar");

  nameEls.forEach(el => el.innerText = u.full_name);
  roleEls.forEach(el => el.innerText = u.role);
  deptEls.forEach(el => el.innerText = u.department_name);

  const initials = u.full_name.split(" ").map(n => n[0]).slice(0, 2).join("");
  avatarEls.forEach(el => el.innerText = initials || "DR");
}

function openLoginModal() {
  const overlay = document.getElementById("loginOverlay");
  if (overlay) {
    overlay.classList.add("is-open");
    loadUsersForSwitcher();
  }
}

function closeLoginModal() {
  const overlay = document.getElementById("loginOverlay");
  if (overlay) overlay.classList.remove("is-open");
}

/**
 * Theme Management (Dark & Light Dual Modes)
 */
function getSavedTheme() {
  return localStorage.getItem("aegisrl-theme") || "dark";
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("aegisrl-theme", theme);

  const iconContainer = document.getElementById("themeToggleIcon");
  if (iconContainer) {
    if (theme === "light") {
      // Moon icon (to switch to dark)
      iconContainer.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    } else {
      // Sun icon (to switch to light)
      iconContainer.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    }
  }

  // Update Chart.js if loaded
  if (typeof decisionDistributionChart !== "undefined" && decisionDistributionChart) {
    decisionDistributionChart.update();
  }
  if (typeof scenarioPerformanceChart !== "undefined" && scenarioPerformanceChart) {
    const isLight = theme === "light";
    scenarioPerformanceChart.options.scales.x.ticks.color = isLight ? "#64748B" : "#94A3B8";
    scenarioPerformanceChart.options.scales.y.ticks.color = isLight ? "#64748B" : "#94A3B8";
    scenarioPerformanceChart.options.scales.y.grid.color = isLight ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.05)";
    scenarioPerformanceChart.options.plugins.legend.labels.color = isLight ? "#334155" : "#94A3B8";
    scenarioPerformanceChart.update();
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  showToast(`Switched to ${next === 'light' ? 'Light' : 'Dark'} Mode`, "info");
}

/**
 * System Health Check & Bootloader
 */
async function checkSystemHealth() {
  try {
    const health = await apiRequest("/health");
    const dbTest = await apiRequest("/db/test");

    const statusDot = document.getElementById("headerStatusDot");
    const statusText = document.getElementById("headerStatusText");
    const latencyPill = document.getElementById("headerLatencyPill");

    if (statusText) {
      statusText.innerText = dbTest.connected ? "Supabase PostgreSQL Live" : "Local Mock Mode";
    }
    if (latencyPill) {
      latencyPill.innerHTML = `${Icons.zap} Inference: &lt; 0.02 ms`;
    }
  } catch (err) {
    console.warn("Health check error:", err);
  }
}

// Global App Initialization on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  // Navigation Click Bindings
  document.querySelectorAll(".nav-link").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const page = item.getAttribute("data-page");
      if (page) navigateTo(page);
    });
  });

  // Mobile sidebar toggle
  const mobileToggle = document.getElementById("mobileMenuToggle");
  const sidebar = document.getElementById("appSidebar");
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open");
    });
  }

  // Profile click opens switcher
  const profileBadge = document.getElementById("sidebarUserProfile");
  if (profileBadge) {
    profileBadge.addEventListener("click", openLoginModal);
  }

  // Initial Load
  applyTheme(getSavedTheme());
  updateUserInterfaceProfile();
  checkSystemHealth();
  loadUsersForSwitcher();

  // Route to initial page (dashboard by default)
  const hash = window.location.hash.replace("#", "") || "dashboard";
  navigateTo(hash);
});
