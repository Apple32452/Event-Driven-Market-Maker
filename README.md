# Event-Driven Market Maker

A reproducible Python simulator for studying market-making policies under stochastic price dynamics, order flow, inventory constraints, adverse selection, and transaction costs.

## Overview

This project simulates a simplified event-driven market-making environment in which a dealer posts bid and ask quotes around a stochastic mid-price. Incoming market orders may interact with those quotes, producing fills, inventory changes, PnL, drawdown, and adverse-selection effects.

The simulator compares four policies:

- **Fixed Spread** — constant bid-ask spread around the mid-price.
- **Inventory Skew** — shifts quotes to reduce unwanted inventory.
- **Volatility Aware** — widens spreads when volatility is high.
- **Inventory + Volatility** — combines inventory-aware quote skew with volatility-aware spread widening.

## Main Result

Across 30 Monte Carlo seeds, the volatility-aware policy produced the highest mean raw PnL, while the combined **Inventory + Volatility** policy produced the strongest risk-adjusted performance.

| Policy | Mean Final PnL | PnL Std. Dev. | Mean Drawdown | Inventory Std. Dev. | Sharpe-like Stability |
|---|---:|---:|---:|---:|---:|
| Fixed Spread | 198.33 | 58.36 | 31.69 | 10.99 | 3.95 |
| Inventory Skew | 175.94 | 7.48 | 3.02 | 2.12 | 18.63 |
| Volatility Aware | 254.69 | 51.71 | 28.02 | 10.41 | 5.11 |
| Inventory + Volatility | 243.93 | 8.45 | 2.70 | 2.07 | 24.64 |

Compared with volatility-only quoting, the combined policy retained about 96% of mean PnL while reducing mean drawdown by about 90%, inventory volatility by about 80%, and cross-run PnL variation by about 84%.

## Figures

### Mean PnL Across 30 Monte Carlo Seeds

![Mean PnL](results/multiseed_pnl_errorbars.png)

### Maximum Drawdown

![Maximum Drawdown](results/multiseed_drawdown_errorbars.png)

### Inventory Risk

![Inventory Risk](results/multiseed_inventory_risk_errorbars.png)

### Sharpe-like PnL Stability

![Sharpe-like Stability](results/multiseed_sharpe_errorbars.png)

## Project Structure

```text
market-making-simulator/
├── configs/
├── python/
│   ├── simulator.py
│   ├── run_experiment.py
│   ├── run_multiseed.py
│   └── plot_multiseed.py
├── results/
│   ├── policy_summary.csv
│   ├── multiseed_policy_results.csv
│   ├── multiseed_policy_summary.csv
│   ├── multiseed_pnl_errorbars.png
│   ├── multiseed_drawdown_errorbars.png
│   ├── multiseed_inventory_risk_errorbars.png
│   └── multiseed_sharpe_errorbars.png
├── requirements.txt
└── README.md
