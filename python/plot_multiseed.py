import os
import pandas as pd
import matplotlib.pyplot as plt


RESULTS_FILE = "results/multiseed_policy_results.csv"
OUTPUT_DIR = "results"


def plot_metric(summary: pd.DataFrame, metric: str, ylabel: str, filename: str) -> None:
    policies = summary.index.tolist()
    means = summary[(metric, "mean")]
    stds = summary[(metric, "std")]

    plt.figure(figsize=(10, 6))
    plt.bar(
        policies,
        means,
        yerr=stds,
        capsize=6,
    )

    plt.xlabel("Quoting Policy")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} Across 30 Monte Carlo Seeds")
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(output_path, dpi=220)
    plt.close()

    print(f"Saved: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = pd.read_csv(RESULTS_FILE)

    metrics = [
        "final_pnl",
        "max_drawdown",
        "inventory_std",
        "sharpe_like",
    ]

    summary = (
        results
        .groupby("policy")[metrics]
        .agg(["mean", "std"])
    )

    preferred_order = [
        "fixed",
        "inventory",
        "volatility",
        "inventory_volatility",
    ]

    summary = summary.reindex(preferred_order)

    plot_metric(
        summary,
        metric="final_pnl",
        ylabel="Final PnL",
        filename="multiseed_pnl_errorbars.png",
    )

    plot_metric(
        summary,
        metric="max_drawdown",
        ylabel="Maximum Drawdown",
        filename="multiseed_drawdown_errorbars.png",
    )

    plot_metric(
        summary,
        metric="inventory_std",
        ylabel="Inventory Standard Deviation",
        filename="multiseed_inventory_risk_errorbars.png",
    )

    plot_metric(
        summary,
        metric="sharpe_like",
        ylabel="Sharpe-like PnL Stability",
        filename="multiseed_sharpe_errorbars.png",
    )


if __name__ == "__main__":
    main()
