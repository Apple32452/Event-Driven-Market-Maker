import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(__file__))

from simulator import (
    MarketMakerConfig,
    MarketMakingSimulator,
    summarize_results,
)


def run_one(policy: str, seed: int):
    config = MarketMakerConfig(
        n_steps=20_000,
        initial_midprice=100.0,
        volatility=0.03,
        order_arrival_prob=0.40,
        informed_order_prob=0.20,
        base_half_spread=0.06,
        inventory_skew=0.015,
        max_inventory=20,
        seed=seed,
    )

    simulator = MarketMakingSimulator(
        config=config,
        policy=policy,
    )

    df = simulator.run()
    summary = summarize_results(df)

    summary["policy"] = policy
    summary["seed"] = seed

    return summary


def main():
    os.makedirs("results", exist_ok=True)

    policies = [
        "fixed",
        "inventory",
        "volatility",
        "inventory_volatility",
    ]

    seeds = list(range(30))
    rows = []

    for policy in policies:
        for seed in seeds:
            rows.append(run_one(policy, seed))

    all_results = pd.DataFrame(rows)
    all_results.to_csv(
        "results/multiseed_policy_results.csv",
        index=False,
    )

    metrics = [
        "final_pnl",
        "final_risk_adjusted_pnl",
        "total_fills",
        "max_inventory",
        "inventory_std",
        "max_drawdown",
        "adverse_selection_cost",
        "sharpe_like",
    ]

    summary = (
        all_results
        .groupby("policy")[metrics]
        .agg(["mean", "std"])
        .round(4)
    )

    summary.to_csv("results/multiseed_policy_summary.csv")

    print("\nMulti-seed policy comparison: mean and standard deviation\n")
    print(summary)


if __name__ == "__main__":
    main()
