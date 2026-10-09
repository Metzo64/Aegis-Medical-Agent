# AegisRL: Concise Project Fact Sheet & Technical Reference

**Project Name:** AegisRL – Adaptive Reinforcement Learning for Hospital Record Access Control  
**Academic Domain:** Reinforcement Learning, Zero-Trust Cybersecurity, Healthcare Informatics  
**Primary Artifact:** Tabular Q-Learning Access Control Agent with Supabase PostgreSQL Integration  

---

## 1. Core Mathematical Specifications

### State Space ($\mathcal{S}$)
Discrete state tuple $\mathbf{s} \in \mathcal{S}$ composed of 7 contextual features:
$$\mathbf{s} = \langle \text{Role}, \text{DeptMatch}, \text{Sensitivity}, \text{RequestTime}, \text{Location}, \text{Frequency}, \text{IsEmergency} \rangle$$

$$\text{Total States } |\mathcal{S}| = 4 \times 2 \times 4 \times 2 \times 3 \times 3 \times 2 = 1,152 \text{ states}$$

- **Role (4):** `DOCTOR (0)`, `NURSE (1)`, `STAFF (2)`, `RESEARCHER (3)`
- **Dept Match (2):** `MISMATCH (0)`, `MATCH (1)`
- **Record Sensitivity (4):** `LOW (0)`, `MEDIUM (1)`, `HIGH (2)`, `CRITICAL_VIP (3)`
- **Request Time (2):** `NORMAL_HOURS (0)`, `OFF_HOURS (1)`
- **Location (3):** `INTERNAL_HOSPITAL (0)`, `VPN_OFFSITE (1)`, `EXTERNAL_UNKNOWN (2)`
- **Request Frequency (3):** `NORMAL <=5/min (0)`, `ELEVATED 6-20/min (1)`, `BURST_HIGH >20/min (2)`
- **Emergency Flag (2):** `NO (0)`, `YES (1)`

### Linear State Index Bijection Formula
$$\text{Index}(\mathbf{s}) = \text{Role} \times 288 + \text{DeptMatch} \times 144 + \text{Sensitivity} \times 36 + \text{RequestTime} \times 18 + \text{Location} \times 6 + \text{Frequency} \times 2 + \text{IsEmergency}$$

### Action Space ($\mathcal{A}$)
$$\mathcal{A} = \{ \text{ALLOW (0)}, \text{DENY (1)}, \text{CHALLENGE (2)}, \text{RESTRICT (3)} \}, \quad |\mathcal{A}| = 4$$

### Tabular Q-Learning Bellman Update Rule
$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha \left[ r_{t+1} + \gamma \max_{a' \in \mathcal{A}} Q(s_{t+1}, a') - Q(s_t, a_t) \right]$$

### Policy Execution
- **Training Exploration:** $\epsilon$-greedy policy with exponential decay $\epsilon_{k+1} = \max(\epsilon_{min}, \epsilon_k \times d)$
- **Inference Exploitation:** Deterministic argmax policy with uniform random tie-breaking:
$$a^* = \arg\max_{a \in \mathcal{A}} Q(s, a)$$

---

## 2. Hyperparameter Configuration Matrix

| Hyperparameter | Symbol | Verified Value | Implementation Source | Description |
| :--- | :---: | :---: | :--- | :--- |
| **Learning Rate** | $\alpha$ | `0.10` | `agent.py`, `train.py` | Step size for temporal-difference error updates |
| **Discount Factor** | $\gamma$ | `0.90` | `agent.py`, `train.py` | Weighting of future expected reward returns |
| **Initial Exploration** | $\epsilon_0$ | `1.00` | `agent.py`, `train.py` | Starting exploration probability (100% random) |
| **Minimum Exploration** | $\epsilon_{min}$ | `0.01` | `agent.py`, `train.py` | Floor exploration rate (1% random actions) |
| **Exploration Decay** | $d$ | `0.9998` | `train.py` | Multiplicative decay per episode |
| **Training Episodes** | $E$ | `35,000` | `train.py` | Total offline training iterations |
| **Random Seed** | $S_0$ | `42` | `env.py`, `train.py` | Deterministic pseudo-random number seed |
| **Evaluation Seed** | $S_{eval}$ | `100` | `evaluate.py` | Independent evaluation dataset seed |
| **Q-Table Matrix Shape** | $|\mathcal{S}| \times |\mathcal{A}|$ | `(1152, 4)` | `models/q_table.json` | 4,608 total floating point value entries |

---

## 3. Piecewise Clinical & Security Reward Function

$$R(s, a, \text{Scenario}) = \begin{cases} 
+20.0 & \text{if Scenario} = \text{EMERGENCY} \land a = \text{ALLOW} \\
-5.0 & \text{if Scenario} = \text{EMERGENCY} \land a = \text{RESTRICT} \\
-10.0 & \text{if Scenario} = \text{EMERGENCY} \land a = \text{CHALLENGE} \\
-35.0 & \text{if Scenario} = \text{EMERGENCY} \land a = \text{DENY (Critical Patient Safety Violation)} \\[6pt]

+12.0 & \text{if Scenario} = \text{NORMAL} \land a = \text{ALLOW} \\
+1.0 & \text{if Scenario} = \text{NORMAL} \land a = \text{CHALLENGE} \\
+3.0 & \text{if Scenario} = \text{NORMAL} \land a = \text{RESTRICT} \land \text{DeptMatch} = 0 \\
-3.0 & \text{if Scenario} = \text{NORMAL} \land a = \text{RESTRICT} \land \text{DeptMatch} = 1 \land \text{Role} \in \{\text{Doc, Nurse}\} \\
-18.0 & \text{if Scenario} = \text{NORMAL} \land a = \text{DENY (Clinical Friction)} \\[6pt]

+18.0 & \text{if Scenario} = \text{STOLEN\_CREDENTIAL} \land a = \text{DENY} \\
+14.0 & \text{if Scenario} = \text{STOLEN\_CREDENTIAL} \land a = \text{CHALLENGE} \\
-8.0 & \text{if Scenario} = \text{STOLEN\_CREDENTIAL} \land a = \text{RESTRICT} \\
-30.0 & \text{if Scenario} = \text{STOLEN\_CREDENTIAL} \land a = \text{ALLOW (Severe Data Breach)} \\[6pt]

+15.0 & \text{if Scenario} = \text{INSIDER\_MISUSE} \land a = \text{DENY} \\
+8.0 & \text{if Scenario} = \text{INSIDER\_MISUSE} \land a = \text{RESTRICT (Containment)} \\
+6.0 & \text{if Scenario} = \text{INSIDER\_MISUSE} \land a = \text{CHALLENGE} \\
-22.0 & \text{if Scenario} = \text{INSIDER\_MISUSE} \land a = \text{ALLOW} \\[6pt]

+20.0 & \text{if Scenario} = \text{MASS\_ACCESS} \land a = \text{DENY} \\
+8.0 & \text{if Scenario} = \text{MASS\_ACCESS} \land a = \text{CHALLENGE} \\
-10.0 & \text{if Scenario} = \text{MASS\_ACCESS} \land a = \text{RESTRICT} \\
-35.0 & \text{if Scenario} = \text{MASS\_ACCESS} \land a = \text{ALLOW (Mass Exfiltration)}
\end{cases}$$

---

## 4. Verified Experimental Evaluation Metrics

Evaluated on $N = 5,000$ independent synthetic test requests:

| Evaluation Metric | Formula / Definition | Measured Value | Target | Verification Status |
| :--- | :--- | :---: | :---: | :---: |
| **Attack Blocking Rate** | $\frac{\text{Attacks Blocked}}{\text{Total Simulated Attacks}} \times 100$ | **$99.37\%$** | $> 90.0\%$ | **EXCEEDED** |
| **Legitimate Access Rate** | $\frac{\text{Legitimate Granted}}{\text{Total Legitimate Requests}} \times 100$ | **$99.79\%$** | $> 95.0\%$ | **EXCEEDED** |
| **False Denial Rate** | $\frac{\text{Legitimate Denied}}{\text{Total Legitimate Requests}} \times 100$ | **$0.21\%$** | $< 5.0\%$ | **EXCEEDED** |
| **Emergency Denial Rate** | $\frac{\text{Emergency Denied}}{\text{Total Emergency Requests}} \times 100$ | **$0.13\%$** | $< 1.0\%$ | **EXCEEDED** |
| **Unauthorized Access Rate**| $\frac{\text{Attacks Allowed}}{\text{Total Simulated Attacks}} \times 100$ | **$0.63\%$** | $< 5.0\%$ | **EXCEEDED** |
| **Cumulative Reward** | $\sum_{t=1}^{5000} r_t$ | **$+71,363.0$** | $> 0$ | **VERIFIED** |
| **Pure RL Latency** | Direct in-memory Q-row argmax query | **$0.0184\text{ ms}$** | $< 1.0\text{ ms}$ | **VERIFIED** |
| **p95 Latency** | 95th percentile decision latency | **$0.0222\text{ ms}$** | $< 2.0\text{ ms}$ | **VERIFIED** |

---

## 5. Supabase PostgreSQL Schema Overview

- **Host:** `https://gynbanyrvxrygiliovtz.supabase.co`
- **Engine:** PostgreSQL 15+ / PostgREST REST API
- **Tables:**
  1. `users` (100 rows): `user_id` (PK), `username`, `full_name`, `role`, `department_id`, `usual_location`
  2. `patients` (1,000 rows): `patient_id` (PK), `patient_code`, `full_name`, `age`, `gender`, `department_id`
  3. `medical_records` (3,548 rows): `record_id` (PK), `patient_id` (FK), `record_type`, `sensitivity`, `record_content`
  4. `departments` (5 rows): `department_id` (PK), `department_name`
  5. `access_requests` (10,052+ rows): `request_id` (PK), `user_id` (FK), `patient_id` (FK), `record_id` (FK), `location`, `emergency_status`, `department_match`, `scenario_type`
  6. `rl_decisions` (48+ rows): `decision_id` (PK), `request_id` (FK), `algorithm`, `action`, `reward`, `decision_time_ms`
  7. `audit_logs` (48+ rows): `audit_id` (PK), `request_id` (FK), `user_id` (FK), `action`, `event_description`, `logged_at`
