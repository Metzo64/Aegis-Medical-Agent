"""
Evaluation script for Hospital Access Control Tabular Q-Learning Agent.
Rigorously evaluates the agent against all five simulated access scenarios and reports:
  1. Attack blocking rate (%)
  2. Unauthorized access rate (%)
  3. Legitimate access rate (%)
  4. False denial rate (%)
  5. Average decision time (milliseconds)
  6. Cumulative reward

Usage:
    python evaluate.py --samples 5000
"""

import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MODEL_PATH, MODEL_DIR, ACTIONS, ACTION_NAMES
from env import AccessRequestEnvironment, Observation
from agent import TabularQLearningAgent


def evaluate_agent(
    model_path: Path = MODEL_PATH,
    num_samples: int = 5000,
    seed: int = 100
) -> Dict[str, Any]:
    """
    Evaluates the trained Tabular Q-Learning agent on fresh simulated requests.
    """
    print("=" * 75)
    print("   EVALUATION REPORT: HOSPITAL ACCESS CONTROL REINFORCEMENT LEARNING")
    print("=" * 75)

    agent = TabularQLearningAgent()
    if not agent.load(model_path):
        print(f"[-] Error: Could not load trained model from {model_path}.")
        print("    Please run `python train.py` first to generate the Q-table.")
        sys.exit(1)

    env = AccessRequestEnvironment(seed=seed)

    # Performance Counters
    total_eval_samples = num_samples
    decision_times_ms: List[float] = []
    cumulative_reward = 0.0

    # Scenario counts & Action breakdowns
    scenario_counts: Dict[str, int] = {
        "NORMAL_ACCESS": 0,
        "EMERGENCY_ACCESS": 0,
        "STOLEN_CREDENTIAL": 0,
        "INSIDER_MISUSE": 0,
        "MASS_ACCESS": 0
    }

    action_matrix: Dict[str, Dict[str, int]] = {
        scen: {act: 0 for act in ACTIONS} for scen in scenario_counts
    }

    total_attacks = 0
    attacks_blocked = 0
    unauthorized_allowed = 0

    total_legitimate = 0
    legitimate_granted = 0
    false_denials = 0
    emergency_denials = 0
    total_emergencies = 0

    for _ in range(num_samples):
        obs, meta = env.generate_request()
        state_idx = env.state_to_index(obs)
        scenario = meta["scenario"]
        is_legitimate = meta["is_legitimate"]
        is_emergency = bool(obs.is_emergency)

        scenario_counts[scenario] += 1

        # Measure pure decision inference latency
        t0 = time.perf_counter()
        action_idx = agent.choose_action(state_idx, training=False)
        t1 = time.perf_counter()
        decision_time_ms = (t1 - t0) * 1000.0
        decision_times_ms.append(decision_time_ms)

        action_name = ACTION_NAMES[action_idx]
        action_matrix[scenario][action_name] += 1

        # Calculate reward using environment reward function
        reward, info = env.calculate_reward(obs, action_idx, meta)
        cumulative_reward += reward

        # Categorize Security & Clinical Metrics
        if not is_legitimate:
            total_attacks += 1
            if action_name in ("DENY", "CHALLENGE"):
                attacks_blocked += 1
            elif action_name == "ALLOW":
                unauthorized_allowed += 1
            elif action_name == "RESTRICT":
                # For insider misuse, restricted view is an acceptable containment policy;
                # For external stolen credentials/mass, partial leakage is unauthorized
                if scenario == "INSIDER_MISUSE":
                    attacks_blocked += 1
                else:
                    unauthorized_allowed += 1
        else:
            total_legitimate += 1
            if action_name in ("ALLOW", "CHALLENGE", "RESTRICT"):
                legitimate_granted += 1
            elif action_name == "DENY":
                false_denials += 1

            if is_emergency:
                total_emergencies += 1
                if action_name == "DENY":
                    emergency_denials += 1

    # Metric Computations
    attack_blocking_rate = (attacks_blocked / total_attacks * 100.0) if total_attacks > 0 else 0.0
    unauthorized_access_rate = (unauthorized_allowed / total_attacks * 100.0) if total_attacks > 0 else 0.0
    legitimate_access_rate = (legitimate_granted / total_legitimate * 100.0) if total_legitimate > 0 else 0.0
    false_denial_rate = (false_denials / total_legitimate * 100.0) if total_legitimate > 0 else 0.0
    avg_decision_time_ms = float(np.mean(decision_times_ms))
    p95_decision_time_ms = float(np.percentile(decision_times_ms, 95))
    emergency_false_denial_rate = (emergency_denials / total_emergencies * 100.0) if total_emergencies > 0 else 0.0

    # Console Output (Required by Project Specification)
    print(f"\n[+] Total Evaluated Requests    : {num_samples:,}")
    print(f"    - Legitimate Requests       : {total_legitimate:,} ({(total_legitimate/num_samples)*100:.1f}%)")
    print(f"    - Simulated Attack Requests : {total_attacks:,} ({(total_attacks/num_samples)*100:.1f}%)")
    print("-" * 75)
    print("KEY PERFORMANCE INDICATORS (PROJECT REQUIREMENTS):")
    print("-" * 75)
    print(f"  1. Attack Blocking Rate      : {attack_blocking_rate:>6.2f}%  (Target: > 90%)")
    print(f"  2. Unauthorized Access Rate  : {unauthorized_access_rate:>6.2f}%  (Target: < 5%)")
    print(f"  3. Legitimate Access Rate    : {legitimate_access_rate:>6.2f}%  (Target: > 95%)")
    print(f"  4. False Denial Rate         : {false_denial_rate:>6.2f}%  (Target: < 5%)")
    print(f"  5. Average Decision Time     : {avg_decision_time_ms:>6.4f} ms (p95: {p95_decision_time_ms:.4f} ms)")
    print(f"  6. Cumulative Reward         : {cumulative_reward:>+10.1f}")
    print("-" * 75)
    print(f"  * Emergency Denial Rate      : {emergency_false_denial_rate:>6.2f}%  (Vital Life-Safety Check)")
    print("-" * 75)

    print("\nDECISION BREAKDOWN BY SIMULATION SCENARIO:")
    print(f"{'SCENARIO':<20} | {'TOTAL':<7} | {'ALLOW':<8} | {'DENY':<8} | {'CHALLENGE':<10} | {'RESTRICT':<8}")
    print("-" * 75)
    for scen, counts in action_matrix.items():
        tot = scenario_counts[scen]
        print(
            f"{scen:<20} | {tot:<7} | "
            f"{counts['ALLOW']:<8} | "
            f"{counts['DENY']:<8} | "
            f"{counts['CHALLENGE']:<10} | "
            f"{counts['RESTRICT']:<8}"
        )
    print("=" * 75)

    results = {
        "num_samples": num_samples,
        "total_legitimate": total_legitimate,
        "total_attacks": total_attacks,
        "metrics": {
            "attack_blocking_rate_pct": round(attack_blocking_rate, 2),
            "unauthorized_access_rate_pct": round(unauthorized_access_rate, 2),
            "legitimate_access_rate_pct": round(legitimate_access_rate, 2),
            "false_denial_rate_pct": round(false_denial_rate, 2),
            "emergency_denial_rate_pct": round(emergency_false_denial_rate, 2),
            "average_decision_time_ms": round(avg_decision_time_ms, 5),
            "p95_decision_time_ms": round(p95_decision_time_ms, 5),
            "cumulative_reward": round(cumulative_reward, 2)
        },
        "scenario_counts": scenario_counts,
        "action_breakdown": action_matrix
    }

    # Save to disk
    eval_output_file = MODEL_DIR / "evaluation_results.json"
    with open(eval_output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Detailed evaluation metrics saved to: {eval_output_file}")

    # Generate interactive Plotly evaluation bar chart
    generate_plotly_eval_chart(action_matrix, MODEL_DIR / "evaluation_chart.html")

    return results


def generate_plotly_eval_chart(action_matrix: dict, output_path: Path) -> None:
    """
    Renders an interactive stacked bar chart showing policy actions across scenarios.
    """
    scenarios = list(action_matrix.keys())
    actions = ["ALLOW", "DENY", "CHALLENGE", "RESTRICT"]
    colors = {
        "ALLOW": "#10b981",      # Emerald Green
        "DENY": "#ef4444",       # Crimson Red
        "CHALLENGE": "#f59e0b",  # Amber Yellow
        "RESTRICT": "#6366f1"    # Indigo Purple
    }

    fig = go.Figure()
    for act in actions:
        fig.add_trace(go.Bar(
            name=act,
            x=scenarios,
            y=[action_matrix[scen][act] for scen in scenarios],
            marker_color=colors[act]
        ))

    fig.update_layout(
        barmode="stack",
        title="Adaptive Policy Action Distribution per Hospital Access Scenario",
        xaxis_title="Access Scenario",
        yaxis_title="Request Count",
        template="plotly_dark",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.write_html(str(output_path), include_plotlyjs="cdn")
    print(f"[+] Evaluation Plotly chart saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Hospital Access Control Agent")
    parser.add_argument("--samples", type=int, default=5000, help="Number of evaluation requests (default: 5000)")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to trained Q-table json")
    args = parser.parse_args()

    evaluate_agent(model_path=Path(args.model), num_samples=args.samples)
