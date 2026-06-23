import os
import sys
import time

sys.path.append(os.path.dirname(__file__))

from simulator import MarketMakerConfig, MarketMakingSimulator


def main():
    n_steps = 200_000

    config = MarketMakerConfig(
        n_steps=n_steps,
        initial_midprice=100.0,
        volatility=0.03,
        order_arrival_prob=0.40,
        informed_order_prob=0.20,
        base_half_spread=0.06,
        inventory_skew=0.015,
        volatility_spread_multiplier=1.5,
        fill_probability=0.75,
        transaction_cost=0.002,
        max_inventory=20,
        seed=42,
    )

    simulator = MarketMakingSimulator(
        config=config,
        policy="inventory_volatility",
    )

    start = time.perf_counter()
    df = simulator.run()
    runtime_seconds = time.perf_counter() - start

    print(f"final_pnl={df['pnl'].iloc[-1]}")
    print(f"fills={df['fills'].iloc[-1]}")
    print(f"final_inventory={df['inventory'].iloc[-1]}")
    print(f"runtime_seconds={runtime_seconds:.6f}")


if __name__ == "__main__":
    main()
