import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(__file__))

from simulator import (
    MarketMakerConfig,
    MarketMakingSimulator,
    summarize_results,
)


def run_policy(policy: str, config: MarketMakerConfig):
    simulator = MarketMakingSimulator(config=config, policy=policy)
    df = simulator.run()

    summary = summarize_results(df)
    summary["policy"] = policy

    return df, summary


def plot_results(results: dict[str, pd.DataFrame]) -> None:
    os.makedirs("results", exist_ok=True)

    plt.figure(figsize=(12, 6))
    for policy, df in results.items():
        plt.plot(df["step"], df["pnl"], label=policy)

    plt.xlabel("Simulation Step")
    plt.ylabel("Mark-to-Market PnL")
    plt.title("Market-Making PnL by Quoting Policy")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/pnl_comparison.png", dpi=200)
    plt.close()

    plt.figure(figsize=(12, 6))
    for policy, df in results.items():
        plt.plot(df["step"], df["inventory"], label=policy)

    plt.xlabel("Simulation Step")
    plt.ylabel("Inventory")
    plt.title("Inventory Trajectory by Quoting Policy")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/inventory_comparison.png", dpi=200)
    plt.close()


def main():
    os.makedirs("results", exist_ok=True)

    config = MarketMakerConfig(
        n_steps=20_000,
        initial_midprice=100.0,
        volatility=0.03,
        order_arrival_prob=0.40,
        informed_order_prob=0.20,
        base_half_spread=0.06,
        inventory_skew=0.015,
        max_inventory=20,
        seed=42,
    )

    policies = [
        "fixed",
        "inventory",
        "volatility",
        "inventory_volatility",
    ]

    all_results = {}
    summaries = []

    for policy in policies:
        df, summary = run_policy(policy, config)
        all_results[policy] = df
        summaries.append(summary)

        df.to_csv(f"results/{policy}_path.csv", index=False)

    summary_df = pd.DataFrame(summaries)

    columns = [
        "policy",
        "final_pnl",
        "final_risk_adjusted_pnl",
        "total_fills",
        "max_inventory",
        "inventory_std",
        "max_drawdown",
        "adverse_selection_cost",
        "sharpe_like",
    ]

    summary_df = summary_df[columns]
    summary_df.to_csv("results/policy_summary.csv", index=False)

    print("\nPolicy Comparison\n")
    print(summary_df.to_string(index=False))

    plot_results(all_results)


if __name__ == "__main__":
    main()
