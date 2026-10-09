/**
 * Aegis-RL EHR Hospital Access Control
 * Real-time RL Decision Engine & 5-Step Animated Pipeline
 */

let lastEvaluatedDecision = null;

/**
 * Initialize Access Page
 */
function initAccessPage() {
  const container = document.getElementById("rlResultContainer");
  if (!container) return;
  if (!lastEvaluatedDecision) {
    container.className = "decision-card";
    container.style.display = "block";
    container.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
        <div style="width:36px;height:36px;border-radius:var(--r1);background:var(--blue-dim);border:1px solid var(--bdr-accent);display:flex;align-items:center;justify-content:center;color:var(--blue-400);flex-shrink:0;">
          ${Icons.cpu}
        </div>
        <div>
          <div style="font-size:0.90rem;font-weight:700;color:var(--text-1);">RL Policy Engine Standby</div>
          <div style="font-size:0.73rem;color:var(--text-3);">Tabular Q-Learning &bull; 1,152 States &bull; &lt;0.02ms Latency</div>
        </div>
      </div>
      <p style="font-size:0.80rem;color:var(--text-2);line-height:1.6;margin-bottom:14px;">
        Select an access scenario preset or configure request telemetry on the left, then click <strong>Evaluate Access Request</strong> to execute real-time zero-trust policy enforcement.
      </p>
      <div style="background:var(--surface-3);border:1px solid var(--bdr-1);border-radius:var(--r1);padding:12px 14px;font-size:0.75rem;color:var(--text-3);display:flex;flex-direction:column;gap:6px;">
        <div style="display:flex;justify-content:space-between;"><span>Discrete State Space:</span><strong class="mono" style="color:var(--text-1)">1,152 States</strong></div>
        <div style="display:flex;justify-content:space-between;"><span>Action Space:</span><strong class="mono" style="color:var(--text-1)">ALLOW, DENY, CHALLENGE, RESTRICT</strong></div>
        <div style="display:flex;justify-content:space-between;"><span>Exploitation Strategy:</span><strong class="mono" style="color:var(--green)">Greedy Policy (&epsilon; = 0.05)</strong></div>
        <div style="display:flex;justify-content:space-between;"><span>PostgreSQL Sync:</span><strong class="mono" style="color:var(--cyan-400)">Real-time Audit &amp; Decisions</strong></div>
      </div>
    `;
  }
}

/**
 * Pre-fill Access Form from Patient Records Page
 */
function prefillAccessForm(patient, recordId, sensitivity) {
  const u = AppState.currentUser;

  // Set Role
  const roleSelect = document.getElementById("accessRoleSelect");
  if (roleSelect) roleSelect.value = u.role_normalized || "DOCTOR";

  // Check Department Match
  const deptMatch = document.getElementById("accessDeptMatch");
  if (deptMatch && patient) {
    deptMatch.checked = (patient.department_id === u.department_id);
  }

  // Set Sensitivity
  const sensSelect = document.getElementById("accessSensitivitySelect");
  if (sensSelect && sensitivity) {
    sensSelect.value = sensitivity;
  }

  // Target Information Display
  const targetLabel = document.getElementById("accessTargetPatientLabel");
  if (targetLabel && patient) {
    const initials = (patient.full_name || '?').split(' ').map(n => n[0]).slice(0, 2).join('');
    targetLabel.innerHTML = `
      <div class="target-avatar">${initials}</div>
      <div class="target-info">
        <div class="target-name-row">
          <span class="target-name">${patient.full_name}</span>
          <span class="pat-code mono">${patient.patient_code}</span>
          <span class="target-dept-badge">${patient.department_name || 'Unit'}</span>
        </div>
        <div class="target-meta">
          Target Record: <span class="mono" style="color:var(--cyan-400);font-weight:600;">REC-${recordId}</span> &bull; Age ${patient.age} &bull; ${patient.gender}
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" onclick="navigateTo('patients')" style="margin-left:auto;">
        Browse Patients &rarr;
      </button>
    `;
  }
}

/**
 * Quick Presets
 */
function applyPreset(presetName) {
  const roleSelect = document.getElementById("accessRoleSelect");
  const deptMatch = document.getElementById("accessDeptMatch");
  const sensSelect = document.getElementById("accessSensitivitySelect");
  const timeSelect = document.getElementById("accessTimeSelect");
  const locSelect = document.getElementById("accessLocSelect");
  const freqSelect = document.getElementById("accessFreqSelect");
  const emergToggle = document.getElementById("accessEmergencyToggle");

  if (presetName === "emergency") {
    roleSelect.value = "DOCTOR";
    deptMatch.checked = false; // Cross-dept emergency
    sensSelect.value = "HIGH";
    timeSelect.value = "OFF_HOURS";
    locSelect.value = "INTERNAL_HOSPITAL";
    freqSelect.value = "ELEVATED";
    emergToggle.checked = true;
    showToast("Preset Loaded: Emergency Trauma Code Blue", "warning");
  } else if (presetName === "routine") {
    roleSelect.value = "DOCTOR";
    deptMatch.checked = true;
    sensSelect.value = "MEDIUM";
    timeSelect.value = "NORMAL_HOURS";
    locSelect.value = "INTERNAL_HOSPITAL";
    freqSelect.value = "NORMAL";
    emergToggle.checked = false;
    showToast("Preset Loaded: Routine Ward Consultation", "info");
  } else if (presetName === "snooping") {
    roleSelect.value = "STAFF";
    deptMatch.checked = false;
    sensSelect.value = "CRITICAL_VIP";
    timeSelect.value = "OFF_HOURS";
    locSelect.value = "EXTERNAL_UNKNOWN";
    freqSelect.value = "NORMAL";
    emergToggle.checked = false;
    showToast("Preset Loaded: Untrusted Offsite Snooping", "warning");
  } else if (presetName === "scraping") {
    roleSelect.value = "STAFF";
    deptMatch.checked = false;
    sensSelect.value = "HIGH";
    timeSelect.value = "NORMAL_HOURS";
    locSelect.value = "EXTERNAL_UNKNOWN";
    freqSelect.value = "BURST_HIGH";
    emergToggle.checked = false;
    showToast("Preset Loaded: Mass Automated Scraping", "error");
  }
}

/**
 * Run 5-Step Animated RL Evaluation Sequence
 */
async function triggerRLEvaluation() {
  const evalBtn = document.getElementById("btnEvaluateRequest");
  if (evalBtn) {
    evalBtn.disabled = true;
    evalBtn.innerHTML = `<span style="display:inline-block;animation:spin 1s linear infinite;">${Icons.cpu}</span> Evaluating...`;
  }

  // Gather Form Context
  const payload = {
    user_id: String(AppState.currentUser.user_id),
    patient_id: AppState.activeTargetPatient ? String(AppState.activeTargetPatient.patient_id) : "3008",
    record_id: AppState.activeTargetRecord ? String(AppState.activeTargetRecord.record_id) : "7057",
    role: document.getElementById("accessRoleSelect").value,
    department_match: document.getElementById("accessDeptMatch").checked,
    record_sensitivity: document.getElementById("accessSensitivitySelect").value,
    request_time: document.getElementById("accessTimeSelect").value,
    location: document.getElementById("accessLocSelect").value,
    request_frequency: document.getElementById("accessFreqSelect").value,
    emergency_status: document.getElementById("accessEmergencyToggle").checked
  };

  const progressLine = document.getElementById("pipelineLineProgress");
  const stepNodes = [
    document.getElementById("stepNode1"),
    document.getElementById("stepNode2"),
    document.getElementById("stepNode3"),
    document.getElementById("stepNode4"),
    document.getElementById("stepNode5")
  ];

  // Reset steps
  stepNodes.forEach(n => {
    if (n) {
      n.classList.remove("active", "completed");
    }
  });
  if (progressLine) progressLine.style.width = "0%";

  const resultContainer = document.getElementById("rlResultContainer");
  if (resultContainer) resultContainer.style.display = "none";

  // Fire backend API in parallel with animation
  let backendResponse = null;
  const apiPromise = apiRequest("/predict", {
    method: "POST",
    body: JSON.stringify(payload)
  }).then(res => {
    backendResponse = res;
    return res;
  }).catch(err => {
    showToast(`Inference Error: ${err.message}`, "error");
    return null;
  });

  // STEP 1: Request Received
  stepNodes[0]?.classList.add("active");
  if (progressLine) progressLine.style.width = "10%";
  await delay(280);

  // STEP 2: Analyzing Context
  stepNodes[0]?.classList.remove("active");
  stepNodes[0]?.classList.add("completed");
  stepNodes[1]?.classList.add("active");
  if (progressLine) progressLine.style.width = "35%";
  await delay(280);

  // STEP 3: Evaluating Behavior
  stepNodes[1]?.classList.remove("active");
  stepNodes[1]?.classList.add("completed");
  stepNodes[2]?.classList.add("active");
  if (progressLine) progressLine.style.width = "65%";
  await delay(280);

  // STEP 4: RL Agent Evaluating Q-Table
  stepNodes[2]?.classList.remove("active");
  stepNodes[2]?.classList.add("completed");
  stepNodes[3]?.classList.add("active");
  if (progressLine) progressLine.style.width = "90%";
  
  // Await actual response
  await apiPromise;
  await delay(250);

  // STEP 5: Decision Rendered
  stepNodes[3]?.classList.remove("active");
  stepNodes[3]?.classList.add("completed");
  stepNodes[4]?.classList.add("completed");
  if (progressLine) progressLine.style.width = "100%";

  if (evalBtn) {
    evalBtn.disabled = false;
    evalBtn.innerHTML = `${Icons.zap} Evaluate Access Request`;
  }

  if (backendResponse) {
    lastEvaluatedDecision = backendResponse;
    renderDecisionResultCard(backendResponse);
  }
}

/**
 * Render RL Decision Result Card
 */
function renderDecisionResultCard(res) {
  const container = document.getElementById("rlResultContainer");
  if (!container) return;

  const action = res.action; // ALLOW, DENY, CHALLENGE, RESTRICT
  const qVals = res.q_values || {};

  container.className = `decision-card ${action}`;
  container.style.display = "block";

  // Action Badge Icon
  let actionIcon = Icons.checkCircle;
  let actionColor = "#10B981";
  if (action === "DENY") {
    actionIcon = Icons.xCircle;
    actionColor = "#EF4444";
  } else if (action === "CHALLENGE") {
    actionIcon = Icons.alertTriangle;
    actionColor = "#F59E0B";
  } else if (action === "RESTRICT") {
    actionIcon = Icons.shield;
    actionColor = "#38BDF8";
  }

  // Calculate Normalized Q-Scores
  const qScores = [
    { name: "ALLOW", val: qVals.ALLOW ?? 0, color: "#10B981" },
    { name: "DENY", val: qVals.DENY ?? 0, color: "#EF4444" },
    { name: "CHALLENGE", val: qVals.CHALLENGE ?? 0, color: "#F59E0B" },
    { name: "RESTRICT", val: qVals.RESTRICT ?? 0, color: "#38BDF8" }
  ];

  const maxQ = Math.max(...qScores.map(s => Math.abs(s.val)), 1);

  const qBarsHtml = qScores.map(s => {
    const isChosen = s.name === action;
    const barWidth = Math.min(Math.max((Math.abs(s.val) / maxQ) * 100, 8), 100);
    return `
      <div class="q-bar-row">
        <span class="q-bar-label" style="${isChosen ? 'color:var(--text-1);font-weight:800;' : ''}">
          ${s.name} ${isChosen ? '&bull;' : ''}
        </span>
        <div class="q-bar-track">
          <div class="q-bar-fill" style="width:${barWidth}%;background:${s.color};opacity:${isChosen ? '1' : '0.5'};"></div>
        </div>
        <span class="q-bar-val" style="color:${isChosen ? s.color : '#94A3B8'};">
          ${s.val > 0 ? '+' : ''}${s.val.toFixed(2)}
        </span>
      </div>
    `;
  }).join("");

  container.innerHTML = `
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px;">
      <div>
        <div class="decision-badge-large">
          <span style="display:inline-block;width:24px;height:24px;">${actionIcon}</span>
          <span>${action}</span>
        </div>
        <p style="font-size:0.95rem;color:var(--text-1);font-weight:600;margin-bottom:8px;">
          ${res.action_description}
        </p>
      </div>

      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
        <span class="pill-badge latency mono" style="font-size:0.78rem;">
          ${Icons.zap} Inference: ${(res.decision_time_ms || 0.016).toFixed(4)} ms
        </span>
        <span class="mono" style="font-size:0.72rem;color:var(--text-3);">
          ${res.request_id}
        </span>
      </div>
    </div>

    <!-- Explanation Box -->
    <div class="explanation-callout">
      <div style="font-weight:700;color:var(--text-1);font-size:0.80rem;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
        ${Icons.cpu} RL Agent Explainability Rationale
      </div>
      <div>${res.explanation}</div>
    </div>

    <!-- Q-Score Value Slices -->
    <div style="margin-top:16px;">
      <div style="font-size:0.75rem;font-weight:700;color:var(--text-2);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
        Tabular Q-Values & Policy Weights:
      </div>
      <div class="q-scores-container">
        ${qBarsHtml}
      </div>
    </div>

    <!-- Actions & Supabase Logging Status -->
    <div style="display:flex;align-items:center;justify-content:space-between;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);margin-top:16px;flex-wrap:wrap;gap:12px;">
      <div style="display:flex;align-items:center;gap:8px;font-size:0.75rem;color:var(--text-2);">
        <span class="status-pulse" style="background:#10B981;"></span>
        <span>Synced to Supabase PostgreSQL (rl_decisions & audit_logs)</span>
      </div>

      <div style="display:flex;gap:10px;">
        ${action === "ALLOW" ? `
          <button class="btn btn-primary btn-sm" onclick="showRecordModal(false)">
            ${Icons.fileText} View Unlocked Record
          </button>
        ` : (action === "RESTRICT" ? `
          <button class="btn btn-primary btn-sm" onclick="showRecordModal(true)">
            ${Icons.shield} View Masked Record
          </button>
        ` : `
          <button class="btn btn-outline btn-sm" onclick="showToast('Access blocked by adaptive zero-trust security policy.', 'warning')">
            ${Icons.xCircle} Access Blocked
          </button>
        `)}
      </div>
    </div>
  `;

  // Scroll smoothly to result
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Record Modal for ALLOW or RESTRICT
 */
function showRecordModal(isMasked = false) {
  const patient = AppState.activeTargetPatient || { full_name: "Lavanya Agarwal", patient_code: "PAT-0001", age: 32, gender: "Other" };
  const recordId = AppState.activeTargetRecord ? AppState.activeTargetRecord.record_id : "7057";

  const modal = document.getElementById("recordInspectionModal");
  if (!modal) return;

  const contentBox = document.getElementById("recordModalContent");
  if (contentBox) {
    if (isMasked) {
      contentBox.innerHTML = `
        <div style="padding:14px;border-radius:8px;background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.25);margin-bottom:14px;color:var(--blue-400);font-size:0.82rem;">
          <strong>RESTRICTED / MASKED CLINICAL VIEW</strong><br/>
          PII (Name, SSN, Contact) redacted under Cross-Department Privacy Guard.
        </div>
        <p><strong>Patient Identifier:</strong> [REDACTED - HASHED: 8f4a***99b]</p>
        <p><strong>Clinical Department:</strong> Cardiology</p>
        <p><strong>Blood Pressure:</strong> 128/82 mmHg</p>
        <p><strong>Heart Rate:</strong> 74 bpm</p>
        <p><strong>Medication Chart:</strong> Synthetic medication for patient PAT-0001</p>
        <p><strong>Notes:</strong> [SENSITIVE PII MASKED ACCORDING TO ZERO-TRUST POLICY]</p>
      `;
    } else {
      contentBox.innerHTML = `
        <div style="padding:14px;border-radius:8px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);margin-bottom:14px;color:#34D399;font-size:0.82rem;">
          <strong>FULL CLINICAL ACCESS GRANTED</strong><br/>
          Full EHR clinical diagnostic record unlocked for routine care.
        </div>
        <p><strong>Patient Name:</strong> ${patient.full_name} (${patient.patient_code})</p>
        <p><strong>Age / Gender:</strong> ${patient.age} / ${patient.gender}</p>
        <p><strong>Record ID:</strong> REC-${recordId}</p>
        <p><strong>Diagnosis:</strong> Synthetic diagnosis and vital signs record for PAT-0001.</p>
        <p><strong>Prescription:</strong> Atorvastatin 20mg daily, Metoprolol 25mg BID.</p>
        <p><strong>Lab Results:</strong> Troponin I: &lt;0.03 ng/mL (Normal). ECG: Normal sinus rhythm.</p>
      `;
    }
  }

  modal.style.display = "flex";
}

function closeRecordModal() {
  const modal = document.getElementById("recordInspectionModal");
  if (modal) modal.style.display = "none";
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
