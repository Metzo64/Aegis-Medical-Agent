"""
Tabular Q-Learning Agent for Hospital Access Control.
Maintains a 2D Q-Table of shape [TOTAL_STATES, NUM_ACTIONS].

Features:
- Observes contextual features without seeing hidden attack/legit label.
- Epsilon-greedy exploration with decay during training.
- Deterministic argmax policy with tie-breaking during inference.
- Model serialization (save/load) to JSON format.
- Real-time decision explanations for college viva and interactive auditing.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np

from config import (
    ACTIONS, ACTION_ALLOW, ACTION_DENY, ACTION_CHALLENGE, ACTION_RESTRICT,
    ACTION_NAMES, ACTION_DESCRIPTIONS, MODEL_PATH, METADATA_PATH,
    ROLES, SENSITIVITIES, LOCATIONS, FREQUENCIES, REQUEST_TIMES
)
from env import TOTAL_STATES, NUM_ROLES, NUM_DEPT_MATCH, NUM_SENSITIVITIES, NUM_TIMES, NUM_LOCATIONS, NUM_FREQUENCIES, NUM_EMERGENCY, Observation, AccessRequestEnvironment

logger = logging.getLogger("HospitalRL.agent")


class TabularQLearningAgent:
    """
    Tabular Q-Learning Agent for secure, adaptive access control.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.90,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.9997,
        num_states: int = TOTAL_STATES,
        num_actions: int = len(ACTIONS)
    ):
        self.learning_rate = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.num_states = num_states
        self.num_actions = num_actions

        # Initialize Q-table with zeros: shape [1152, 4]
        self.q_table = np.zeros((self.num_states, self.num_actions), dtype=np.float64)
        self.total_episodes_trained = 0
        self.training_history: List[Dict[str, Any]] = []

    def choose_action(self, state_idx: int, training: bool = True) -> int:
        """
        Chooses an action using epsilon-greedy policy during training,
        or greedy argmax during evaluation/inference.
        """
        if training and np.random.rand() < self.epsilon:
            return int(np.random.randint(self.num_actions))

        # Argmax with random tie-breaking
        q_row = self.q_table[state_idx]
        max_q = np.max(q_row)
        best_actions = np.where(np.isclose(q_row, max_q))[0]
        return int(np.random.choice(best_actions))

    def update(
        self,
        state_idx: int,
        action: int,
        reward: float,
        next_state_idx: int,
        done: bool
    ) -> float:
        """
        Standard Tabular Q-Learning update rule:
        Q(s, a) <- Q(s, a) + alpha * [reward + gamma * max_a' Q(s', a') - Q(s, a)]
        """
        current_q = self.q_table[state_idx, action]

        if done:
            target = reward
        else:
            best_next_q = np.max(self.q_table[next_state_idx])
            target = reward + self.gamma * best_next_q

        td_error = target - current_q
        self.q_table[state_idx, action] += self.learning_rate * td_error
        return float(td_error)

    def decay_epsilon(self) -> float:
        """
        Decays exploration rate epsilon towards epsilon_min.
        """
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return self.epsilon

    def get_q_values(self, state_idx: int) -> Dict[str, float]:
        """
        Returns Q-values for all 4 actions formatted as a dictionary.
        """
        row = self.q_table[state_idx]
        return {ACTION_NAMES[i]: round(float(row[i]), 4) for i in range(self.num_actions)}

    def explain_decision(self, obs: Observation, action: int, q_vals: Dict[str, float]) -> str:
        """
        Generates human-readable reasoning for why an action was chosen.
        Essential for healthcare audits and viva demonstration.
        """
        role_name = ROLES[obs.role]
        action_name = ACTION_NAMES[action]
        sens_name = SENSITIVITIES[obs.sensitivity]
        loc_name = LOCATIONS[obs.location]
        freq_name = FREQUENCIES[obs.frequency]
        dept_status = "Department MATCH" if obs.dept_match == 1 else "Department MISMATCH"
        emergency_str = "ACTIVE EMERGENCY" if obs.is_emergency == 1 else "Non-Emergency"

        reasons = []

        if obs.is_emergency == 1:
            if action == ACTION_ALLOW:
                reasons.append("Emergency override active: immediate patient vital data access granted to prevent clinical harm.")
            else:
                reasons.append("Emergency override active, but security restrictions took precedence.")

        if obs.location == 2:  # EXTERNAL_UNKNOWN
            reasons.append("Request originated from an untrusted external network.")
            if action in (ACTION_DENY, ACTION_CHALLENGE):
                reasons.append("Zero-trust policy requires blocking or step-up authentication for external connections.")

        if obs.frequency == 2:  # BURST_HIGH
            reasons.append(f"Abnormal burst query velocity detected ({freq_name}), characteristic of scraping or automated extraction.")

        if obs.dept_match == 0:
            reasons.append(f"{role_name} requested record outside assigned unit ({dept_status}).")

        if obs.sensitivity >= 2:  # HIGH or CRITICAL_VIP
            reasons.append(f"Target record has heightened sensitivity level: {sens_name}.")

        if not reasons:
            reasons.append(f"Standard routine access for {role_name} with {dept_status} during {REQUEST_TIMES[obs.request_time]}.")

        explanation = f"Selected '{action_name}' (Q-Score: {q_vals.get(action_name, 0.0):.2f}). Context: {'; '.join(reasons)}"
        return explanation

    def save(self, filepath: Optional[Path] = None, metadata_path: Optional[Path] = None) -> None:
        """
        Saves Q-table and agent hyperparameters to disk.
        """
        target_path = Path(filepath) if filepath else MODEL_PATH
        target_meta = Path(metadata_path) if metadata_path else METADATA_PATH

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert numpy array to serializable nested list
        model_payload = {
            "num_states": self.num_states,
            "num_actions": self.num_actions,
            "actions": ACTIONS,
            "q_table": self.q_table.tolist()
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(model_payload, f, indent=2)

        meta_payload = {
            "total_episodes_trained": self.total_episodes_trained,
            "learning_rate": self.learning_rate,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "non_zero_q_entries": int(np.count_nonzero(self.q_table))
        }

        with open(target_meta, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        logger.info(f"Agent successfully saved to {target_path}")

    def load(self, filepath: Optional[Path] = None) -> bool:
        """
        Loads Q-table from disk. Returns True if successful, False otherwise.
        """
        target_path = Path(filepath) if filepath else MODEL_PATH
        if not target_path.exists():
            logger.warning(f"No trained model found at {target_path}. Using uninitialized agent.")
            return False

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            loaded_q = np.array(data["q_table"], dtype=np.float64)
            if loaded_q.shape == (self.num_states, self.num_actions):
                self.q_table = loaded_q
                logger.info(f"Loaded trained Q-table from {target_path} (shape: {self.q_table.shape})")
                return True
            else:
                logger.error(f"Shape mismatch: expected ({self.num_states}, {self.num_actions}), found {loaded_q.shape}")
                return False
        except Exception as e:
            logger.error(f"Failed to load Q-table from {target_path}: {e}")
            return False
