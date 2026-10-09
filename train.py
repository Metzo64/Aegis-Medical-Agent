"""
Training script for Hospital Access Control Tabular Q-Learning Agent.
Trains the agent over simulated episodes, tracks convergence, generates Plotly charts,
and saves the trained model to disk.

Usage:
    python train.py --episodes 35000
"""

import sys
import time
import argparse
import json
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MODEL_PATH, METADATA_PATH, TRAINING_METRICS_PATH, MODEL_DIR
from env import AccessRequestEnvironment
from agent import TabularQLearningAgent


def train_agent(
    episodes: int = 35000,
    learning_rate: float = 0.1,
    discount_factor: float = 0.90,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.01,
    epsilon_decay: float = 0.9998,
    log_interval: int = 1000
) -> TabularQLearningAgent:
    """
    Executes training loop and tracks performance metrics.
    """
    print("=" * 70)
    print("   TRAINING TABULAR Q-LEARNING AGENT FOR HOSPITAL ACCESS CONTROL")
    print("=" * 70)
    print(f"Target Episodes    : {episodes:,}")
    print(f"Learning Rate (alpha): {learning_rate}")
    print(f"Discount Factor (gamma): {discount_factor}")
    print(f"Exploration (epsilon): {epsilon_start} -> {epsilon_min} (decay: {epsilon_decay})")
    print(f"Total States       : 1,152")
    print(f"Action Space       : ALLOW, DENY, CHALLENGE, RESTRICT (4 actions)")
    print("-" * 70)

    env = AccessRequestEnvironment(seed=42)
    agent = TabularQLearningAgent(
        learning_rate=learning_rate,
        discount_factor=discount_factor,
        epsilon_start=epsilon_start,
        epsilon_min=epsilon_min,
        epsilon_decay=epsilon_decay
    )

    episode_rewards = []
    moving_avg_rewards = []
    checkpoint_episodes = []
    avg_rewards_log = []
    epsilon_log = []
    td_errors_log = []

    start_time = time.time()
    recent_rewards = []
    recent_td_errors = []

    for episode in range(1, episodes + 1):
        obs = env.reset()
        state_idx = env.state_to_index(obs)

        # Agent chooses action via epsilon-greedy
        action = agent.choose_action(state_idx, training=True)

        # Environment steps
        next_obs, reward, done, info = env.step(action)
        next_state_idx = env.state_to_index(next_obs)

        # Update Q-table
        td_error = agent.update(state_idx, action, reward, next_state_idx, done)
        agent.decay_epsilon()

        recent_rewards.append(reward)
        recent_td_errors.append(abs(td_error))

        # Periodic logging and evaluation snapshots
        if episode % log_interval == 0:
            mean_r = float(np.mean(recent_rewards))
            mean_td = float(np.mean(recent_td_errors))
            checkpoint_episodes.append(episode)
            avg_rewards_log.append(round(mean_r, 3))
            epsilon_log.append(round(agent.epsilon, 4))
            td_errors_log.append(round(mean_td, 4))

            elapsed = time.time() - start_time
            rate = episode / elapsed if elapsed > 0 else 0
            print(
                f"Episode {episode:>6d}/{episodes} | "
                f"Avg Reward: {mean_r:>+6.2f} | "
                f"Epsilon: {agent.epsilon:.4f} | "
                f"TD Error: {mean_td:.4f} | "
                f"Speed: {rate:4.0f} ep/s"
            )
            recent_rewards = []
            recent_td_errors = []

    total_training_time = time.time() - start_time
    agent.total_episodes_trained = episodes

    print("-" * 70)
    print(f"[+] Training completed in {total_training_time:.2f} seconds ({episodes / total_training_time:.0f} ep/sec).")

    # Save model and metadata
    agent.save(MODEL_PATH, METADATA_PATH)

    # Save training metric logs
    metrics_data = {
        "episodes": checkpoint_episodes,
        "average_rewards": avg_rewards_log,
        "epsilon_history": epsilon_log,
        "td_error_history": td_errors_log,
        "total_training_time_seconds": round(total_training_time, 2)
    }
    with open(TRAINING_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    # Generate Plotly Training Convergence Visualization
    generate_plotly_training_chart(metrics_data, MODEL_DIR / "training_curves.html")

    return agent


def generate_plotly_training_chart(metrics: dict, output_path: Path) -> None:
    """
    Renders an interactive 2-panel Plotly figure displaying:
      1. Average Reward Convergence Curve
      2. Epsilon Decay and Bellman TD Error
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Average Reward per Episode (Policy Convergence)", "Exploration Rate (ε) & Bellman TD Error"),
        vertical_spacing=0.12
    )

    # Panel 1: Reward Curve
    fig.add_trace(
        go.Scatter(
            x=metrics["episodes"],
            y=metrics["average_rewards"],
            mode="lines+markers",
            name="Avg Reward",
            line=dict(color="#10b981", width=2.5),
            marker=dict(size=4)
        ),
        row=1, col=1
    )

    # Panel 2: Epsilon Decay & TD Error
    fig.add_trace(
        go.Scatter(
            x=metrics["episodes"],
            y=metrics["epsilon_history"],
            mode="lines",
            name="Epsilon (ε)",
            line=dict(color="#6366f1", width=2, dash="dash")
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=metrics["episodes"],
            y=metrics["td_error_history"],
            mode="lines",
            name="TD Error",
            line=dict(color="#f59e0b", width=2)
        ),
        row=2, col=1
    )

    fig.update_layout(
        title="Adaptive Q-Learning Convergence - Hospital Access Control",
        template="plotly_dark",
        height=650,
        hovermode="x unified",
        margin=dict(l=40, r=40, t=80, b=40)
    )
    fig.update_xaxes(title_text="Training Episodes", row=2, col=1)
    fig.update_yaxes(title_text="Reward", row=1, col=1)
    fig.update_yaxes(title_text="Value", row=2, col=1)

    fig.write_html(str(output_path), include_plotlyjs="cdn")
    print(f"[+] Interactive Plotly training chart saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Tabular Q-Learning Agent for Hospital Access Control")
    parser.add_argument("--episodes", type=int, default=35000, help="Number of training episodes (default: 35000)")
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate alpha (default: 0.1)")
    parser.add_argument("--gamma", type=float, default=0.90, help="Discount factor gamma (default: 0.90)")
    args = parser.parse_args()

    train_agent(episodes=args.episodes, learning_rate=args.lr, discount_factor=args.gamma)
