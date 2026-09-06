# B1 — KV-Cache Capacity Reconciliation

## Question

**From the model specification alone**, compute:

1. KV-cache bytes per token exactly.
2. Approximate maximum number of concurrent 4096-token sequences.

**Then** check that prediction against the benchmark log.

The analysis therefore separates the initial model-spec prediction from the later log check and reconciliation.

### Unit convention

The model specification states GPU memory and non-KV overhead in **GB**. This analysis treats those supplied values as decimal GB:

`1 GB = 10^9 bytes`

Binary units are used only for readable KV-footprint conversions:

`1 KiB = 1024 bytes`

`1 MiB = 1024^2 bytes`

The capacity calculation itself is performed in bytes to avoid mixing decimal GB with binary GiB.

---

## Stage 1 — Prediction from Model Spec Alone

### 1. KV-cache bytes per token

The KV cache stores both **K (key)** and **V (value)** for every transformer layer.

Formula:

`KV bytes/token = 2 (K,V) × layers × KV heads × head_dim × bytes per fp16 element`

From the model specification:

* `layers = 28`
* `KV heads = 8`
* `head_dim = 128`
* `fp16 = 2 bytes/element`

Substitute:

`2 × 28 × 8 × 128 × 2`

`= 114,688 bytes/token`

Convert bytes to KiB:

`114,688 ÷ 1024 = 112 KiB/token`

**Why divide by 1024 once?**
Because `1 KiB = 1024 bytes`, so one division converts bytes to KiB.

### 2. KV memory for one 4096-token sequence

A full sequence contains 4096 tokens:

`114,688 bytes/token × 4096 tokens`

`= 469,762,048 bytes`

Convert directly to MiB:

`469,762,048 ÷ 1024^2 = 448 MiB`

**Why divide by 1024^2?**
Because `1 MiB = 1024^2 bytes`.

### 3. Configured GPU memory budget

The GPU has 24 GB and the serving configuration uses 92%:

`24 GB × 0.92 = 22.08 GB`

Using the stated decimal-GB convention:

`22.08 × 10^9 = 22,080,000,000 bytes`

**Why?**
The specification gives the GPU memory as 24 GB, so the calculation keeps that stated unit convention rather than silently reinterpreting it as GiB.

### 4. Initial capacity hypothesis

Subtract the stated 1.6 GB non-KV runtime overhead:

`22.08 - 1.6 = 20.48 GB`

In bytes:

`20.48 × 10^9 = 20,480,000,000 bytes`

Using the 469,762,048-byte KV footprint per 4096-token sequence:

`20,480,000,000 ÷ 469,762,048 = 43.597...`

Therefore the **initial model-spec-only hypothesis** is:

`≈ 43.60 sequences`

or approximately 43 complete 4096-token sequences.

**Important:** this is the initial hypothesis before checking the benchmark log and before reserving model-weight memory.

---

## Stage 2 — Check Against Benchmark Log

The relevant long-context rows use:

* `prompt_len = 3584`
* `gen_len = 512`

Therefore:

`3584 + 512 = 4096`

So these are the correct capacity-stress rows for the 4096-token maximum.

Relevant observations from `bench_log.csv`:

| Batch | Prompt | Gen | `preempted_seqs` | `kv_cache_util` |
| ----: | -----: | --: | ---------------: | --------------: |
|     4 |   3584 | 512 |                0 |            0.16 |
|     8 |   3584 | 512 |                0 |            0.31 |
|    16 |   3584 | 512 |                0 |            0.62 |
|    24 |   3584 | 512 |                0 |            0.93 |
|    32 |   3584 | 512 |                7 |            0.97 |
|    48 |   3584 | 512 |               23 |            0.97 |

The initial ~43.60-sequence prediction does not match the observed capacity behavior: the batch-32 and batch-48 runs are already at approximately 0.97 KV utilization and show preemptions.

For the batch-32 row:

`32 - 7 = 25`

For the batch-48 row:

`48 - 23 = 25`

Here, `batch_size - preempted_seqs` gives an **inferred resident-sequence count**: the number of submitted sequences remaining without having been preempted.

The two capacity-stress rows independently give the same estimate:

`25 resident sequences`

The utilization values provide an additional consistency check. At 24 resident sequences, utilization is 0.93. Scaling that observed utilization proportionally to 25 sequences:

`0.93 × (25 / 24) = 0.969 ≈ 0.97`

This matches the reported 0.97 utilization in the batch-32 and batch-48 rows.

---

## Stage 3 — Reconciled Calculation

The initial calculation allocated too much memory to KV cache because it did not reserve the model's own weight memory.

### 1. Model-weight memory

The specification gives 4.2 billion parameters at fp16.

`4.2 × 10^9 parameters × 2 bytes/parameter`

`= 8.4 × 10^9 bytes`

`= 8.4 GB`

**Why?**
fp16 stores each model parameter using 2 bytes.

### 2. Correct KV-cache budget

Configured GPU budget:

`24 × 0.92 = 22.08 GB`

Reserve model weights:

`22.08 - 8.4 = 13.68 GB`

Reserve the stated non-KV runtime overhead:

`13.68 - 1.6 = 12.08 GB`

In bytes:

`12.08 × 10^9 = 12,080,000,000 bytes`

**Why?**
Model weights and the specified non-KV runtime allocations consume GPU memory before KV cache can use the remainder.

### 3. Corrected 4096-token sequence capacity

One complete 4096-token sequence requires:

`469,762,048 bytes`

Therefore:

`12,080,000,000 ÷ 469,762,048 = 25.715...`

Thus:

`≈ 25 concurrent 4096-token sequences`

We report 25 whole sequences because a fractional sequence cannot be resident.

### 4. Reconciliation with the log

The corrected model-spec prediction is:

`≈ 25 sequences`

The benchmark log independently gives:

`32 - 7 = 25`

and:

`48 - 23 = 25`

The utilization pattern is also consistent:

`0.93 × (25 / 24) = 0.969 ≈ 0.97`

Therefore the model-spec calculation and benchmark behavior reconcile at approximately:

`25 concurrent 4096-token sequences`

---

## Conclusion

**Prediction from model spec alone:**

KV-cache footprint = **114,688 bytes/token**, or **112 KiB/token**.

One 4096-token sequence requires **469,762,048 bytes (448 MiB)**.

The initial capacity hypothesis was **~43.60 sequences** before reserving model weights.

**Check against log:**

The capacity-stress rows give:

`32 - 7 = 25`

`48 - 23 = 25`

Both rows report `kv_cache_util = 0.97`.

**Reconciled answer:**

After reserving **8.4 GB** for fp16 model weights and **1.6 GB** for non-KV runtime overhead, the KV budget is **12.08 GB**.

`12,080,000,000 ÷ 469,762,048 = 25.715...`

Therefore:

**≈ 25 concurrent 4096-token sequences**

The model-spec prediction and benchmark log reconcile at approximately **25 sequences**.
