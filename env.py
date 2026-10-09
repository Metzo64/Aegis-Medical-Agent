"""
Simulation Environment for Hospital Access Control.
Models access requests as a Markov Decision Process (MDP) / Contextual Decision Process.

Requirements satisfied:
- Generates 5 simulated access patterns:
    1. Normal access
    2. Simulated stolen-credential misuse
    3. Insider-like misuse
    4. Mass access attempt
    5. Emergency access
- State features observed by agent:
    user role, department match, record sensitivity,
    request time, location, request frequency, emergency status.
- HIDDEN labels (scenario, is_legitimate) are NOT exposed in observation.
- Four actions: ALLOW, DENY, CHALLENGE, RESTRICT.
- Clinically sound reward function balancing patient safety and data security.
"""

import random
import time
from typing import Tuple, Dict, Any, Optional, NamedTuple
import numpy as np

from config import (
    ACTIONS, ACTION_ALLOW, ACTION_DENY, ACTION_CHALLENGE, ACTION_RESTRICT,
    ROLES, ROLE_MAP,
    SENSITIVITIES, SENSITIVITY_MAP,
    LOCATIONS, LOCATION_MAP,
    FREQUENCIES, FREQUENCY_MAP,
    REQUEST_TIMES, TIME_MAP
)

# Number of discrete states in Tabular Q-Learning:
# 4 roles * 2 dept_match * 4 sensitivities * 2 times * 3 locations * 3 frequencies * 2 emergency
NUM_ROLES = len(ROLES)              # 4
NUM_DEPT_MATCH = 2                 # 2 (0=No, 1=Yes)
NUM_SENSITIVITIES = len(SENSITIVITIES) # 4
NUM_TIMES = len(REQUEST_TIMES)     # 2 (0=Normal, 1=Off-hours)
NUM_LOCATIONS = len(LOCATIONS)     # 3
NUM_FREQUENCIES = len(FREQUENCIES) # 3
NUM_EMERGENCY = 2                  # 2 (0=No, 1=Yes)

TOTAL_STATES = (
    NUM_ROLES *
    NUM_DEPT_MATCH *
    NUM_SENSITIVITIES *
    NUM_TIMES *
    NUM_LOCATIONS *
    NUM_FREQUENCIES *
    NUM_EMERGENCY
)  # Exactly 1,152 states


class Observation(NamedTuple):
    role: int            # 0: DOCTOR, 1: NURSE, 2: STAFF, 3: RESEARCHER
    dept_match: int      # 0: Mismatch, 1: Match
    sensitivity: int     # 0: LOW, 1: MEDIUM, 2: HIGH, 3: CRITICAL_VIP
    request_time: int    # 0: NORMAL_HOURS, 1: OFF_HOURS
    location: int        # 0: INTERNAL_HOSPITAL, 1: VPN_OFFSITE, 2: EXTERNAL_UNKNOWN
    frequency: int       # 0: NORMAL (<=5/min), 1: ELEVATED (6-20/min), 2: BURST_HIGH (>20/min)
    is_emergency: int    # 0: No, 1: Yes


class AccessRequestEnvironment:
    """
    Hospital Access Control Reinforcement Learning Environment.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.num_actions = len(ACTIONS)
        self.total_states = TOTAL_STATES
        self.current_state: Optional[Observation] = None
        self.current_meta: Dict[str, Any] = {}
        self.step_count = 0

    @staticmethod
    def state_to_index(obs: Observation) -> int:
        """
        Converts the discrete observation tuple into a unique linear state index (0 to 1151).
        """
        idx = (
            obs.role * (NUM_DEPT_MATCH * NUM_SENSITIVITIES * NUM_TIMES * NUM_LOCATIONS * NUM_FREQUENCIES * NUM_EMERGENCY) +
            obs.dept_match * (NUM_SENSITIVITIES * NUM_TIMES * NUM_LOCATIONS * NUM_FREQUENCIES * NUM_EMERGENCY) +
            obs.sensitivity * (NUM_TIMES * NUM_LOCATIONS * NUM_FREQUENCIES * NUM_EMERGENCY) +
            obs.request_time * (NUM_LOCATIONS * NUM_FREQUENCIES * NUM_EMERGENCY) +
            obs.location * (NUM_FREQUENCIES * NUM_EMERGENCY) +
            obs.frequency * (NUM_EMERGENCY) +
            obs.is_emergency
        )
        return int(idx)

    @staticmethod
    def index_to_state(idx: int) -> Observation:
        """
        Converts a linear state index back to an Observation tuple.
        """
        rem = idx
        is_emergency = rem % NUM_EMERGENCY
        rem //= NUM_EMERGENCY
        frequency = rem % NUM_FREQUENCIES
        rem //= NUM_FREQUENCIES
        location = rem % NUM_LOCATIONS
        rem //= NUM_LOCATIONS
        request_time = rem % NUM_TIMES
        rem //= NUM_TIMES
        sensitivity = rem % NUM_SENSITIVITIES
        rem //= NUM_SENSITIVITIES
        dept_match = rem % NUM_DEPT_MATCH
        rem //= NUM_DEPT_MATCH
        role = rem % NUM_ROLES
        return Observation(role, dept_match, sensitivity, request_time, location, frequency, is_emergency)

    def generate_request(self, scenario_override: Optional[str] = None) -> Tuple[Observation, Dict[str, Any]]:
        """
        Generates a synthetic access request from one of five realistic scenarios:
          1. NORMAL_ACCESS
          2. EMERGENCY_ACCESS
          3. STOLEN_CREDENTIAL
          4. INSIDER_MISUSE
          5. MASS_ACCESS
        Returns:
          - obs: Observation tuple (visible to the agent)
          - hidden_meta: Ground-truth metadata (NOT given to agent; used by simulator for reward/eval)
        """
        if scenario_override:
            scenario = scenario_override
        else:
            # Distribution of incoming hospital access traffic
            scenario = random.choices(
                ["NORMAL_ACCESS", "EMERGENCY_ACCESS", "STOLEN_CREDENTIAL", "INSIDER_MISUSE", "MASS_ACCESS"],
                weights=[0.50, 0.15, 0.12, 0.12, 0.11],
                k=1
            )[0]

        if scenario == "NORMAL_ACCESS":
            # Legitimate routine clinical workflows
            role = random.choices([ROLE_MAP["DOCTOR"], ROLE_MAP["NURSE"], ROLE_MAP["STAFF"]], weights=[0.55, 0.35, 0.10])[0]
            dept_match = random.choices([1, 0], weights=[0.92, 0.08])[0]
            sensitivity = random.choices([SENSITIVITY_MAP["LOW"], SENSITIVITY_MAP["MEDIUM"], SENSITIVITY_MAP["HIGH"]], weights=[0.45, 0.40, 0.15])[0]
            request_time = random.choices([TIME_MAP["NORMAL_HOURS"], TIME_MAP["OFF_HOURS"]], weights=[0.85, 0.15])[0]
            location = random.choices([LOCATION_MAP["INTERNAL_HOSPITAL"], LOCATION_MAP["VPN_OFFSITE"]], weights=[0.85, 0.15])[0]
            frequency = random.choices([FREQUENCY_MAP["NORMAL"], FREQUENCY_MAP["ELEVATED"]], weights=[0.95, 0.05])[0]
            is_emergency = 0
            is_legitimate = True

        elif scenario == "EMERGENCY_ACCESS":
            # Legitimate urgent emergency/trauma care
            role = random.choices([ROLE_MAP["DOCTOR"], ROLE_MAP["NURSE"]], weights=[0.75, 0.25])[0]
            # In emergencies, doctors frequently cross departmental boundaries (e.g., ER consults cardiology)
            dept_match = random.choices([1, 0], weights=[0.45, 0.55])[0]
            sensitivity = random.choices([SENSITIVITY_MAP["HIGH"], SENSITIVITY_MAP["CRITICAL_VIP"], SENSITIVITY_MAP["MEDIUM"]], weights=[0.55, 0.30, 0.15])[0]
            # Emergencies occur anytime (24/7)
            request_time = random.choices([TIME_MAP["NORMAL_HOURS"], TIME_MAP["OFF_HOURS"]], weights=[0.50, 0.50])[0]
            location = random.choices([LOCATION_MAP["INTERNAL_HOSPITAL"], LOCATION_MAP["VPN_OFFSITE"]], weights=[0.95, 0.05])[0]
            # Clinicians rapidly pulling vitals/labs
            frequency = random.choices([FREQUENCY_MAP["ELEVATED"], FREQUENCY_MAP["NORMAL"]], weights=[0.65, 0.35])[0]
            is_emergency = 1
            is_legitimate = True

        elif scenario == "STOLEN_CREDENTIAL":
            # Compromised user credentials operated externally or at unusual hours
            role = random.choices([ROLE_MAP["DOCTOR"], ROLE_MAP["NURSE"], ROLE_MAP["STAFF"]], weights=[0.50, 0.30, 0.20])[0]
            dept_match = random.choices([0, 1], weights=[0.80, 0.20])[0]
            # Adversary targets high value/sensitive records
            sensitivity = random.choices([SENSITIVITY_MAP["HIGH"], SENSITIVITY_MAP["CRITICAL_VIP"]], weights=[0.55, 0.45])[0]
            request_time = random.choices([TIME_MAP["OFF_HOURS"], TIME_MAP["NORMAL_HOURS"]], weights=[0.80, 0.20])[0]
            location = random.choices([LOCATION_MAP["EXTERNAL_UNKNOWN"], LOCATION_MAP["VPN_OFFSITE"]], weights=[0.85, 0.15])[0]
            frequency = random.choices([FREQUENCY_MAP["ELEVATED"], FREQUENCY_MAP["NORMAL"], FREQUENCY_MAP["BURST_HIGH"]], weights=[0.50, 0.30, 0.20])[0]
            # Adversary might try spoofing emergency flag to bypass firewalls
            is_emergency = random.choices([0, 1], weights=[0.90, 0.10])[0]
            is_legitimate = False

        elif scenario == "INSIDER_MISUSE":
            # Internal employee snooping outside professional purview (e.g. VIP patient, psychiatric notes)
            role = random.choices([ROLE_MAP["NURSE"], ROLE_MAP["STAFF"], ROLE_MAP["RESEARCHER"], ROLE_MAP["DOCTOR"]], weights=[0.35, 0.35, 0.20, 0.10])[0]
            dept_match = 0  # Snooping outside assigned department
            sensitivity = random.choices([SENSITIVITY_MAP["CRITICAL_VIP"], SENSITIVITY_MAP["HIGH"]], weights=[0.75, 0.25])[0]
            request_time = random.choices([TIME_MAP["NORMAL_HOURS"], TIME_MAP["OFF_HOURS"]], weights=[0.60, 0.40])[0]
            location = random.choices([LOCATION_MAP["INTERNAL_HOSPITAL"], LOCATION_MAP["VPN_OFFSITE"]], weights=[0.90, 0.10])[0]
            frequency = random.choices([FREQUENCY_MAP["NORMAL"], FREQUENCY_MAP["ELEVATED"]], weights=[0.80, 0.20])[0]
            is_emergency = 0
            is_legitimate = False

        elif scenario == "MASS_ACCESS":
            # Automated bot scraping or bulk exfiltration attempt
            role = random.choices([ROLE_MAP["STAFF"], ROLE_MAP["RESEARCHER"], ROLE_MAP["DOCTOR"]], weights=[0.40, 0.40, 0.20])[0]
            dept_match = 0
            sensitivity = random.choices([SENSITIVITY_MAP["LOW"], SENSITIVITY_MAP["MEDIUM"], SENSITIVITY_MAP["HIGH"]], weights=[0.30, 0.40, 0.30])[0]
            request_time = random.choices([TIME_MAP["OFF_HOURS"], TIME_MAP["NORMAL_HOURS"]], weights=[0.75, 0.25])[0]
            location = random.choices([LOCATION_MAP["EXTERNAL_UNKNOWN"], LOCATION_MAP["VPN_OFFSITE"]], weights=[0.70, 0.30])[0]
            frequency = FREQUENCY_MAP["BURST_HIGH"]  # High velocity queries
            is_emergency = random.choices([0, 1], weights=[0.95, 0.05])[0]
            is_legitimate = False

        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        obs = Observation(
            role=role,
            dept_match=dept_match,
            sensitivity=sensitivity,
            request_time=request_time,
            location=location,
            frequency=frequency,
            is_emergency=is_emergency
        )

        hidden_meta = {
            "scenario": scenario,
            "is_legitimate": is_legitimate,
            "timestamp": time.time(),
            "patient_id": f"PAT-{random.randint(1000, 9999)}",
            "user_id": f"USR-{random.randint(100, 999)}",
            "record_id": f"REC-{random.randint(10000, 99999)}"
        }

        return obs, hidden_meta

    def reset(self) -> Observation:
        """
        Resets environment and samples a new access request.
        """
        self.step_count = 0
        self.current_state, self.current_meta = self.generate_request()
        return self.current_state

    def step(self, action: int) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Executes an action in the environment.
        Actions:
          0: ALLOW
          1: DENY
          2: CHALLENGE
          3: RESTRICT

        Returns:
          next_state (Observation), reward (float), done (bool), info (dict)
        """
        if self.current_state is None:
            self.reset()

        reward, outcome_info = self.calculate_reward(self.current_state, action, self.current_meta)
        self.step_count += 1

        # In contextual access-control, each request is evaluated on arrival.
        # We model each step as a decision episode, or next_state as the next incoming request.
        done = True
        next_state, next_meta = self.generate_request()

        info = {
            **self.current_meta,
            **outcome_info,
            "action_taken": ACTIONS[action],
            "reward": reward
        }

        self.current_state = next_state
        self.current_meta = next_meta
        return next_state, reward, done, info

    def calculate_reward(self, obs: Observation, action: int, meta: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Principled hospital access-control reward function.
        Balances:
          - Confidentiality & Security (blocking stolen credentials, scrapers, snoops)
          - Patient Safety & Clinical Availability (ensuring doctors get emergency records immediately)
          - Minimal Clinical Friction (rewarding ALLOW for legitimate routine queries)
        """
        is_legitimate = meta["is_legitimate"]
        scenario = meta["scenario"]
        is_emergency = bool(obs.is_emergency)

        outcome_info = {
            "security_breach": False,
            "false_denial": False,
            "attack_blocked": False,
            "legitimate_granted": False,
            "step_up_prompted": False,
            "restricted_granted": False
        }

        # -------------------------------------------------------------
        # SCENARIO 1: EMERGENCY ACCESS (Legitimate, High Urgency)
        # -------------------------------------------------------------
        if scenario == "EMERGENCY_ACCESS":
            if action == ACTION_ALLOW:
                # Immediate life-saving data access delivered
                reward = 20.0
                outcome_info["legitimate_granted"] = True
            elif action == ACTION_RESTRICT:
                # Masked vital signs in emergency may slow emergency care
                reward = -5.0
                outcome_info["restricted_granted"] = True
            elif action == ACTION_CHALLENGE:
                # 2FA delay in emergency can be life-threatening
                reward = -10.0
                outcome_info["step_up_prompted"] = True
            elif action == ACTION_DENY:
                # Severe penalty: Blocking doctors during emergency risks patient life!
                reward = -35.0
                outcome_info["false_denial"] = True

        # -------------------------------------------------------------
        # SCENARIO 2: NORMAL CLINICAL ACCESS (Legitimate Routine)
        # -------------------------------------------------------------
        elif scenario == "NORMAL_ACCESS":
            if action == ACTION_ALLOW:
                # Frictionless patient care
                reward = 12.0
                outcome_info["legitimate_granted"] = True
            elif action == ACTION_CHALLENGE:
                # Legitimate staff can complete 2FA, slight workflow friction
                reward = 1.0
                outcome_info["step_up_prompted"] = True
            elif action == ACTION_RESTRICT:
                if obs.dept_match == 1 and obs.role in (ROLE_MAP["DOCTOR"], ROLE_MAP["NURSE"]):
                    # Unnecessary restriction on primary caregiver
                    reward = -3.0
                else:
                    # Legitimate cross-dept or staff masked view
                    reward = 3.0
                outcome_info["restricted_granted"] = True
            elif action == ACTION_DENY:
                # Disrupts legitimate clinician workflow
                reward = -18.0
                outcome_info["false_denial"] = True

        # -------------------------------------------------------------
        # SCENARIO 3: STOLEN CREDENTIAL ATTACK (Malicious External Actor)
        # -------------------------------------------------------------
        elif scenario == "STOLEN_CREDENTIAL":
            if action == ACTION_DENY:
                # Threat completely stopped
                reward = 18.0
                outcome_info["attack_blocked"] = True
            elif action == ACTION_CHALLENGE:
                # Step-up 2FA/biometric: external adversary cannot pass device MFA
                reward = 14.0
                outcome_info["attack_blocked"] = True
                outcome_info["step_up_prompted"] = True
            elif action == ACTION_RESTRICT:
                # Adversary still extracts partial sensitive medical info
                reward = -8.0
                outcome_info["security_breach"] = True
                outcome_info["restricted_granted"] = True
            elif action == ACTION_ALLOW:
                # Direct data breach!
                reward = -30.0
                outcome_info["security_breach"] = True

        # -------------------------------------------------------------
        # SCENARIO 4: INSIDER-LIKE MISUSE (Snooping on VIPs / Off-Department)
        # -------------------------------------------------------------
        elif scenario == "INSIDER_MISUSE":
            if action == ACTION_DENY:
                # Unauthorized snooping blocked
                reward = 15.0
                outcome_info["attack_blocked"] = True
            elif action == ACTION_RESTRICT:
                # Good middle-ground: masked view hides PII/VIP chart while preventing lockouts
                reward = 8.0
                outcome_info["restricted_granted"] = True
            elif action == ACTION_CHALLENGE:
                # Requires supervisor override or biometric reason, deterring snooping
                reward = 6.0
                outcome_info["step_up_prompted"] = True
            elif action == ACTION_ALLOW:
                # Confidentiality breach under HIPAA / hospital policy
                reward = -22.0
                outcome_info["security_breach"] = True

        # -------------------------------------------------------------
        # SCENARIO 5: MASS ACCESS ATTEMPT (Scraping / Bulk Exfiltration)
        # -------------------------------------------------------------
        elif scenario == "MASS_ACCESS":
            if action == ACTION_DENY:
                # Bulk scraping blocked instantly
                reward = 20.0
                outcome_info["attack_blocked"] = True
            elif action == ACTION_CHALLENGE:
                # Step-up challenge breaks automated script
                reward = 8.0
                outcome_info["attack_blocked"] = True
                outcome_info["step_up_prompted"] = True
            elif action == ACTION_RESTRICT:
                # Bulk partial data is still a major data leak
                reward = -10.0
                outcome_info["security_breach"] = True
                outcome_info["restricted_granted"] = True
            elif action == ACTION_ALLOW:
                # Catastrophic mass patient record leak
                reward = -35.0
                outcome_info["security_breach"] = True

        else:
            reward = 0.0

        return reward, outcome_info


def parse_context_to_observation(context: Dict[str, Any]) -> Observation:
    """
    Utility function to convert external JSON/dictionary request into discrete Observation.
    Supports string or integer inputs and provides safe fallbacks.
    """
    # Role
    raw_role = str(context.get("role", "DOCTOR")).upper()
    role = ROLE_MAP.get(raw_role, ROLE_MAP["DOCTOR"])

    # Dept Match
    raw_dept_match = context.get("department_match")
    if raw_dept_match is None:
        user_dept = str(context.get("user_department", "")).strip().lower()
        patient_dept = str(context.get("patient_department", "")).strip().lower()
        dept_match = 1 if (user_dept and user_dept == patient_dept) else 0
    else:
        dept_match = 1 if (bool(raw_dept_match) or raw_dept_match in (1, "1", "true", "True", True)) else 0

    # Sensitivity
    raw_sens = str(context.get("record_sensitivity", context.get("sensitivity", "MEDIUM"))).upper()
    sensitivity = SENSITIVITY_MAP.get(raw_sens, SENSITIVITY_MAP["MEDIUM"])

    # Request Time
    raw_time = str(context.get("request_time", context.get("time_of_day", "NORMAL_HOURS"))).upper()
    if "OFF" in raw_time or "NIGHT" in raw_time:
        request_time = TIME_MAP["OFF_HOURS"]
    else:
        request_time = TIME_MAP["NORMAL_HOURS"]

    # Location
    raw_loc = str(context.get("location", "INTERNAL_HOSPITAL")).upper()
    location = LOCATION_MAP.get(raw_loc, LOCATION_MAP["INTERNAL_HOSPITAL"])

    # Frequency
    raw_freq = context.get("request_frequency", context.get("frequency", "NORMAL"))
    if isinstance(raw_freq, (int, float)):
        if raw_freq <= 5:
            frequency = FREQUENCY_MAP["NORMAL"]
        elif raw_freq <= 20:
            frequency = FREQUENCY_MAP["ELEVATED"]
        else:
            frequency = FREQUENCY_MAP["BURST_HIGH"]
    else:
        frequency = FREQUENCY_MAP.get(str(raw_freq).upper(), FREQUENCY_MAP["NORMAL"])

    # Emergency
    raw_em = context.get("emergency_status", context.get("is_emergency", 0))
    is_emergency = 1 if (bool(raw_em) or raw_em in (1, "1", "true", "True", True)) else 0

    return Observation(
        role=role,
        dept_match=dept_match,
        sensitivity=sensitivity,
        request_time=request_time,
        location=location,
        frequency=frequency,
        is_emergency=is_emergency
    )
