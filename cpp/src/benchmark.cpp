#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>

struct Config {
    int n_steps = 200000;
    double initial_midprice = 100.0;
    double volatility = 0.03;
    double order_arrival_prob = 0.40;
    double informed_order_prob = 0.20;
    double base_half_spread = 0.06;
    double inventory_skew = 0.015;
    double volatility_spread_multiplier = 1.5;
    double fill_probability = 0.75;
    double transaction_cost = 0.002;
    int max_inventory = 20;
    unsigned int seed = 42;
};

struct State {
    double midprice;
    int inventory = 0;
    double cash = 0.0;
    int fills = 0;
    double adverse_selection_cost = 0.0;
};

double get_half_spread(const Config& cfg, const std::string& policy) {
    if (policy == "fixed" || policy == "inventory") {
        return cfg.base_half_spread;
    }

    return cfg.base_half_spread +
           cfg.volatility_spread_multiplier * cfg.volatility;
}

void run_simulation(const Config& cfg, const std::string& policy) {
    State state{cfg.initial_midprice};

    std::mt19937 rng(cfg.seed);
    std::uniform_real_distribution<double> uniform(0.0, 1.0);
    std::normal_distribution<double> normal(0.0, cfg.volatility);

    for (int t = 0; t < cfg.n_steps; ++t) {
        const double half_spread = get_half_spread(cfg, policy);

        double inventory_adjustment = 0.0;
        if (policy == "inventory" || policy == "inventory_volatility") {
            inventory_adjustment = cfg.inventory_skew * state.inventory;
        }

        const double reservation_price = state.midprice - inventory_adjustment;
        const double bid = reservation_price - half_spread;
        const double ask = reservation_price + half_spread;

        const double next_price_move = normal(rng);

        if (uniform(rng) < cfg.order_arrival_prob) {
            const bool informed = uniform(rng) < cfg.informed_order_prob;

            bool incoming_buy = false;
            if (informed) {
                incoming_buy = next_price_move >= 0.0;
            } else {
                incoming_buy = uniform(rng) < 0.5;
            }

            double quote_distance = 0.0;

            if (incoming_buy) {
                quote_distance = std::max(0.0, ask - state.midprice);
            } else {
                quote_distance = std::max(0.0, state.midprice - bid);
            }

            const double competitiveness = std::exp(-8.0 * quote_distance);
            const double fill_prob =
                std::min(1.0, cfg.fill_probability * competitiveness);

            if (uniform(rng) < fill_prob) {
                if (incoming_buy && state.inventory > -cfg.max_inventory) {
                    state.inventory -= 1;
                    state.cash += ask - cfg.transaction_cost;
                    state.fills += 1;

                    if (next_price_move > 0.0) {
                        state.adverse_selection_cost += next_price_move;
                    }
                } else if (!incoming_buy && state.inventory < cfg.max_inventory) {
                    state.inventory += 1;
                    state.cash -= bid + cfg.transaction_cost;
                    state.fills += 1;

                    if (next_price_move < 0.0) {
                        state.adverse_selection_cost += std::abs(next_price_move);
                    }
                }
            }
        }

        state.midprice = std::max(0.01, state.midprice + next_price_move);
    }

    const double pnl = state.cash + state.inventory * state.midprice;

    std::cout << "final_pnl=" << pnl
              << ",fills=" << state.fills
              << ",final_inventory=" << state.inventory
              << ",adverse_selection_cost=" << state.adverse_selection_cost
              << '\n';
}

int main(int argc, char* argv[]) {
    int n_steps = 200000;

    if (argc > 1) {
        n_steps = std::stoi(argv[1]);
    }

    Config cfg;
    cfg.n_steps = n_steps;

    const auto start = std::chrono::high_resolution_clock::now();

    run_simulation(cfg, "inventory_volatility");

    const auto end = std::chrono::high_resolution_clock::now();

    const std::chrono::duration<double> elapsed = end - start;

    std::cout << std::fixed << std::setprecision(6);
    std::cout << "runtime_seconds=" << elapsed.count() << '\n';

    return 0;
}
