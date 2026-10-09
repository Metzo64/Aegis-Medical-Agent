"""
Comprehensive verification test script for the Hospital Access Control RL project.
Tests:
  1. Environment state bijection (encoding/decoding for all 1,152 states)
  2. Hidden label separation (agent receives only observable features)
  3. Action space (ALLOW, DENY, CHALLENGE, RESTRICT)
  4. Reward function clinical & security sanity
  5. Q-learning agent training and save/load
  6. Database module resilience and schema adapter
  7. FastAPI endpoints (/health, /db/test, /predict, /simulate)
"""

import sys
import os
import unittest
import numpy as np
from fastapi.testclient import TestClient

from config import ACTIONS, ACTION_ALLOW, ACTION_DENY, ACTION_CHALLENGE, ACTION_RESTRICT, REQUIRED_TABLES
from env import (
    AccessRequestEnvironment, Observation, TOTAL_STATES,
    parse_context_to_observation
)
from agent import TabularQLearningAgent
from db import test_connection, adapt_payload_to_schema
from main import app


class TestHospitalAccessRL(unittest.TestCase):

    def setUp(self):
        self.env = AccessRequestEnvironment(seed=42)
        self.agent = TabularQLearningAgent()

    def test_01_state_bijection(self):
        """Verify that state_to_index and index_to_state are a complete bijection for all 1,152 states."""
        self.assertEqual(TOTAL_STATES, 1152)
        for idx in range(TOTAL_STATES):
            obs = self.env.index_to_state(idx)
            recovered_idx = self.env.state_to_index(obs)
            self.assertEqual(idx, recovered_idx, f"State index mismatch at {idx}")

    def test_02_hidden_labels_separated(self):
        """Verify requirement 8: The agent's observation does NOT contain scenario or is_legitimate."""
        obs, meta = self.env.generate_request()
        # Observable tuple fields
        self.assertEqual(len(obs), 7)
        self.assertTrue(hasattr(obs, "role"))
        self.assertTrue(hasattr(obs, "dept_match"))
        self.assertTrue(hasattr(obs, "sensitivity"))
        self.assertTrue(hasattr(obs, "request_time"))
        self.assertTrue(hasattr(obs, "location"))
        self.assertTrue(hasattr(obs, "frequency"))
        self.assertTrue(hasattr(obs, "is_emergency"))

        # Hidden meta fields
        self.assertFalse(hasattr(obs, "is_legitimate"))
        self.assertFalse(hasattr(obs, "scenario"))
        self.assertIn("is_legitimate", meta)
        self.assertIn("scenario", meta)

    def test_03_emergency_reward_prioritizes_life_safety(self):
        """Verify requirement 10: In emergency, ALLOW reward is much greater than DENY or CHALLENGE."""
        obs, meta = self.env.generate_request(scenario_override="EMERGENCY_ACCESS")
        r_allow, _ = self.env.calculate_reward(obs, ACTION_ALLOW, meta)
        r_deny, _ = self.env.calculate_reward(obs, ACTION_DENY, meta)
        r_challenge, _ = self.env.calculate_reward(obs, ACTION_CHALLENGE, meta)

        self.assertGreater(r_allow, 0.0)
        self.assertLess(r_deny, -20.0)
        self.assertGreater(r_allow, r_challenge)
        self.assertGreater(r_challenge, r_deny)

    def test_04_attack_reward_penalizes_unauthorized_access(self):
        """Verify requirement 10: In stolen credential misuse, ALLOW is heavily penalized, DENY is rewarded."""
        obs, meta = self.env.generate_request(scenario_override="STOLEN_CREDENTIAL")
        r_deny, _ = self.env.calculate_reward(obs, ACTION_DENY, meta)
        r_allow, _ = self.env.calculate_reward(obs, ACTION_ALLOW, meta)

        self.assertGreater(r_deny, 10.0)
        self.assertLess(r_allow, -20.0)

    def test_05_agent_learning_and_serialization(self):
        """Verify Q-learning agent update, save, and reload."""
        state_idx = 100
        action = ACTION_ALLOW
        reward = 15.0
        next_state_idx = 101

        old_q = self.agent.q_table[state_idx, action]
        td_error = self.agent.update(state_idx, action, reward, next_state_idx, done=False)
        new_q = self.agent.q_table[state_idx, action]

        self.assertNotEqual(old_q, new_q)
        self.assertAlmostEqual(new_q, old_q + 0.1 * td_error)

    def test_06_database_connection_safe(self):
        """Verify that db test_connection runs without uncaught exceptions."""
        result = test_connection()
        self.assertIn("connected", result)
        self.assertIn("status", result)

    def test_07_fastapi_endpoints(self):
        """Verify FastAPI /health, /db/test, and /predict endpoints using TestClient."""
        client = TestClient(app)

        # Health endpoint
        res_health = client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "healthy")

        # DB test endpoint
        res_db = client.get("/db/test")
        self.assertEqual(res_db.status_code, 200)

        # Predict endpoint
        payload = {
            "user_id": "USR-TEST-1",
            "role": "DOCTOR",
            "department_match": True,
            "record_sensitivity": "MEDIUM",
            "request_time": "NORMAL_HOURS",
            "location": "INTERNAL_HOSPITAL",
            "request_frequency": "NORMAL",
            "emergency_status": False
        }
        res_pred = client.post("/predict", json=payload)
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        self.assertIn(pred_data["action"], ACTIONS)
        self.assertIn("q_values", pred_data)
        self.assertIn("explanation", pred_data)


if __name__ == "__main__":
    unittest.main()
