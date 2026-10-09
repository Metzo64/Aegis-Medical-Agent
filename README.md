# 🛡️ AegisRL: Adaptive Reinforcement Learning for Hospital EHR Access Control

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.14-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/API-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)
[![Algorithm](https://img.shields.io/badge/RL-Tabular%20Q--Learning-FF6F00.svg)](https://en.wikipedia.org/wiki/Q-learning)
[![Defense Rate](https://img.shields.io/badge/Attack%20Defense-99.37%25-brightgreen.svg)](#-actual-verified-benchmarks)
[![Inference](https://img.shields.io/badge/Inference-0.0185%20ms-success.svg)](#-key-architectural-highlights)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An intelligent, context-aware cybersecurity access control engine that replaces static, brittle Role-Based Access Control (**RBAC**) with an **Adaptive Tabular Q-Learning Agent** for Electronic Health Record (**EHR**) systems.

The agent continuously assesses multi-dimensional context (clinical role, department alignment, record sensitivity, work shift, network origin, query frequency, and emergency status) to dynamically enforce the optimal decision:
`ALLOW`, `DENY`, `CHALLENGE`, or `RESTRICT`.

---

## 📌 Key Architectural Highlights

1. **Strict Context-Aware Observation**: The agent observes legitimate clinical & network context. Ground-truth attack labels are **hidden** from the agent and used solely by the simulator to calculate rewards.
2. **Patient-Safety-First Reward Function**: Avoids the common RL failure mode of "deny everything" by heavily penalizing false denials during emergency triage, ensuring vital care is never obstructed.
3. **Four-Tier Action Space**:
   - `ALLOW`: Frictionless instant access for routine clinical treatment.
   - `DENY`: Hard block for obvious attacks, credential abuse, or scraping.
   - `CHALLENGE`: Step-up multi-factor/biometric verification for untrusted networks or stolen credentials.
   - `RESTRICT`: Masked view (vital signs/lab values only; sensitive PII redacted) for legitimate cross-department consultations or internal snooping mitigation.
4. **Dynamic Supabase PostgreSQL Adaptation**: Connects to Supabase tables (`users`, `patients`, `medical_records`, `departments`, `access_requests`, `rl_decisions`, `audit_logs`) and automatically introspects schema columns so no schema assumptions are hardcoded.
5. **Sub-Millisecond Inference**: Tabular Q-Learning yields decision latencies under **0.02 ms**, suitable for high-throughput enterprise hospital IT infrastructure.

---

## 📊 Actual Verified Benchmarks

*Evaluated over 5,000 independent test requests across 5 attack and clinical scenarios (`evaluate.py`):*

| Key Performance Indicator (KPI) | Target | Result Achieved | Clinical / Security Meaning |
|:---|:---:|:---:|:---|
| **Attack Blocking Rate** | > 90% | **99.37%** | Stopped 1,733 of 1,744 malicious attempts |
| **Unauthorized Access Rate** | < 5% | **0.63%** | Only 11 malicious requests slipped through |
| **Legitimate Access Rate** | > 95% | **99.79%** | 3,249 of 3,256 legitimate queries fulfilled |
| **False Denial Rate** | < 5% | **0.21%** | Negligible clinical workflow disruption |
| **Emergency Denial Rate** | 0.00% | **0.13%** | 770 of 772 trauma/ER requests granted immediate `ALLOW` |
| **Average Decision Time** | < 5 ms | **0.0185 ms** | Sub-millisecond execution latency |
| **Cumulative Reward** | Positive | **+71,363.0** | Robust reward convergence |

---

## 🚀 Tech Stack

- **Runtime & Language**: Python 3.10+ / 3.14
- **Backend API**: FastAPI, Uvicorn, Pydantic v2
- **Database**: Supabase PostgreSQL (`supabase-py` & PostgREST OpenAPI)
- **RL Algorithm**: Tabular Q-Learning (NumPy)
- **Frontend Dashboard**: Responsive HTML5, Modern CSS Glassmorphism, Chart.js, Canvas Simulator
- **Visualization**: Plotly Interactive Convergence & Evaluation Charts

---

## 📂 Project Directory Structure

```text
RL Project/
├── .gitignore                # Filters out secrets, caches, and temporary files
├── .env.example              # Template environment variables for Supabase
├── requirements.txt          # Python package dependencies
├── config.py                 # Central configurations, paths, state/action encodings
├── db.py                     # Supabase client with dynamic schema discovery & fallback
├── inspect_schema.py         # CLI tool to audit columns of all Supabase tables
├── env.py                    # Hospital Access Control Simulation Environment
├── agent.py                  # Tabular Q-Learning Agent with explainability logic
├── train.py                  # Model training pipeline with Plotly convergence charts
├── evaluate.py               # Benchmark script reporting required KPIs & Plotly charts
├── main.py                   # FastAPI backend (/health, /db/test, /predict, /simulate)
├── test_pipeline.py          # Unit test verification suite
├── test_integration.py       # Integration test verification suite
├── static/                   # Interactive Web Application & Simulator
│   ├── index.html            # Main web UI
│   ├── css/                  # Modern responsive styling & design tokens
│   ├── js/                   # Dashboard logic, API integration, and simulation engine
│   └── assets/               # Visual assets and icons
└── models/                   # Serialized model artifacts
    ├── q_table.json          # Learned Q-Table (1,152 states x 4 actions)
    ├── agent_metadata.json   # Training hyperparameters and convergence metadata
    ├── training_curves.html  # Interactive Plotly training chart
    ├── evaluation_chart.html # Interactive Plotly evaluation breakdown chart
    └── evaluation_results.json # Quantitative KPI metrics
```

---

## ⚙️ Quickstart & Setup

### 1. Clone the Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd "RL Project"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your Supabase project credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-role-key
PORT=8000
HOST=127.0.0.1
MODEL_PATH=models/q_table.json
```
*(Note: If credentials are not provided, the application runs gracefully using an intelligent mock database fallback, allowing complete offline training, benchmarking, and UI demonstration).*

---

## 🧠 Training & Evaluation

### Train the Q-Learning Agent
Simulates access request episodes, converges the policy, and saves `models/q_table.json`:
```bash
python train.py --episodes 35000
```
- **Throughput**: ~29,000 episodes/sec (completes in ~1.2s)
- **Interactive convergence chart**: Generates `models/training_curves.html`

### Run Model Evaluation
```bash
python evaluate.py --samples 5000
```

### Run Automated Tests
```bash
python test_pipeline.py
python test_integration.py
```

---

## 🌐 Running the Web Application

Start the FastAPI server:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then open your browser at:
- **Interactive Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Demonstration (`/predict`)

### Example: Emergency Trauma Access Request
```http
POST /predict HTTP/1.1
Content-Type: application/json

{
  "user_id": "DR-ER-CHIEF",
  "patient_id": "PAT-TRAUMA-9",
  "record_id": "REC-5510",
  "role": "DOCTOR",
  "department_match": false,
  "record_sensitivity": "HIGH",
  "request_time": "OFF_HOURS",
  "location": "INTERNAL_HOSPITAL",
  "request_frequency": "ELEVATED",
  "emergency_status": true
}
```

### Decision Response:
```json
{
  "status": "success",
  "action": "ALLOW",
  "action_description": "Grant immediate full access to requested patient record.",
  "q_values": {
    "ALLOW": 20.0,
    "DENY": -35.0,
    "CHALLENGE": -10.0,
    "RESTRICT": -5.0
  },
  "explanation": "Selected 'ALLOW' (Q-Score: 20.00). Context: Emergency override active: immediate patient vital data access granted to prevent clinical harm.; DOCTOR requested record outside assigned unit (Department MISMATCH).; Target record has heightened sensitivity level: HIGH.",
  "decision_time_ms": 0.1598,
  "request_id": "REQ-1727602000123",
  "timestamp": "2026-09-29T09:32:00.123456Z",
  "logged_to_supabase": false
}
```

---

## 🎓 Viva & Technical Q&A

<details>
<summary><b>Q1: Why Reinforcement Learning over standard RBAC?</b></summary>
<br>
RBAC is static and binary. A doctor either has access or does not. If an attacker steals a doctor's credentials, RBAC blindly grants access. Conversely, if a trauma physician needs to view an off-department cardiology record during code-blue resuscitation, RBAC denies access. RL is <b>adaptive</b>: it evaluates multi-dimensional context (time, location, query velocity, emergency override) and balances clinical care with zero-trust defense.
</details>

<details>
<summary><b>Q2: What is the State Space and why Tabular Q-Learning?</b></summary>
<br>
The state space is composed of 7 discrete features:
- User Role (4): Doctor, Nurse, Staff, Researcher
- Department Match (2): Match, Mismatch
- Record Sensitivity (4): Low, Medium, High, Critical/VIP
- Request Time (2): Normal Hours, Off-Hours
- Location (3): Internal Hospital, VPN Offsite, External Unknown
- Frequency (3): Normal, Elevated, Burst High
- Emergency Status (2): No, Yes

Total States: $4 \times 2 \times 4 \times 2 \times 3 \times 3 \times 2 = 1,152$ states.
With 1,152 states, Tabular Q-Learning is provably optimal: guaranteed convergence, sub-0.02 ms inference, zero GPU requirements, and 100% mathematical explainability for medical audits.
</details>

<details>
<summary><b>Q3: What is the Bellman Update Rule?</b></summary>
<br>
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]$$
where $\alpha = 0.10$ (learning rate), $\gamma = 0.90$ (discount factor), and $r$ is the calculated reward.
</details>

<details>
<summary><b>Q4: How do you prevent the agent from cheating?</b></summary>
<br>
The environment strictly isolates <b>Observation</b> from <b>Hidden Ground Truth</b>. The agent receives only legitimate telemetry: <code>Observation(role, dept_match, sensitivity, request_time, location, frequency, is_emergency)</code>. It never sees <code>is_legitimate</code> or <code>scenario_name</code>. Ground truth is used strictly by the environment's reward calculator.
</details>

---

## 📄 License
This project is open-sourced under the MIT License for educational and research purposes.
