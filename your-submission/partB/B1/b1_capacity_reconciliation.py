from __future__ import annotations

import csv
from pathlib import Path


# File:
# repo\your-submission\partB\B1\b1_capacity_reconciliation.py
#
# parents[3] = repository root
ROOT = Path(__file__).resolve().parents[3]

MODEL_SPEC = ROOT / "starter_kit" / "bench" / "model_spec.md"
BENCH_LOG = ROOT / "starter_kit" / "bench" / "bench_log.csv"


# ---------------------------------------------------------------------
# Values taken directly from model_spec.md
#
# IMPORTANT UNIT CONVENTION
# The supplied specification states GPU memory and overhead in "GB".
# We therefore treat those stated values as decimal GB:
#     1 GB = 10^9 bytes
#
# Binary conversions (KiB/MiB) are used only for readable display.
# ---------------------------------------------------------------------

PARAMETERS = 4.2e9
FP16_BYTES = 2

LAYERS = 28
KV_HEADS = 8
HEAD_DIM = 128

GPU_MEMORY_GB = 24.0
GPU_MEMORY_UTILIZATION = 0.92
NON_KV_OVERHEAD_GB = 1.6

MAX_MODEL_LEN = 4096

DECIMAL_BYTES_PER_GB = 10**9


# ---------------------------------------------------------------------
# Stage 1: prediction from model specification alone
# ---------------------------------------------------------------------

def kv_bytes_per_token() -> int:
    """
    KV cache stores both K and V for every transformer layer.

    Formula:
        bytes/token =
        2(K,V) × layers × KV heads × head_dim × bytes/element
    """
    return (
        2
        * LAYERS
        * KV_HEADS
        * HEAD_DIM
        * FP16_BYTES
    )


def model_weight_bytes() -> int:
    """Approximate fp16 model-weight memory."""
    return int(PARAMETERS * FP16_BYTES)


def first_pass_capacity() -> float:
    """
    Initial hypothesis before checking the benchmark log.

    This intentionally does NOT reserve model weights.
    """
    configured_bytes = (
        GPU_MEMORY_GB
        * DECIMAL_BYTES_PER_GB
        * GPU_MEMORY_UTILIZATION
    )

    non_kv_bytes = (
        NON_KV_OVERHEAD_GB
        * DECIMAL_BYTES_PER_GB
    )

    kv_budget_bytes = configured_bytes - non_kv_bytes

    sequence_bytes = (
        kv_bytes_per_token()
        * MAX_MODEL_LEN
    )

    return kv_budget_bytes / sequence_bytes


def corrected_capacity() -> float:
    """
    Reconciled calculation after reserving model weights.
    """
    configured_bytes = (
        GPU_MEMORY_GB
        * DECIMAL_BYTES_PER_GB
        * GPU_MEMORY_UTILIZATION
    )

    weights_bytes = model_weight_bytes()

    non_kv_bytes = (
        NON_KV_OVERHEAD_GB
        * DECIMAL_BYTES_PER_GB
    )

    kv_budget_bytes = (
        configured_bytes
        - weights_bytes
        - non_kv_bytes
    )

    sequence_bytes = (
        kv_bytes_per_token()
        * MAX_MODEL_LEN
    )

    return kv_budget_bytes / sequence_bytes


# ---------------------------------------------------------------------
# Stage 2: benchmark-log check
# ---------------------------------------------------------------------

def check_log():
    """
    Select rows where prompt_len + gen_len = 4096.

    These are the rows relevant to the 4096-token capacity question.
    """
    rows = []

    with BENCH_LOG.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            prompt_len = int(row["prompt_len"])
            gen_len = int(row["gen_len"])

            if prompt_len + gen_len == MAX_MODEL_LEN:
                batch_size = int(row["batch_size"])
                preempted = int(row["preempted_seqs"])

                rows.append(
                    {
                        "batch_size": batch_size,
                        "prompt_len": prompt_len,
                        "gen_len": gen_len,
                        "preempted": preempted,
                        "resident_estimate": (
                            batch_size - preempted
                        ),
                        "kv_cache_util": float(
                            row["kv_cache_util"]
                        ),
                    }
                )

    return rows


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("B1 Capacity Reconciliation")
    print()
    print(f"Model spec : {MODEL_SPEC}")
    print(f"Benchmark  : {BENCH_LOG}")
    print()
    print(
        "Unit convention: supplied GB values are treated as "
        "decimal GB (1 GB = 10^9 bytes)."
    )
    print()

    # ================================================================
    # Stage 1 — Prediction from model spec alone
    # ================================================================

    print("=" * 80)
    print("STAGE 1 — PREDICTION FROM MODEL SPEC ALONE")
    print("=" * 80)

    kv_bpt = kv_bytes_per_token()

    print()
    print("1. KV-cache bytes per token")
    print("----------------------------")
    print(
        "Formula = 2(K,V) × layers × KV heads × "
        "head_dim × bytes per fp16 element"
    )
    print(
        f"       = 2 × {LAYERS} × {KV_HEADS} × "
        f"{HEAD_DIM} × {FP16_BYTES}"
    )
    print(f"       = {kv_bpt:,} bytes/token")

    print()
    print("Convert bytes/token to KiB/token:")
    print(
        f"{kv_bpt:,} ÷ 1024 "
        f"= {kv_bpt / 1024:.0f} KiB/token"
    )
    print(
        "Why ÷1024 once: 1 KiB = 1024 bytes."
    )

    sequence_bytes = kv_bpt * MAX_MODEL_LEN

    print()
    print("2. KV memory for one 4096-token sequence")
    print("-----------------------------------------")
    print(
        f"{kv_bpt:,} bytes/token × {MAX_MODEL_LEN} tokens"
    )
    print(f"= {sequence_bytes:,} bytes")

    print(
        f"= {sequence_bytes / (1024 ** 2):.0f} MiB"
    )
    print(
        "Why ÷1024²: 1 MiB = 1024² bytes."
    )

    configured_bytes = (
        GPU_MEMORY_GB
        * DECIMAL_BYTES_PER_GB
        * GPU_MEMORY_UTILIZATION
    )

    configured_gb = (
        GPU_MEMORY_GB * GPU_MEMORY_UTILIZATION
    )

    print()
    print("3. Configured GPU memory budget")
    print("--------------------------------")
    print(
        f"{GPU_MEMORY_GB:.2f} GB × "
        f"{GPU_MEMORY_UTILIZATION:.2f}"
    )
    print(f"= {configured_gb:.2f} GB")
    print(
        f"= {configured_bytes:,.0f} bytes"
    )
    print(
        "Why: 92% of the stated 24 GB GPU memory is "
        "available to the serving process."
    )

    non_kv_bytes = (
        NON_KV_OVERHEAD_GB
        * DECIMAL_BYTES_PER_GB
    )

    initial_memory_bytes = (
        configured_bytes - non_kv_bytes
    )

    initial_memory_gb = (
        initial_memory_bytes / DECIMAL_BYTES_PER_GB
    )

    print()
    print("4. Initial capacity hypothesis")
    print("-------------------------------")
    print(
        f"{configured_gb:.2f} GB - "
        f"{NON_KV_OVERHEAD_GB:.2f} GB"
    )
    print(
        f"= {initial_memory_gb:.2f} GB"
    )

    first_capacity = first_pass_capacity()

    print()
    print(
        f"{initial_memory_bytes:,.0f} bytes ÷ "
        f"{sequence_bytes:,} bytes/sequence"
    )
    print(
        f"= {first_capacity:.3f} sequences"
    )
    print(
        f"≈ {int(first_capacity)} whole 4096-token sequences"
    )
    print(
        "This is the initial hypothesis; model weights "
        "have not yet been reserved."
    )

    # ================================================================
    # Stage 2 — Check against benchmark log
    # ================================================================

    print()
    print("=" * 80)
    print("STAGE 2 — CHECK AGAINST BENCHMARK LOG")
    print("=" * 80)

    rows = check_log()

    print()
    print(
        "Selected rows satisfy prompt_len + gen_len = 4096."
    )
    print(
        "Therefore they represent the 4096-token capacity-stress case."
    )
    print()

    for row in rows:
        print(
            f"batch={row['batch_size']} | "
            f"prompt={row['prompt_len']} | "
            f"gen={row['gen_len']} | "
            f"preempted={row['preempted']} | "
            f"resident≈{row['resident_estimate']} | "
            f"kv_util={row['kv_cache_util']:.2f}"
        )

    # ================================================================
    # Stage 3 — Reconciled calculation
    # ================================================================

    print()
    print("=" * 80)
    print("STAGE 3 — RECONCILED CALCULATION")
    print("=" * 80)

    weights_bytes = model_weight_bytes()
    weights_gb = (
        weights_bytes / DECIMAL_BYTES_PER_GB
    )

    kv_budget_bytes = (
        configured_bytes
        - weights_bytes
        - non_kv_bytes
    )

    kv_budget_gb = (
        kv_budget_bytes / DECIMAL_BYTES_PER_GB
    )

    corrected = corrected_capacity()

    print()
    print("1. Model-weight memory")
    print("-----------------------")
    print(
        f"{PARAMETERS / 1e9:.1f}B parameters × "
        f"{FP16_BYTES} bytes/parameter"
    )
    print(
        f"= {weights_bytes:,} bytes"
    )
    print(
        f"= {weights_gb:.2f} GB"
    )
    print(
        "Why: fp16 stores each model parameter using 2 bytes."
    )

    print()
    print("2. Correct KV-cache memory budget")
    print("----------------------------------")
    print(
        f"Configured GPU budget = {configured_gb:.2f} GB"
    )
    print(
        f"                     = {configured_bytes:,.0f} bytes"
    )
    print(
        f"Model weights         = {weights_gb:.2f} GB"
    )
    print(
        f"Non-KV overhead       = {NON_KV_OVERHEAD_GB:.2f} GB"
    )
    print()
    print(
        f"{configured_gb:.2f} - "
        f"{weights_gb:.2f} - "
        f"{NON_KV_OVERHEAD_GB:.2f}"
    )
    print(
        f"= {kv_budget_gb:.2f} GB"
    )
    print(
        f"= {kv_budget_bytes:,.0f} bytes"
    )
    print(
        "Why: model weights and stated non-KV runtime "
        "overhead consume GPU memory before KV cache."
    )

    print()
    print("3. Corrected 4096-token sequence capacity")
    print("-------------------------------------------")
    print(
        f"{kv_budget_bytes:,.0f} bytes ÷ "
        f"{sequence_bytes:,} bytes/sequence"
    )
    print(
        f"= {corrected:.3f} sequences"
    )
    print(
        f"≈ {int(corrected)} whole 4096-token sequences"
    )
    print(
        "Why: only complete sequences can be resident, "
        "so the fractional result is converted to a whole-sequence capacity."
    )

    print()
    print("4. Log reconciliation")
    print("----------------------")

    for row in rows:
        print(
            f"batch {row['batch_size']} - "
            f"preempted {row['preempted']} "
            f"= {row['resident_estimate']} resident sequences"
        )

    if rows:
        values = sorted(
            set(row["resident_estimate"] for row in rows)
        )
        print()
        print(
            f"Observed resident-sequence estimates: {values}"
        )


if __name__ == "__main__":
    main()