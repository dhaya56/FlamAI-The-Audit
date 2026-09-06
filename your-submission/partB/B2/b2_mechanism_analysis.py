from __future__ import annotations

import csv
from pathlib import Path


# ---------------------------------------------------------------------
# Paths and experiment definition
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

BENCH_LOG = (
    ROOT
    / "starter_kit"
    / "bench"
    / "bench_log.csv"
)

PROMPT_LEN = 3584


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def load_rows() -> list[dict]:
    """Load and sort the prompt-3584 sweep from the benchmark log."""
    rows = []

    with BENCH_LOG.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            if int(row["prompt_len"]) != PROMPT_LEN:
                continue

            rows.append(
                {
                    "batch_size": int(row["batch_size"]),
                    "prompt_len": int(row["prompt_len"]),
                    "gen_len": int(row["gen_len"]),
                    "wall_clock_s": float(row["wall_clock_s"]),
                    "reported_tok_s": float(row["reported_tok_s"]),
                    "ttft_ms_p50": float(row["ttft_ms_p50"]),
                    "itl_ms_p50": float(row["itl_ms_p50"]),
                    "e2e_ms_p95": float(row["e2e_ms_p95"]),
                    "preempted_seqs": int(row["preempted_seqs"]),
                    "kv_cache_util": float(row["kv_cache_util"]),
                }
            )

    rows.sort(key=lambda row: row["batch_size"])

    return rows


def pct_change(old: float, new: float) -> float | None:
    """Return percentage change, or None when the baseline is zero."""
    if old == 0:
        return None

    return ((new - old) / old) * 100.0


def print_change(
    metric: str,
    old: float,
    new: float,
    unit: str = "",
) -> None:
    """Print an absolute and percentage change."""
    delta = new - old
    pct = pct_change(old, new)

    if pct is None:
        pct_text = "N/A (baseline is zero)"
    else:
        pct_text = f"{pct:+.2f}%"

    print(
        f"{metric}: "
        f"{old} -> {new} "
        f"(delta={delta:+.3f}, "
        f"change={pct_text}){unit}"
    )


# ---------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------

def main():
    rows = load_rows()

    if len(rows) < 2:
        raise ValueError(
            "Expected at least two rows for prompt_len=3584."
        )

    # ================================================================
    # 1. Derived workload
    # ================================================================

    print("B2 — Mechanism Analysis")
    print()
    print(f"Filter: prompt_len = {PROMPT_LEN}")
    print()

    generation_lengths = {
        row["gen_len"]
        for row in rows
    }

    if len(generation_lengths) == 1:
        gen_len = rows[0]["gen_len"]
        tokens_per_request = PROMPT_LEN + gen_len

        print("=" * 90)
        print("1. DERIVED WORKLOAD")
        print("=" * 90)
        print()
        print(
            f"prompt_len + gen_len = "
            f"{PROMPT_LEN} + {gen_len} "
            f"= {tokens_per_request} tokens/request"
        )

    # ================================================================
    # 2. Independently verify reported_tok_s
    # ================================================================

    print()
    print("=" * 90)
    print("2. CHECK WHAT reported_tok_s REPRESENTS")
    print("=" * 90)
    print()

    for row in rows:
        batch = row["batch_size"]

        total_work = batch * (
            row["prompt_len"] + row["gen_len"]
        )

        derived_tok_s = (
            total_work / row["wall_clock_s"]
        )

        error = (
            row["reported_tok_s"] - derived_tok_s
        )

        print(
            f"batch {batch}: "
            f"({batch} × "
            f"({row['prompt_len']}+{row['gen_len']})) "
            f"/ {row['wall_clock_s']:.2f} "
            f"= {derived_tok_s:.2f} tok/s | "
            f"reported={row['reported_tok_s']:.2f} | "
            f"difference={error:+.2f}"
        )

    print()
    print(
        "Close agreement across rows indicates that "
        "reported_tok_s counts prompt + generated tokens "
        "per wall-clock second."
    )

    # ================================================================
    # 3. Automatically detect throughput reversals
    # ================================================================

    print()
    print("=" * 90)
    print("3. THROUGHPUT REVERSALS")
    print("=" * 90)
    print()

    reversals = []

    for previous, current in zip(rows, rows[1:]):
        if (
            current["batch_size"] > previous["batch_size"]
            and current["reported_tok_s"]
            < previous["reported_tok_s"]
        ):
            reversals.append(
                {
                    "previous": previous,
                    "current": current,
                }
            )

    if not reversals:
        print("No throughput reversals detected.")
    else:
        for reversal in reversals:
            previous = reversal["previous"]
            current = reversal["current"]

            pct = pct_change(
                previous["reported_tok_s"],
                current["reported_tok_s"],
            )

            print(
                f"batch {previous['batch_size']} -> "
                f"{current['batch_size']}: "
                f"{previous['reported_tok_s']:.1f} -> "
                f"{current['reported_tok_s']:.1f} tok/s "
                f"({pct:+.2f}%)"
            )

    # ================================================================
    # 4. Automatically select the first reversal window
    # ================================================================

    print()
    print("=" * 90)
    print("4. FIRST REVERSAL WINDOW")
    print("=" * 90)
    print()

    if not reversals:
        print("No reversal window available for mechanism analysis.")
        return

    first_reversal = reversals[0]

    pre_reversal = first_reversal["previous"]
    reversal = first_reversal["current"]

    following = None

    for row in rows:
        if row["batch_size"] > reversal["batch_size"]:
            following = row
            break

    print(
        f"Pre-reversal batch: {pre_reversal['batch_size']}"
    )

    print(
        f"First reversal batch: {reversal['batch_size']}"
    )

    if following is not None:
        print(
            f"Next post-reversal batch: "
            f"{following['batch_size']}"
        )

    # ================================================================
    # 5. Quantify the first reversal
    # ================================================================

    print()
    print("=" * 90)
    print("5. CAPACITY / LATENCY CHANGES AT FIRST REVERSAL")
    print("=" * 90)
    print()

    print(
        f"Pre-reversal batch {pre_reversal['batch_size']}: "
        f"reported_tok_s={pre_reversal['reported_tok_s']:.1f}, "
        f"kv_util={pre_reversal['kv_cache_util']:.2f}, "
        f"preempted={pre_reversal['preempted_seqs']}, "
        f"ttft_p50={pre_reversal['ttft_ms_p50']:.1f} ms, "
        f"itl_p50={pre_reversal['itl_ms_p50']:.2f} ms, "
        f"e2e_p95={pre_reversal['e2e_ms_p95']:.1f} ms"
    )

    print(
        f"First reversal batch {reversal['batch_size']}: "
        f"reported_tok_s={reversal['reported_tok_s']:.1f}, "
        f"kv_util={reversal['kv_cache_util']:.2f}, "
        f"preempted={reversal['preempted_seqs']}, "
        f"ttft_p50={reversal['ttft_ms_p50']:.1f} ms, "
        f"itl_p50={reversal['itl_ms_p50']:.2f} ms, "
        f"e2e_p95={reversal['e2e_ms_p95']:.1f} ms"
    )

    print()
    print("Quantified transition:")

    print_change(
        "reported_tok_s",
        pre_reversal["reported_tok_s"],
        reversal["reported_tok_s"],
        " tok/s",
    )

    print_change(
        "kv_cache_util",
        pre_reversal["kv_cache_util"],
        reversal["kv_cache_util"],
    )

    print_change(
        "preempted_seqs",
        pre_reversal["preempted_seqs"],
        reversal["preempted_seqs"],
    )

    print_change(
        "ttft_ms_p50",
        pre_reversal["ttft_ms_p50"],
        reversal["ttft_ms_p50"],
        " ms",
    )

    print_change(
        "itl_ms_p50",
        pre_reversal["itl_ms_p50"],
        reversal["itl_ms_p50"],
        " ms",
    )

    print_change(
        "e2e_ms_p95",
        pre_reversal["e2e_ms_p95"],
        reversal["e2e_ms_p95"],
        " ms",
    )

    # ================================================================
    # 6. Check whether degradation continues
    # ================================================================

    if following is not None:
        print()
        print("=" * 90)
        print("6. NEXT POST-REVERSAL ROW")
        print("=" * 90)
        print()

        print(
            f"batch {reversal['batch_size']} -> "
            f"{following['batch_size']}"
        )

        print_change(
            "reported_tok_s",
            reversal["reported_tok_s"],
            following["reported_tok_s"],
            " tok/s",
        )

        print_change(
            "kv_cache_util",
            reversal["kv_cache_util"],
            following["kv_cache_util"],
        )

        print_change(
            "preempted_seqs",
            reversal["preempted_seqs"],
            following["preempted_seqs"],
        )

        print_change(
            "ttft_ms_p50",
            reversal["ttft_ms_p50"],
            following["ttft_ms_p50"],
            " ms",
        )

        print_change(
            "itl_ms_p50",
            reversal["itl_ms_p50"],
            following["itl_ms_p50"],
            " ms",
        )

        print_change(
            "e2e_ms_p95",
            reversal["e2e_ms_p95"],
            following["e2e_ms_p95"],
            " ms",
        )

    # ================================================================
    # 7. Data-derived preemption-free operating point
    # ================================================================

    print()
    print("=" * 90)
    print("7. DATA-DERIVED PREEMPTION-FREE OPERATING POINT")
    print("=" * 90)
    print()

    preemption_free = [
        row
        for row in rows
        if row["preempted_seqs"] == 0
    ]

    if not preemption_free:
        print("No preemption-free operating point found.")
        return

    last_safe = max(
        preemption_free,
        key=lambda row: row["batch_size"],
    )

    print(
        f"Last preemption-free batch: "
        f"{last_safe['batch_size']}"
    )

    print(
        f"reported_tok_s = "
        f"{last_safe['reported_tok_s']:.1f}"
    )

    print(
        f"kv_cache_util = "
        f"{last_safe['kv_cache_util']:.2f}"
    )

    # Compare safe operating point with first reversal.
    safe_vs_reversal = pct_change(
        reversal["reported_tok_s"],
        last_safe["reported_tok_s"],
    )

    print()
    print(
        "Observed throughput difference between "
        "the first reversal row and the last "
        "preemption-free row:"
    )

    print(
        f"{reversal['reported_tok_s']:.1f} -> "
        f"{last_safe['reported_tok_s']:.1f} tok/s "
        f"({safe_vs_reversal:+.2f}%)"
    )

    # Compare safe operating point with largest tested batch.
    largest = max(
        rows,
        key=lambda row: row["batch_size"],
    )

    safe_vs_largest = pct_change(
        largest["reported_tok_s"],
        last_safe["reported_tok_s"],
    )

    print()
    print(
        f"Largest tested batch: {largest['batch_size']}"
    )

    print(
        f"reported_tok_s = "
        f"{largest['reported_tok_s']:.1f}"
    )

    print(
        "Observed throughput difference between "
        "the largest tested batch and the last "
        "preemption-free batch:"
    )

    print(
        f"{largest['reported_tok_s']:.1f} -> "
        f"{last_safe['reported_tok_s']:.1f} tok/s "
        f"({safe_vs_largest:+.2f}%)"
    )

    print()
    print(
        "Data-derived operating-point recommendation: "
        f"cap this 3584-token workload at batch "
        f"{last_safe['batch_size']} to remain in the "
        "observed preemption-free regime."
    )


if __name__ == "__main__":
    main()