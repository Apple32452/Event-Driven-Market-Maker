from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np
import pandas as pd


@dataclass
class MarketMakerConfig:
    n_steps: int = 20_000
    initial_midprice: float = 100.0

    # Market dynamics
    volatility: float = 0.02
    order_arrival_prob: float = 0.35
    informed_order_prob: float = 0.15

    # Quoting parameters
    base_half_spread: float = 0.05
    inventory_skew: float = 0.01
    volatility_spread_multiplier: float = 1.5

    # Risk constraints
    max_inventory: int = 20
    inventory_penalty: float = 0.0005

    # Execution assumptions
    fill_probability: float = 0.75
    transaction_cost: float = 0.002

    seed: int = 42


@dataclass
class MarketMakerState:
    midprice: float
    inventory: int = 0
    cash: float = 0.0
    total_fills: int = 0
    buy_fills: int = 0
    sell_fills: int = 0
    adverse_selection_cost: float = 0.0

    history: List[Dict] = field(default_factory=list)


class MarketMakingSimulator:
    def __init__(self, config: MarketMakerConfig, policy: str = "inventory_volatility"):
        self.config = config
        self.policy = policy
        self.rng = np.random.default_rng(config.seed)

        self.state = MarketMakerState(
            midprice=config.initial_midprice
        )

    def get_half_spread(self) -> float:
        cfg = self.config

        if self.policy in {"fixed", "inventory"}:
            return cfg.base_half_spread

        if self.policy in {"volatility", "inventory_volatility"}:
            return (
                cfg.base_half_spread
                + cfg.volatility_spread_multiplier * cfg.volatility
            )

        raise ValueError(f"Unknown policy: {self.policy}")

    def get_quotes(self) -> tuple[float, float]:
        cfg = self.config
        state = self.state

        half_spread = self.get_half_spread()
        inventory_adjustment = 0.0

        if self.policy in {"inventory", "inventory_volatility"}:
            inventory_adjustment = cfg.inventory_skew * state.inventory

        reservation_price = state.midprice - inventory_adjustment

        bid = reservation_price - half_spread
        ask = reservation_price + half_spread

        return bid, ask

    def generate_order_flow(self, next_price_move: float) -> str | None:
        cfg = self.config

        if self.rng.random() > cfg.order_arrival_prob:
            return None

        is_informed = self.rng.random() < cfg.informed_order_prob

        if is_informed:
            if next_price_move > 0:
                return "buy"
            if next_price_move < 0:
                return "sell"

        return "buy" if self.rng.random() < 0.5 else "sell"

    def attempt_fill(
        self,
        side: str,
        bid: float,
        ask: float,
        next_price_move: float,
    ) -> None:
        """
        Fill probability depends on quote competitiveness.

        Quotes farther from the midprice are less likely to fill.
        """
        cfg = self.config
        state = self.state

        if side == "buy":
            # External market buy may hit our ask.
            quote_distance = max(0.0, ask - state.midprice)

        elif side == "sell":
            # External market sell may hit our bid.
            quote_distance = max(0.0, state.midprice - bid)

        else:
            return

        # Wider / less competitive quotes receive fewer fills.
        competitiveness = np.exp(-8.0 * quote_distance)

        fill_probability = min(
            1.0,
            cfg.fill_probability * competitiveness,
        )

        if self.rng.random() > fill_probability:
            return

        if side == "buy":
            if state.inventory <= -cfg.max_inventory:
                return

            state.inventory -= 1
            state.cash += ask - cfg.transaction_cost
            state.total_fills += 1
            state.sell_fills += 1

            if next_price_move > 0:
                state.adverse_selection_cost += next_price_move

        elif side == "sell":
            if state.inventory >= cfg.max_inventory:
                return

            state.inventory += 1
            state.cash -= bid + cfg.transaction_cost
            state.total_fills += 1
            state.buy_fills += 1

            if next_price_move < 0:
                state.adverse_selection_cost += abs(next_price_move)

    def mark_to_market_pnl(self) -> float:
        state = self.state
        return state.cash + state.inventory * state.midprice

    def run(self) -> pd.DataFrame:
        for t in range(self.config.n_steps):
            bid, ask = self.get_quotes()

            next_price_move = self.rng.normal(
                loc=0.0,
                scale=self.config.volatility,
            )

            incoming_order = self.generate_order_flow(next_price_move)

            if incoming_order is not None:
                self.attempt_fill(
                    side=incoming_order,
                    bid=bid,
                    ask=ask,
                    next_price_move=next_price_move,
                )

            self.state.midprice = max(
                0.01,
                self.state.midprice + next_price_move,
            )

            pnl = self.mark_to_market_pnl()

            inventory_penalty = (
                self.config.inventory_penalty
                * self.state.inventory ** 2
            )

            risk_adjusted_pnl = pnl - inventory_penalty

            self.state.history.append(
                {
                    "step": t,
                    "midprice": self.state.midprice,
                    "bid": bid,
                    "ask": ask,
                    "inventory": self.state.inventory,
                    "cash": self.state.cash,
                    "pnl": pnl,
                    "risk_adjusted_pnl": risk_adjusted_pnl,
                    "fills": self.state.total_fills,
                    "adverse_selection_cost": self.state.adverse_selection_cost,
                    "incoming_order": incoming_order,
                }
            )

        return pd.DataFrame(self.state.history)


def summarize_results(df: pd.DataFrame) -> Dict[str, float]:
    pnl_changes = df["pnl"].diff().dropna()

    max_drawdown = (
        df["pnl"].cummax() - df["pnl"]
    ).max()

    sharpe_like = 0.0
    if pnl_changes.std() > 1e-12:
        sharpe_like = (
            pnl_changes.mean() / pnl_changes.std()
        ) * np.sqrt(len(pnl_changes))

    return {
        "final_pnl": float(df["pnl"].iloc[-1]),
        "final_risk_adjusted_pnl": float(df["risk_adjusted_pnl"].iloc[-1]),
        "total_fills": int(df["fills"].iloc[-1]),
        "max_inventory": int(df["inventory"].abs().max()),
        "inventory_std": float(df["inventory"].std()),
        "max_drawdown": float(max_drawdown),
        "adverse_selection_cost": float(df["adverse_selection_cost"].iloc[-1]),
        "sharpe_like": float(sharpe_like),
    }
