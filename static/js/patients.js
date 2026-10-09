/**
 * Aegis-RL EHR Hospital Access Control
 * Patient Records Browsing, Search, and Detail Drawer
 */

let activeDepartmentFilter = null;
let currentPatientRecords = [];

/**
 * Initialize Patients Page
 */
async function loadPatientsPage() {
  const searchInput = document.getElementById("patientSearchInput");
  if (searchInput) {
    searchInput.value = "";
  }
  await fetchAndRenderPatients();
}

/**
 * Fetch and Render Patient Cards
 */
async function fetchAndRenderPatients(query = "", deptId = null) {
  const container = document.getElementById("patientsGridContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align:center; padding: 48px; color: #64748B;">
      <div style="margin-bottom:12px;display:inline-block;animation:spin 1s linear infinite;">${Icons.cpu}</div>
      <div>Loading patient records from Supabase...</div>
    </div>
  `;

  try {
    let url = `/api/patients?limit=30`;
    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (deptId) url += `&department_id=${deptId}`;

    const data = await apiRequest(url);
    const patients = data.patients || [];
    AppState.patientsCache = patients;

    if (patients.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding: 48px; color: #64748B;">
          <div>No patients matching "${query || 'filter'}" found in database.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = patients.map(p => {
      return `
        <div class="patient-grid-card" onclick="openPatientDrawer(${p.patient_id})">
          <div class="patient-header">
            <span class="pat-code">${p.patient_code}</span>
            <span class="sens-badge sens-MEDIUM">${p.department_name}</span>
          </div>
          <div>
            <div class="pat-name">${p.full_name}</div>
            <div style="font-size:0.75rem;color:var(--text-2);margin-top:2px;">
              ${p.age} yrs &bull; ${p.gender} &bull; ID: ${p.patient_id}
            </div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);font-size:0.75rem;">
            <span style="color:var(--text-3);">Clinical EHR Records</span>
            <span style="color:var(--blue-400);font-weight:600;display:flex;align-items:center;gap:4px;">
              View Records &rarr;
            </span>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align:center; padding: 48px; color: #EF4444;">
        Failed to load patients: ${err.message}
      </div>
    `;
  }
}

/**
 * Filter by Department
 */
function setPatientDeptFilter(deptId) {
  activeDepartmentFilter = deptId;
  document.querySelectorAll(".dept-filter-btn").forEach(btn => {
    const bId = btn.getAttribute("data-dept");
    btn.classList.toggle("btn-primary", bId == deptId || (!deptId && !bId));
    btn.classList.toggle("btn-outline", !(bId == deptId || (!deptId && !bId)));
  });

  const searchInput = document.getElementById("patientSearchInput");
  fetchAndRenderPatients(searchInput ? searchInput.value : "", deptId);
}

/**
 * Live Search Debounce Handler
 */
let patientSearchTimeout = null;
function handlePatientSearchInput(e) {
  clearTimeout(patientSearchTimeout);
  const val = e.target.value.trim();
  patientSearchTimeout = setTimeout(() => {
    fetchAndRenderPatients(val, activeDepartmentFilter);
  }, 250);
}

/**
 * Patient Drawer - Inspect Patient and their Medical Records
 */
async function openPatientDrawer(patientId) {
  const patient = AppState.patientsCache.find(p => p.patient_id === patientId);
  if (!patient) return;

  const drawer = document.getElementById("patientDrawer");
  const backdrop = document.getElementById("drawerBackdrop");
  if (!drawer || !backdrop) return;

  // Fill Header
  document.getElementById("drawerPatientName").innerText = patient.full_name;
  document.getElementById("drawerPatientCode").innerText = patient.patient_code;
  document.getElementById("drawerPatientMeta").innerText = `${patient.age} yrs • ${patient.gender} • ${patient.department_name}`;

  // Fetch real records
  const recordsContainer = document.getElementById("drawerRecordsList");
  recordsContainer.innerHTML = `<div style="text-align:center;padding:24px;color:var(--text-3);">Fetching patient records from database...</div>`;

  backdrop.classList.add("open");
  drawer.classList.add("open");

  try {
    const data = await apiRequest(`/api/patients/${patientId}/records`);
    currentPatientRecords = data.records || [];

    if (currentPatientRecords.length === 0) {
      recordsContainer.innerHTML = `
        <div style="text-align:center;padding:32px;color:var(--text-3);">
          No medical records on file for this patient.
        </div>
      `;
      return;
    }

    recordsContainer.innerHTML = currentPatientRecords.map(r => {
      const sens = r.sensitivity_level || "MEDIUM";
      return `
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:16px;margin-bottom:12px;transition:all 160ms;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div style="font-weight:700;font-size:0.90rem;color:var(--text-1);">${r.record_type} Record</div>
            <span class="sens-badge sens-${sens}">${sens}</span>
          </div>
          <div style="font-size:0.78rem;color:var(--text-2);margin-bottom:12px;line-height:1.4;">
            ${r.record_content || 'Encrypted diagnostic chart / vitals data.'}
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.04);">
            <span class="mono" style="font-size:0.72rem;color:var(--text-3);">REC-${r.record_id}</span>
            <button class="btn btn-primary btn-sm" onclick="requestAccessFromDrawer(${patient.patient_id}, ${r.record_id}, '${sens}', '${r.record_type}')">
              ${Icons.zap} Request Access
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    recordsContainer.innerHTML = `<div style="color:var(--red);padding:16px;">Failed to load records: ${err.message}</div>`;
  }
}

function closePatientDrawer() {
  const drawer = document.getElementById("patientDrawer");
  const backdrop = document.getElementById("drawerBackdrop");
  if (drawer) drawer.classList.remove("open");
  if (backdrop) backdrop.classList.remove("open");
}

/**
 * Shortcut from Drawer to RL Decision Page
 */
function requestAccessFromDrawer(patientId, recordId, sensitivity, recordType) {
  const patient = AppState.patientsCache.find(p => p.patient_id === patientId);
  closePatientDrawer();

  // Pre-populate target in AppState
  AppState.activeTargetPatient = patient;
  AppState.activeTargetRecord = {
    record_id: recordId,
    record_type: recordType,
    sensitivity: sensitivity
  };

  navigateTo("access");

  // Pre-fill the access form
  if (typeof prefillAccessForm === "function") {
    prefillAccessForm(patient, recordId, sensitivity);
  }
}
