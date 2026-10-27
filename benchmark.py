"""
Benchmark: Brute Force vs Aho-Corasick Multi-Pattern Search
=============================================================
REAL-TIME TIMING VERSION
- Shows a live elapsed timer while each algorithm is running
- Prints character-by-character progress so you see it working
- Produces results.csv and benchmark_report.png at the end
"""

import time
import random
import csv
import sys
import os
import threading

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

from brute_force  import brute_force_search
from aho_corasick import aho_corasick_search

# ─────────────────────────────────────────────────────────────────────────────
# LIVE TIMER THREAD
# Runs in the background and updates the console every 0.1s
# while the algorithm is running in the main thread
# ─────────────────────────────────────────────────────────────────────────────
class LiveTimer:
    """
    Displays a live elapsed time counter on the same console line.
    Start before running the algorithm, stop immediately after.

    Usage:
        timer = LiveTimer("  Brute Force running")
        timer.start()
        result = run_algorithm()
        elapsed = timer.stop()
    """
    def __init__(self, label: str):
        self.label     = label
        self._start    = None
        self._running  = False
        self._thread   = None

    def _tick(self):
        """Background thread: rewrite the current line every 100ms."""
        while self._running:
            elapsed = time.perf_counter() - self._start
            # \r returns cursor to start of line so we overwrite in place
            sys.stdout.write(f"\r  {self.label}  [{elapsed:>8.3f}s elapsed]  ...")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        self._start   = time.perf_counter()
        self._running = True
        self._thread  = threading.Thread(target=self._tick, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        self._running = False
        self._thread.join()
        elapsed = time.perf_counter() - self._start
        # Clear the live line and print the final time cleanly
        sys.stdout.write(f"\r  {self.label}  DONE — {elapsed*1000:>10.3f} ms ({elapsed:.4f}s)\n")
        sys.stdout.flush()
        return elapsed


# ─────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────
DNA_ALPHABET = "ATCG"
SEED = 42

def generate_dna(length: int, rng: random.Random) -> str:
    return "".join(rng.choice(DNA_ALPHABET) for _ in range(length))

def generate_patterns(count: int, length: int, rng: random.Random) -> list:
    return [generate_dna(length, rng) for _ in range(count)]

def embed_patterns(text: str, patterns: list, rng: random.Random,
                   embed_count: int = 3) -> str:
    text_list = list(text)
    for pattern in patterns[:embed_count]:
        if len(pattern) <= len(text):
            pos = rng.randint(0, len(text) - len(pattern))
            text_list[pos:pos + len(pattern)] = list(pattern)
    return "".join(text_list)


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK CONFIGURATIONS
# ─────────────────────────────────────────────────────────────────────────────
CONFIGS = [
    {"label": "Config 1", "text_len":    10_000, "pat_count":   5, "pat_len":  8},
    {"label": "Config 2", "text_len":   100_000, "pat_count":   5, "pat_len":  8},
    {"label": "Config 3", "text_len":   100_000, "pat_count":  20, "pat_len":  8},
    {"label": "Config 4", "text_len": 1_000_000, "pat_count":  20, "pat_len": 10},
    {"label": "Config 5", "text_len": 1_000_000, "pat_count":  50, "pat_len": 10},
    {"label": "Config 6", "text_len": 5_000_000, "pat_count": 100, "pat_len": 12},
]

REPEATS = 3


# ─────────────────────────────────────────────────────────────────────────────
# RUN ONE CONFIGURATION WITH LIVE TIMING
# ─────────────────────────────────────────────────────────────────────────────
def run_benchmark(cfg: dict) -> dict:
    rng      = random.Random(SEED)
    patterns = generate_patterns(cfg["pat_count"], cfg["pat_len"], rng)
    text     = generate_dna(cfg["text_len"], rng)
    text     = embed_patterns(text, patterns, rng)

    print()
    print(f"┌─ {cfg['label']} "
          f"{'─' * (54 - len(cfg['label']))}")
    print(f"│  Text length  : {cfg['text_len']:>10,} characters")
    print(f"│  Pattern count: {cfg['pat_count']:>10}  ×  {cfg['pat_len']} chars each")
    print(f"│  Repeats      : {REPEATS} runs averaged")
    print(f"│")

    # ── Brute Force with live timer ──────────────────────────────────────────
    print(f"│  [BRUTE FORCE]")
    bf_times = []
    for rep in range(REPEATS):
        print(f"│    Run {rep+1}/{REPEATS}:", end="")
        sys.stdout.flush()

        timer = LiveTimer(f"Brute Force run {rep+1}")
        timer.start()
        bf_matches, bf_comps = brute_force_search(text, patterns)
        elapsed_bf = timer.stop()

        # Re-prefix the timer's output line with the border character
        bf_times.append(elapsed_bf)

    bf_ms  = (sum(bf_times) / len(bf_times)) * 1000
    bf_min = min(bf_times) * 1000
    bf_max = max(bf_times) * 1000
    print(f"│    Average: {bf_ms:.3f} ms  "
          f"(min {bf_min:.3f} / max {bf_max:.3f} ms)")
    print(f"│    Comparisons: {bf_comps:,}")
    print(f"│    Matches found: {len(bf_matches)}")
    print(f"│")

    # ── Aho-Corasick with live timer ─────────────────────────────────────────
    print(f"│  [AHO-CORASICK]")
    ac_times = []
    for rep in range(REPEATS):
        print(f"│    Run {rep+1}/{REPEATS}:", end="")
        sys.stdout.flush()

        timer = LiveTimer(f"Aho-Corasick run {rep+1}")
        timer.start()
        ac_matches, ac_comps = aho_corasick_search(text, patterns)
        elapsed_ac = timer.stop()

        ac_times.append(elapsed_ac)

    ac_ms  = (sum(ac_times) / len(ac_times)) * 1000
    ac_min = min(ac_times) * 1000
    ac_max = max(ac_times) * 1000
    print(f"│    Average: {ac_ms:.3f} ms  "
          f"(min {ac_min:.3f} / max {ac_max:.3f} ms)")
    print(f"│    Comparisons: {ac_comps:,}")
    print(f"│    Matches found: {len(ac_matches)}")
    print(f"│")

    # ── Result ───────────────────────────────────────────────────────────────
    speedup        = bf_ms / ac_ms if ac_ms > 0 else float("inf")
    comp_reduction = (1 - ac_comps / bf_comps) * 100 if bf_comps > 0 else 0
    correct        = set(bf_matches) == set(ac_matches)

    print(f"│  ══ RESULT ══════════════════════════════════════")
    print(f"│  Speedup           : {speedup:.1f}×  "
          f"(AC is {speedup:.1f} times faster)")
    print(f"│  Comparison reduction: {comp_reduction:.1f}% fewer lookups")
    print(f"│  Correctness       : {'✓ PASS — identical matches' if correct else '✗ FAIL — MISMATCH'}")
    print(f"└{'─'*58}")

    return {
        "label"              : cfg["label"],
        "text_length"        : cfg["text_len"],
        "pattern_count"      : cfg["pat_count"],
        "pattern_length"     : cfg["pat_len"],
        "bf_time_ms"         : round(bf_ms, 3),
        "bf_min_ms"          : round(bf_min, 3),
        "bf_max_ms"          : round(bf_max, 3),
        "ac_time_ms"         : round(ac_ms, 3),
        "ac_min_ms"          : round(ac_min, 3),
        "ac_max_ms"          : round(ac_max, 3),
        "bf_comparisons"     : bf_comps,
        "ac_comparisons"     : ac_comps,
        "speedup"            : round(speedup, 2),
        "comp_reduction_pct" : round(comp_reduction, 1),
        "matches_bf"         : len(bf_matches),
        "matches_ac"         : len(ac_matches),
        "correct"            : correct,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SAVE CSV
# ─────────────────────────────────────────────────────────────────────────────
def save_csv(results: list, path: str):
    if not results:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  Saved CSV : {path}")


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCE CHART
# ─────────────────────────────────────────────────────────────────────────────
def save_chart(results: list, path: str):
    if not HAS_PLOT:
        return

    labels     = [r["label"]          for r in results]
    bf_times   = [r["bf_time_ms"]     for r in results]
    ac_times   = [r["ac_time_ms"]     for r in results]
    bf_comps   = [r["bf_comparisons"] for r in results]
    ac_comps   = [r["ac_comparisons"] for r in results]
    speedups   = [r["speedup"]        for r in results]
    pat_counts = [r["pattern_count"]  for r in results]

    x     = range(len(labels))
    bar_w = 0.35
    NAVY  = "#1A2B4A"
    GREEN = "#2D6A4F"
    RED   = "#C0392B"

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Aho-Corasick (1975) vs Brute Force — Real-Time Benchmarking Results\n"
        "Honours Research Project — Pattern Matching Performance Analysis",
        fontsize=13, fontweight="bold"
    )

    # Panel 1: Execution Time (log scale)
    ax1 = axes[0, 0]
    b1 = ax1.bar([i - bar_w/2 for i in x], bf_times, bar_w,
                 label="Brute Force",   color=RED,  alpha=0.85)
    b2 = ax1.bar([i + bar_w/2 for i in x], ac_times, bar_w,
                 label="Aho-Corasick", color=NAVY, alpha=0.85)
    ax1.set_title("Execution Time (ms) — log scale", fontweight="bold")
    ax1.set_ylabel("Time (ms)")
    ax1.set_xticks(list(x)); ax1.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax1.set_yscale("log")
    ax1.yaxis.set_major_formatter(ticker.ScalarFormatter())
    ax1.legend(); ax1.grid(axis="y", alpha=0.3)
    for bar in b1:
        h = bar.get_height()
        ax1.text(bar.get_x()+bar.get_width()/2, h*1.08, f"{h:.1f}",
                 ha="center", va="bottom", fontsize=7, color=RED)
    for bar in b2:
        h = bar.get_height()
        ax1.text(bar.get_x()+bar.get_width()/2, h*1.08, f"{h:.1f}",
                 ha="center", va="bottom", fontsize=7, color=NAVY)

    # Panel 2: Character Comparisons
    ax2 = axes[0, 1]
    ax2.bar([i - bar_w/2 for i in x], [c/1e6 for c in bf_comps], bar_w,
            label="Brute Force",   color=RED,  alpha=0.85)
    ax2.bar([i + bar_w/2 for i in x], [c/1e6 for c in ac_comps], bar_w,
            label="Aho-Corasick", color=NAVY, alpha=0.85)
    ax2.set_title("Character Comparisons (millions)", fontweight="bold")
    ax2.set_ylabel("Comparisons (× 10⁶)")
    ax2.set_xticks(list(x)); ax2.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax2.legend(); ax2.grid(axis="y", alpha=0.3)

    # Panel 3: Speedup bar
    ax3 = axes[1, 0]
    bars3 = ax3.bar(list(x), speedups, color=GREEN, alpha=0.85)
    ax3.set_title("Speedup: Aho-Corasick over Brute Force", fontweight="bold")
    ax3.set_ylabel("Speedup Factor (×)")
    ax3.set_xticks(list(x)); ax3.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax3.axhline(y=1, color="gray", linestyle="--", alpha=0.5)
    ax3.grid(axis="y", alpha=0.3)
    for bar, sp in zip(bars3, speedups):
        ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                 f"{sp:.1f}×", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=GREEN)

    # Panel 4: Speedup vs Pattern Count (key research finding)
    ax4 = axes[1, 1]
    ax4.plot(pat_counts, speedups, "o-", color=NAVY, linewidth=2, markersize=8)
    ax4.fill_between(pat_counts, speedups, alpha=0.15, color=NAVY)
    ax4.set_title("Speedup vs Pattern Count\n(Key Finding: AC advantage grows with k)",
                  fontweight="bold")
    ax4.set_xlabel("Number of Patterns (k)")
    ax4.set_ylabel("Speedup Factor (×)")
    ax4.axhline(y=1, color="gray", linestyle="--", alpha=0.5)
    ax4.grid(alpha=0.3)
    for xp, yp in zip(pat_counts, speedups):
        ax4.annotate(f"{yp:.1f}×", (xp, yp),
                     textcoords="offset points", xytext=(4, 6),
                     fontsize=8, color=NAVY)

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved PNG : {path}")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY TABLE
# ─────────────────────────────────────────────────────────────────────────────
def print_summary(results: list):
    print("\n")
    print("═" * 105)
    print("  FINAL BENCHMARK SUMMARY")
    print("═" * 105)
    print(f"  {'Config':<10} {'Text Len':>10} {'Patterns':>9} "
          f"{'BF Avg':>11} {'AC Avg':>11} {'Speedup':>9} "
          f"{'BF Comps':>14} {'AC Comps':>12} {'Comp Red%':>10} {'OK':>5}")
    print("  " + "─" * 103)
    for r in results:
        print(
            f"  {r['label']:<10} "
            f"{r['text_length']:>10,} "
            f"{r['pattern_count']:>9} "
            f"{r['bf_time_ms']:>10.2f}ms "
            f"{r['ac_time_ms']:>10.2f}ms "
            f"{r['speedup']:>8.1f}× "
            f"{r['bf_comparisons']:>14,} "
            f"{r['ac_comparisons']:>12,} "
            f"{r['comp_reduction_pct']:>9.1f}% "
            f"{'✓' if r['correct'] else '✗':>5}"
        )
    print("═" * 105)
    total_bf = sum(r["bf_time_ms"] for r in results)
    total_ac = sum(r["ac_time_ms"] for r in results)
    print(f"\n  Total wall-clock time — Brute Force : {total_bf:>10,.2f} ms  "
          f"({total_bf/1000:.2f}s)")
    print(f"  Total wall-clock time — Aho-Corasick: {total_ac:>10,.2f} ms  "
          f"({total_ac/1000:.2f}s)")
    print(f"  Overall speedup                      : {total_bf/total_ac:.1f}×")
    print(f"  All results correct                  : "
          f"{'YES — every match verified' if all(r['correct'] for r in results) else 'NO — CHECK CODE'}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("═" * 60)
    print("  REAL-TIME BENCHMARK")
    print("  Brute Force vs Aho-Corasick (CACM 1975)")
    print(f"  {len(CONFIGS)} configurations × {REPEATS} repeats each")
    print("  Timer updates every 100ms while algorithm runs")
    print("═" * 60)

    results = []
    overall_start = time.perf_counter()

    for cfg in CONFIGS:
        results.append(run_benchmark(cfg))

    overall_elapsed = time.perf_counter() - overall_start
    print(f"\n  Total benchmark wall-clock time: {overall_elapsed:.2f}s")

    print_summary(results)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    save_csv(results,  os.path.join(out_dir, "results.csv"))
    save_chart(results, os.path.join(out_dir, "benchmark_report.png"))
    print("\n  All done.")
