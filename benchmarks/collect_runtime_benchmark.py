from __future__ import annotations

import csv
import re
import statistics
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

N_RUNS = 5
N_EVENTS = 200_000

PYTHON_BENCHMARK = [
    sys.executable,
    str(ROOT / "python" / "benchmark_python.py"),
]

CPP_BINARY = ROOT / "cpp" / "build" / "market_making_benchmark"
CPP_BENCHMARK = [
    str(CPP_BINARY),
    str(N_EVENTS),
]


def parse_runtime(output: str) -> float:
    match = re.search(r"runtime_seconds=([0-9.]+)", output)

    if match is None:
        raise RuntimeError(
            "Could not find runtime_seconds in benchmark output:\n" + output
        )

    return float(match.group(1))


def run_benchmark(label: str, command: list[str]) -> list[dict]:
    rows = []

    for run_id in range(1, N_RUNS + 1):
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        runtime_seconds = parse_runtime(completed.stdout)

        rows.append(
            {
                "implementation": label,
                "run": run_id,
                "n_events": N_EVENTS,
                "runtime_seconds": runtime_seconds,
                "events_per_second": N_EVENTS / runtime_seconds,
            }
        )

    return rows


def main() -> None:
    if not CPP_BINARY.exists():
        raise FileNotFoundError(
            "C++ benchmark binary not found. Run:\n"
            "cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release\n"
            "cmake --build cpp/build"
        )

    RESULTS_DIR.mkdir(exist_ok=True)

    rows = []
    rows.extend(
        run_benchmark(
            "Python full-history workflow",
            PYTHON_BENCHMARK,
        )
    )
    rows.extend(
        run_benchmark(
            "C++ compute-only event loop",
            CPP_BENCHMARK,
        )
    )

    runs_path = RESULTS_DIR / "runtime_benchmark_runs.csv"

    with runs_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "implementation",
                "run",
                "n_events",
                "runtime_seconds",
                "events_per_second",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    implementations = [
        "Python full-history workflow",
        "C++ compute-only event loop",
    ]

    summary_rows = []
    python_mean = None

    for implementation in implementations:
        runtimes = [
            row["runtime_seconds"]
            for row in rows
            if row["implementation"] == implementation
        ]

        mean_runtime = statistics.mean(runtimes)
        std_runtime = statistics.stdev(runtimes)

        if implementation == "Python full-history workflow":
            python_mean = mean_runtime

        summary_rows.append(
            {
                "implementation": implementation,
                "n_events": N_EVENTS,
                "n_runs": N_RUNS,
                "mean_runtime_seconds": mean_runtime,
                "std_runtime_seconds": std_runtime,
                "mean_events_per_second": N_EVENTS / mean_runtime,
            }
        )

    for row in summary_rows:
        row["speedup_vs_python_workflow"] = (
            python_mean / row["mean_runtime_seconds"]
        )

    summary_path = RESULTS_DIR / "runtime_benchmark_summary.csv"

    with summary_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "implementation",
                "n_events",
                "n_runs",
                "mean_runtime_seconds",
                "std_runtime_seconds",
                "mean_events_per_second",
                "speedup_vs_python_workflow",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    labels = [row["implementation"] for row in summary_rows]
    means_ms = [
        1000.0 * row["mean_runtime_seconds"]
        for row in summary_rows
    ]
    stds_ms = [
        1000.0 * row["std_runtime_seconds"]
        for row in summary_rows
    ]

    plt.figure(figsize=(9, 6))
    plt.bar(labels, means_ms, yerr=stds_ms, capsize=6)
    plt.yscale("log")
    plt.xlabel("Implementation")
    plt.ylabel("Runtime per 200,000 events (milliseconds, log scale)")
    plt.title("Market-Making Simulation Runtime Benchmark")
    plt.xticks(rotation=12, ha="right")
    plt.figtext(
        0.5,
        0.01,
        "Python stores full event histories; C++ benchmark is compute-only. "
        "Interpret as a workflow benchmark, not a matched language comparison.",
        ha="center",
        fontsize=9,
    )
    plt.tight_layout(rect=[0, 0.07, 1, 1])

    plot_path = RESULTS_DIR / "runtime_benchmark.png"
    plt.savefig(plot_path, dpi=220)
    plt.close()

    print(f"Saved: {runs_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {plot_path}")


if __name__ == "__main__":
    main()
