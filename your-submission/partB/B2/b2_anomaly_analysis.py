from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

BENCH_LOG = (
    ROOT
    / "starter_kit"
    / "bench"
    / "bench_log.csv"
)


def load_long_context_rows():
    rows = []

    with BENCH_LOG.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            if int(row["prompt_len"]) == 3584:
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

    return rows


def main():
    rows = load_long_context_rows()

    print("B2 — Long-context throughput anomaly")
    print()
    print("Filter: prompt_len = 3584")
    print()

    print(
        f"{'Batch':>7}"
        f"{'Wall(s)':>10}"
        f"{'Reported tok/s':>17}"
        f"{'TTFT p50':>12}"
        f"{'ITL p50':>12}"
        f"{'E2E p95':>12}"
        f"{'Preempted':>12}"
        f"{'KV util':>10}"
    )
    print("-" * 95)

    for row in rows:
        print(
            f"{row['batch_size']:7d}"
            f"{row['wall_clock_s']:10.2f}"
            f"{row['reported_tok_s']:17.1f}"
            f"{row['ttft_ms_p50']:12.1f}"
            f"{row['itl_ms_p50']:12.2f}"
            f"{row['e2e_ms_p95']:12.1f}"
            f"{row['preempted_seqs']:12d}"
            f"{row['kv_cache_util']:10.2f}"
        )

    print()
    print("Adjacent throughput changes")
    print()

    for previous, current in zip(rows, rows[1:]):
        old = previous["reported_tok_s"]
        new = current["reported_tok_s"]

        delta = new - old
        pct = (delta / old) * 100

        print(
            f"batch {previous['batch_size']} -> "
            f"{current['batch_size']}: "
            f"{old:.1f} -> {new:.1f} tok/s "
            f"({delta:+.1f}, {pct:+.2f}%)"
        )

    print()
    print("Capacity/preemption changes")
    print()

    for row in rows:
        print(
            f"batch {row['batch_size']}: "
            f"kv_util={row['kv_cache_util']:.2f}, "
            f"preempted={row['preempted_seqs']}"
        )

    print()
    print("Detected throughput reversals")
    print()

    reversals = []

    for previous, current in zip(rows, rows[1:]):
        old = previous["reported_tok_s"]
        new = current["reported_tok_s"]

        if current["batch_size"] > previous["batch_size"] and new < old:
            delta = new - old
            pct = (delta / old) * 100

            reversals.append(
                {
                    "from_batch": previous["batch_size"],
                    "to_batch": current["batch_size"],
                    "old_tok_s": old,
                    "new_tok_s": new,
                    "delta_tok_s": delta,
                    "delta_pct": pct,
                }
            )

    if not reversals:
        print("No throughput reversals detected.")
    else:
        for reversal in reversals:
            print(
                f"batch {reversal['from_batch']} -> "
                f"{reversal['to_batch']}: "
                f"{reversal['old_tok_s']:.1f} -> "
                f"{reversal['new_tok_s']:.1f} tok/s "
                f"({reversal['delta_tok_s']:+.1f}, "
                f"{reversal['delta_pct']:+.2f}%)"
            )


if __name__ == "__main__":
    main()
