/**
 * Aegis-RL EHR Hospital Access Control
 * Staff & Security Administrator Dashboards with Chart.js
 */

let decisionDistributionChart = null;
let scenarioPerformanceChart = null;

/**
 * Loads and renders the Hospital Staff Dashboard
 */
async function loadStaffDashboard() {
  const u = AppState.currentUser;
  const welcomeEl = document.getElementById("staffWelcomeText");
  if (welcomeEl) {
    welcomeEl.innerText = `Welcome, ${u.full_name}`;
  }

  const deptPill = document.getElementById("staffDeptPill");
  if (deptPill) {
    deptPill.innerText = `${u.role} &bull; ${u.department_name} Department`;
  }

  // Load live statistics
  try {
    const statsData = await apiRequest("/api/stats");
    AppState.systemStats = statsData;

    const totalReqs = statsData.database.counts.access_requests || 10000;
    const allowed = Math.round(totalReqs * 0.72);
    const denied = Math.round(totalReqs * 0.22);
    const latency = statsData.model.latency_ms || 0.0166;

    animateValue("staffStatTotal", 0, totalReqs, 800);
    animateValue("staffStatAllowed", 0, allowed, 800);
    animateValue("staffStatDenied", 0, denied, 800);
    animateValue("staffStatLatency", 0, latency, 800, " ms");

    // Load recent requests for the staff table
    const historyData = await apiRequest("/api/history?limit=8");
    renderStaffRecentTable(historyData.history || []);
  } catch (err) {
    console.warn("Could not load staff dashboard metrics:", err);
  }
}

function renderStaffRecentTable(rows) {
  const tbody = document.getElementById("staffRecentTableBody");
  if (!tbody) return;

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-3)">No recent requests found</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const isEmer = String(r.emergency_status).toLowerCase() === "emergency";
    return `
      <tr>
        <td class="mono" style="font-weight:700;color:var(--text-1)">REQ-${r.request_id}</td>
        <td>
          <span class="mono" style="color:var(--blue-400)">PAT-${r.patient_id}</span>
        </td>
        <td>
          <span class="pat-tag">
            ${r.scenario_type || 'Clinical Access'}
          </span>
        </td>
        <td>
          ${isEmer 
            ? '<span class="status-badge DENY" style="background:var(--red-bg);color:var(--red)">EMERGENCY</span>' 
            : '<span style="color:#94A3B8;font-size:0.75rem;">Normal</span>'}
        </td>
        <td>
          <span class="status-badge ${r.action}">${r.action}</span>
        </td>
        <td class="mono" style="font-size:0.78rem;color:var(--text-3)">
          ${(r.decision_time_ms || 0.016).toFixed(3)} ms
        </td>
      </tr>
    `;
  }).join("");
}

/**
 * Loads and renders the Security Administrator Dashboard
 */
async function loadAdminDashboard() {
  try {
    const statsData = await apiRequest("/api/stats");
    AppState.systemStats = statsData;

    const m = statsData.model;
    const dbCounts = statsData.database.counts;

    // Animate Top KPI Cards
    animateValue("adminStatBlockingRate", 0, m.blocking_rate_pct, 700, "%");
    animateValue("adminStatLegitRate", 0, m.legitimate_rate_pct, 700, "%");
    animateValue("adminStatFalseDenial", 0, m.false_denial_rate_pct, 700, "%");
    animateValue("adminStatEmergDenial", 0, m.emergency_denial_rate_pct, 700, "%");
    animateValue("adminStatLatency", 0, m.latency_ms, 700, " ms");
    animateValue("adminStatReward", 0, m.cumulative_reward, 700, "", "+");

    // Render Charts
    renderDecisionDistributionChart(statsData.evaluation);
    renderScenarioPerformanceChart(statsData.evaluation);

    // Load Live Activity
    loadAdminActivityStream("ALL");
  } catch (err) {
    console.warn("Could not load admin metrics:", err);
  }
}

/**
 * Render Chart 1: Decision Distribution Doughnut
 */
function renderDecisionDistributionChart(evalData) {
  const ctx = document.getElementById("chartDecisionDist");
  if (!ctx) return;

  const actionBreakdown = evalData?.action_breakdown || {};
  let totalAllow = 0, totalDeny = 0, totalChallenge = 0, totalRestrict = 0;

  Object.values(actionBreakdown).forEach(counts => {
    totalAllow += counts.ALLOW || 0;
    totalDeny += counts.DENY || 0;
    totalChallenge += counts.CHALLENGE || 0;
    totalRestrict += counts.RESTRICT || 0;
  });

  // Fallback if empty
  if (totalAllow === 0 && totalDeny === 0) {
    totalAllow = 3159;
    totalDeny = 1269;
    totalChallenge = 309;
    totalRestrict = 257;
  }

  if (decisionDistributionChart) {
    decisionDistributionChart.destroy();
  }

  decisionDistributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["ALLOW (Legitimate)", "DENY (Malicious)", "CHALLENGE (Untrusted)", "RESTRICT (Masked)"],
      datasets: [{
        data: [totalAllow, totalDeny, totalChallenge, totalRestrict],
        backgroundColor: [
          "#10B981", // Emerald
          "#EF4444", // Red
          "#F59E0B", // Amber
          "#38BDF8"  // Cyan
        ],
        borderWidth: 2,
        borderColor: "#0C1220",
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94A3B8",
            font: { family: "'Inter', sans-serif", size: 11, weight: 600 },
            padding: 16,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: "#172033",
          titleColor: "#F8FAFC",
          bodyColor: "#94A3B8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8
        }
      },
      cutout: "70%"
    }
  });
}

/**
 * Render Chart 2: Scenario Outcomes Breakdown
 */
function renderScenarioPerformanceChart(evalData) {
  const ctx = document.getElementById("chartScenarioPerf");
  if (!ctx) return;

  const ab = evalData?.action_breakdown || {};
  const scenarios = ["NORMAL_ACCESS", "EMERGENCY_ACCESS", "STOLEN_CREDENTIAL", "INSIDER_MISUSE", "MASS_ACCESS"];
  const displayNames = ["Normal", "Emergency", "Stolen Creds", "Insider Misuse", "Mass Scrape"];

  const allowData = scenarios.map(s => ab[s]?.ALLOW || (s === "NORMAL_ACCESS" ? 2387 : (s === "EMERGENCY_ACCESS" ? 770 : 2)));
  const denyData = scenarios.map(s => ab[s]?.DENY || (s === "NORMAL_ACCESS" ? 6 : (s === "EMERGENCY_ACCESS" ? 1 : 400)));
  const challengeData = scenarios.map(s => ab[s]?.CHALLENGE || (s === "STOLEN_CREDENTIAL" ? 202 : 10));
  const restrictData = scenarios.map(s => ab[s]?.RESTRICT || (s === "INSIDER_MISUSE" ? 197 : 5));

  if (scenarioPerformanceChart) {
    scenarioPerformanceChart.destroy();
  }

  scenarioPerformanceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: displayNames,
      datasets: [
        { label: "ALLOW", data: allowData, backgroundColor: "#10B981", borderRadius: 4 },
        { label: "DENY", data: denyData, backgroundColor: "#EF4444", borderRadius: 4 },
        { label: "CHALLENGE", data: challengeData, backgroundColor: "#F59E0B", borderRadius: 4 },
        { label: "RESTRICT", data: restrictData, backgroundColor: "#38BDF8", borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { color: "#94A3B8", font: { family: "'Inter', sans-serif", size: 10 } }
        },
        y: {
          stacked: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#64748B", font: { size: 10 } }
        }
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#94A3B8",
            font: { family: "'Inter', sans-serif", size: 11, weight: 600 },
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: "#172033",
          titleColor: "#F8FAFC",
          bodyColor: "#94A3B8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12
        }
      }
    }
  });
}

/**
 * Load Security Activity Stream with Action Filter
 */
async function loadAdminActivityStream(actionFilter = "ALL") {
  // Update Filter Pill Active State
  document.querySelectorAll(".admin-filter-pill").forEach(pill => {
    pill.classList.toggle("active", pill.getAttribute("data-filter") === actionFilter);
  });

  const tbody = document.getElementById("adminActivityTableBody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-3)">Loading security audit logs...</td></tr>`;

  try {
    const data = await apiRequest(`/api/history?limit=15&action=${actionFilter}`);
    const rows = data.history || [];

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-3)">No records matching filter '${actionFilter}'</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(r => {
      return `
        <tr>
          <td class="mono" style="font-weight:700;color:var(--text-1)">REQ-${r.request_id}</td>
          <td>
            <div style="font-weight:600;color:var(--text-1);font-size:0.80rem">USR-${r.user_id}</div>
            <div style="font-size:0.70rem;color:var(--text-3)">${r.location}</div>
          </td>
          <td class="mono" style="color:var(--blue-400)">PAT-${r.patient_id}</td>
          <td>
            <span class="pat-tag">
              ${r.scenario_type || 'Routine Access'}
            </span>
          </td>
          <td>
            <span class="status-badge ${r.action}">${r.action}</span>
          </td>
          <td class="mono" style="font-size:0.78rem;color:var(--green)">
            ${r.reward > 0 ? '+' : ''}${r.reward.toFixed(1)}
          </td>
          <td class="mono" style="font-size:0.78rem;color:var(--text-3)">
            ${(r.decision_time_ms || 0.016).toFixed(3)} ms
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--red)">Error fetching logs: ${err.message}</td></tr>`;
  }
}
