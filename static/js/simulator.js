/**
 * Aegis-RL EHR Hospital Access Control
 * Attack Simulator & Interactive HTML5 Canvas Cyber Network Visualization
 */

let simulationHistory = [];
let networkAnimationId = null;
let canvasNetwork = null;
let canvasCtx = null;

// Cyber Network Topology Nodes
const networkNodes = [
  { id: "vault", label: "Core EHR Vault", x: 0.50, y: 0.48, color: "#38BDF8", radius: 24, type: "core" },
  { id: "gateway", label: "External Gateway", x: 0.20, y: 0.48, color: "#818CF8", radius: 18, type: "gateway" },
  { id: "attacker", label: "External Threat", x: 0.08, y: 0.22, color: "#EF4444", radius: 16, type: "attacker" },
  { id: "er", label: "Emergency Ward", x: 0.76, y: 0.22, color: "#10B981", radius: 18, type: "clinical" },
  { id: "cardio", label: "Cardiology", x: 0.84, y: 0.50, color: "#2DD4BF", radius: 16, type: "clinical" },
  { id: "neuro", label: "Neurology", x: 0.74, y: 0.78, color: "#2DD4BF", radius: 16, type: "clinical" },
  { id: "staff", label: "Internal Staff", x: 0.38, y: 0.82, color: "#F59E0B", radius: 16, type: "internal" }
];

// Connection Links between Nodes
const networkLinks = [
  { from: "attacker", to: "gateway" },
  { from: "gateway", to: "vault" },
  { from: "er", to: "vault" },
  { from: "cardio", to: "vault" },
  { from: "neuro", to: "vault" },
  { from: "staff", to: "vault" },
  { from: "staff", to: "gateway" }
];

// Active Packets traveling along links
let activePackets = [];
let activeBreachPulse = null;

/**
 * Initialize Simulator Page
 */
function initSimulatorPage() {
  setupNetworkCanvas();
  renderSimulationHistoryTable();
}

/**
 * Setup and Render HTML5 Canvas Cyber Network
 */
function setupNetworkCanvas() {
  canvasNetwork = document.getElementById("cyberNetworkCanvas");
  if (!canvasNetwork) return;

  canvasCtx = canvasNetwork.getContext("2d");

  function resize() {
    const rect = canvasNetwork.parentElement.getBoundingClientRect();
    canvasNetwork.width = rect.width * window.devicePixelRatio;
    canvasNetwork.height = rect.height * window.devicePixelRatio;
    canvasCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  resize();
  window.addEventListener("resize", resize);

  // Initialize random background packets
  if (activePackets.length === 0) {
    for (let i = 0; i < 6; i++) {
      spawnPacket(networkLinks[Math.floor(Math.random() * networkLinks.length)], "#38BDF8", 0.008);
    }
  }

  if (!networkAnimationId) {
    animateNetwork();
  }
}

function spawnPacket(link, color = "#38BDF8", speed = 0.012) {
  activePackets.push({
    fromId: link.from,
    toId: link.to,
    progress: 0,
    speed: speed,
    color: color
  });
}

/**
 * Canvas Animation Loop
 */
function animateNetwork() {
  if (!canvasNetwork || !canvasCtx) return;

  const w = canvasNetwork.width / window.devicePixelRatio;
  const h = canvasNetwork.height / window.devicePixelRatio;

  canvasCtx.clearRect(0, 0, w, h);

  // Draw Grid Lines in background
  canvasCtx.strokeStyle = "rgba(255, 255, 255, 0.025)";
  canvasCtx.lineWidth = 1;
  const gridSize = 40;
  for (let x = 0; x < w; x += gridSize) {
    canvasCtx.beginPath();
    canvasCtx.moveTo(x, 0);
    canvasCtx.lineTo(x, h);
    canvasCtx.stroke();
  }
  for (let y = 0; y < h; y += gridSize) {
    canvasCtx.beginPath();
    canvasCtx.moveTo(0, y);
    canvasCtx.lineTo(w, y);
    canvasCtx.stroke();
  }

  // Draw Links
  networkLinks.forEach(link => {
    const nFrom = networkNodes.find(n => n.id === link.from);
    const nTo = networkNodes.find(n => n.id === link.to);
    if (!nFrom || !nTo) return;

    const x1 = nFrom.x * w;
    const y1 = nFrom.y * h;
    const x2 = nTo.x * w;
    const y2 = nTo.y * h;

    canvasCtx.beginPath();
    canvasCtx.moveTo(x1, y1);
    canvasCtx.lineTo(x2, y2);
    canvasCtx.strokeStyle = "rgba(56, 189, 248, 0.14)";
    canvasCtx.lineWidth = 2;
    canvasCtx.stroke();
  });

  // Update & Draw Packets
  for (let i = activePackets.length - 1; i >= 0; i--) {
    const pkt = activePackets[i];
    pkt.progress += pkt.speed;

    const nFrom = networkNodes.find(n => n.id === pkt.fromId);
    const nTo = networkNodes.find(n => n.id === pkt.toId);

    if (nFrom && nTo) {
      const px = (nFrom.x + (nTo.x - nFrom.x) * pkt.progress) * w;
      const py = (nFrom.y + (nTo.y - nFrom.y) * pkt.progress) * h;

      canvasCtx.beginPath();
      canvasCtx.arc(px, py, 3.5, 0, Math.PI * 2);
      canvasCtx.fillStyle = pkt.color;
      canvasCtx.shadowColor = pkt.color;
      canvasCtx.shadowBlur = 10;
      canvasCtx.fill();
      canvasCtx.shadowBlur = 0;
    }

    if (pkt.progress >= 1) {
      activePackets.splice(i, 1);
      // Continuous background traffic
      if (activePackets.length < 5) {
        const randLink = networkLinks[Math.floor(Math.random() * networkLinks.length)];
        spawnPacket(randLink, "#38BDF8", 0.009);
      }
    }
  }

  // Draw Breach Pulse Shockwave if active
  if (activeBreachPulse) {
    activeBreachPulse.radius += 3.5;
    activeBreachPulse.opacity -= 0.025;

    const n = networkNodes.find(node => node.id === activeBreachPulse.nodeId);
    if (n && activeBreachPulse.opacity > 0) {
      canvasCtx.beginPath();
      canvasCtx.arc(n.x * w, n.y * h, activeBreachPulse.radius, 0, Math.PI * 2);
      canvasCtx.strokeStyle = activeBreachPulse.color;
      canvasCtx.globalAlpha = activeBreachPulse.opacity;
      canvasCtx.lineWidth = 2.5;
      canvasCtx.stroke();
      canvasCtx.globalAlpha = 1.0;
    } else {
      activeBreachPulse = null;
    }
  }

  // Draw Nodes
  networkNodes.forEach(node => {
    const nx = node.x * w;
    const ny = node.y * h;

    // Outer Glow Ring
    canvasCtx.beginPath();
    canvasCtx.arc(nx, ny, node.radius + 4, 0, Math.PI * 2);
    canvasCtx.fillStyle = "rgba(17, 24, 39, 0.85)";
    canvasCtx.fill();
    canvasCtx.strokeStyle = node.color;
    canvasCtx.lineWidth = 2;
    canvasCtx.stroke();

    // Inner Core
    canvasCtx.beginPath();
    canvasCtx.arc(nx, ny, node.radius - 4, 0, Math.PI * 2);
    canvasCtx.fillStyle = node.color;
    canvasCtx.shadowColor = node.color;
    canvasCtx.shadowBlur = 14;
    canvasCtx.fill();
    canvasCtx.shadowBlur = 0;

    // Node Label
    canvasCtx.fillStyle = "#F8FAFC";
    canvasCtx.font = "600 11px 'Plus Jakarta Sans', sans-serif";
    canvasCtx.textAlign = "center";
    canvasCtx.fillText(node.label, nx, ny + node.radius + 18);
  });

  networkAnimationId = requestAnimationFrame(animateNetwork);
}

/**
 * Run a Scenario Simulation
 */
async function runSimulation(scenarioName) {
  const statusEl = document.getElementById("canvasSimStatus");
  if (statusEl) {
    statusEl.innerText = `Simulating: ${scenarioName}...`;
  }

  // Trigger Visual Packet Bursts on Canvas
  if (scenarioName === "NORMAL_ACCESS") {
    spawnPacket({ from: "cardio", to: "vault" }, "#10B981", 0.022);
    spawnPacket({ from: "vault", to: "cardio" }, "#10B981", 0.022);
    activeBreachPulse = { nodeId: "cardio", radius: 10, opacity: 0.9, color: "#10B981" };
  } else if (scenarioName === "EMERGENCY_ACCESS") {
    spawnPacket({ from: "er", to: "vault" }, "#10B981", 0.035);
    activeBreachPulse = { nodeId: "er", radius: 10, opacity: 1.0, color: "#10B981" };
  } else if (scenarioName === "STOLEN_CREDENTIAL") {
    spawnPacket({ from: "attacker", to: "gateway" }, "#EF4444", 0.03);
    spawnPacket({ from: "gateway", to: "vault" }, "#EF4444", 0.03);
    activeBreachPulse = { nodeId: "attacker", radius: 10, opacity: 1.0, color: "#EF4444" };
  } else if (scenarioName === "INSIDER_MISUSE") {
    spawnPacket({ from: "staff", to: "vault" }, "#F59E0B", 0.028);
    activeBreachPulse = { nodeId: "staff", radius: 10, opacity: 1.0, color: "#F59E0B" };
  } else if (scenarioName === "MASS_ACCESS") {
    for (let k = 0; k < 5; k++) {
      setTimeout(() => {
        spawnPacket({ from: "attacker", to: "gateway" }, "#EF4444", 0.04);
        spawnPacket({ from: "gateway", to: "vault" }, "#EF4444", 0.04);
      }, k * 90);
    }
    activeBreachPulse = { nodeId: "gateway", radius: 10, opacity: 1.0, color: "#EF4444" };
  }

  try {
    const res = await apiRequest(`/simulate?scenario=${scenarioName}`);
    renderSimulationResult(res);

    // Save to history
    simulationHistory.unshift({
      scenario: scenarioName,
      action: res.rl_decision.action,
      reward: res.rl_decision.reward_awarded,
      latency: res.rl_decision.decision_time_ms,
      is_legit: res.hidden_ground_truth.is_legitimate,
      time: new Date().toLocaleTimeString()
    });

    renderSimulationHistoryTable();

    if (statusEl) {
      statusEl.innerText = `Decision: ${res.rl_decision.action} (${res.rl_decision.decision_time_ms.toFixed(3)} ms)`;
    }

    showToast(`Simulation [${scenarioName}] -> ${res.rl_decision.action}`, res.rl_decision.action === "ALLOW" ? "success" : "warning");
  } catch (err) {
    showToast(`Simulation Error: ${err.message}`, "error");
    if (statusEl) statusEl.innerText = "Error";
  }
}

/**
 * Render Simulation Detail Card
 */
function renderSimulationResult(simData) {
  const container = document.getElementById("simulationResultPanel");
  if (!container) return;

  const obs = simData.observable_features || {};
  const truth = simData.hidden_ground_truth || {};
  const dec = simData.rl_decision || {};
  const audit = simData.outcome_audit || {};

  container.style.display = "block";
  container.className = `decision-card ${dec.action}`;

  container.innerHTML = `
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:14px;margin-bottom:18px;">
      <div>
        <div class="decision-badge-large">
          <span>${dec.action}</span>
        </div>
        <p style="font-size:0.92rem;color:var(--text-1);font-weight:600;">
          ${dec.action_description}
        </p>
      </div>

      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
        <span class="pill-badge latency mono">
          ${Icons.zap} Latency: ${(dec.decision_time_ms || 0.016).toFixed(4)} ms
        </span>
        <span class="mono" style="font-size:0.75rem;color:${dec.reward_awarded > 0 ? '#34D399' : '#F87171'};font-weight:700;">
          Reward: ${dec.reward_awarded > 0 ? '+' : ''}${dec.reward_awarded.toFixed(1)}
        </span>
      </div>
    </div>

    <!-- 2 Column Comparison: Observable vs Hidden Ground Truth -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;margin:16px 0;">
      <!-- Observable by Agent -->
      <div style="background:rgba(0,0,0,0.25);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:16px;">
        <div style="font-size:0.75rem;font-weight:700;color:var(--blue-400);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
          ${Icons.shield} Observable Context (Agent Visible)
        </div>
        <div style="font-size:0.80rem;display:flex;flex-direction:column;gap:5px;color:var(--text-2);">
          <div>Role: <strong style="color:var(--text-1);">${obs.role}</strong></div>
          <div>Department Match: <strong style="color:${obs.dept_match ? '#34D399' : '#F87171'};">${obs.dept_match ? 'MATCH' : 'MISMATCH'}</strong></div>
          <div>Sensitivity: <strong style="color:#FBBF24;">${obs.sensitivity}</strong></div>
          <div>Location: <strong style="color:var(--text-1);">${obs.location}</strong></div>
          <div>Query Velocity: <strong style="color:var(--text-1);">${obs.frequency}</strong></div>
          <div>Emergency Override: <strong style="color:${obs.is_emergency ? '#F87171' : '#94A3B8'};">${obs.is_emergency ? 'ACTIVE' : 'NO'}</strong></div>
        </div>
      </div>

      <!-- Hidden Ground Truth -->
      <div style="background:rgba(0,0,0,0.25);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:16px;">
        <div style="font-size:0.75rem;font-weight:700;color:#2DD4BF;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
          ${Icons.crosshair} Hidden Ground Truth (Simulator Only)
        </div>
        <div style="font-size:0.80rem;display:flex;flex-direction:column;gap:5px;color:var(--text-2);">
          <div>Scenario: <strong style="color:var(--text-1);">${truth.scenario}</strong></div>
          <div>Legitimacy: <strong style="color:${truth.is_legitimate ? '#34D399' : '#EF4444'};">${truth.is_legitimate ? 'LEGITIMATE CLINICAL' : 'MALICIOUS ATTACK'}</strong></div>
          <div>Evaluation Correctness: <strong style="color:#34D399;">${audit.is_correct ? 'CORRECT SECURITY OUTCOME' : 'ANOMALY'}</strong></div>
          <div>Clinical Safety Outcome: <strong style="color:var(--text-1);">${audit.outcome}</strong></div>
        </div>
      </div>
    </div>

    <!-- Agent Rationale -->
    <div class="explanation-callout">
      <div style="font-weight:700;color:var(--text-1);font-size:0.80rem;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:4px;">
        Decision Rationale & Explainability
      </div>
      <div>${dec.explanation}</div>
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Render Simulation History Table
 */
function renderSimulationHistoryTable() {
  const tbody = document.getElementById("simHistoryTableBody");
  if (!tbody) return;

  if (simulationHistory.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-3);">No simulations run in this session yet. Click any scenario card above.</td></tr>`;
    return;
  }

  tbody.innerHTML = simulationHistory.slice(0, 10).map(s => {
    return `
      <tr>
        <td class="mono" style="color:var(--text-2);">${s.time}</td>
        <td style="font-weight:700;color:var(--text-1);">${s.scenario}</td>
        <td>
          <span class="status-badge ${s.action}">${s.action}</span>
        </td>
        <td class="mono" style="color:${s.reward > 0 ? '#34D399' : '#F87171'};font-weight:700;">
          ${s.reward > 0 ? '+' : ''}${s.reward.toFixed(1)}
        </td>
        <td class="mono" style="color:var(--text-3);">
          ${(s.latency || 0.016).toFixed(3)} ms
        </td>
      </tr>
    `;
  }).join("");
}
