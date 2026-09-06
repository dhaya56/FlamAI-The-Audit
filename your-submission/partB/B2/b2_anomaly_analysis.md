# B2 — Long-Context Throughput Anomaly

## Question

The `prompt_len = 3584` sweep contains a throughput anomaly relative to the naive expectation that increasing batch size should continue increasing throughput.

The task is to identify the anomaly, explain the mechanism using specific rows and columns, and propose one configuration or deployment change with a quantitative predicted effect.

---

## Experiment

Command:

```text
python your-submission\partB\B2\b2_mechanism_analysis.py
```

The analysis filters the benchmark log to `prompt_len = 3584`, automatically detects throughput reversals, and compares the first reversal with the preceding and following rows.

For these rows:

$$
3584+512=\boxed{4096\text{ tokens/request}}
$$

---

## 1. Identify the Throughput Anomaly

The measured `reported_tok_s` values are:

| Batch | `reported_tok_s` |
| ----: | ---------------: |
|     4 |            565.4 |
|     8 |            902.6 |
|    16 |           1311.4 |
|    24 |           1607.4 |
|    32 |           1384.0 |
|    48 |           1298.5 |

Throughput increases through batch 24, then reverses.

First reversal:

$$
1607.4\rightarrow1384.0\text{ tok/s}
$$

Percentage change:

$$
\frac{1384.0-1607.4}{1607.4}\times100
=
\boxed{-13.90\%}
$$

A second reversal occurs from batch 32 to 48:

$$
1384.0\rightarrow1298.5\text{ tok/s}
=
\boxed{-6.18\%}
$$

Therefore the anomaly is that increasing batch size beyond 24 **reduces** the measured `reported_tok_s` instead of increasing it.

---

## 2. What Does `reported_tok_s` Measure?

The log can be checked independently using:

$$
\text{derived rate}
=
\frac{\text{batch size}\times(\text{prompt length}+\text{generation length})}
{\text{wall-clock time}}
$$

For example, for batch 24:

$$
\frac{24\times(3584+512)}{61.16}
=
1607.33\text{ tok/s}
$$

while the log reports:

$$
1607.4\text{ tok/s}
$$

The same close agreement occurs for every row in the sweep.

Therefore, in this benchmark:

> `reported_tok_s` is effectively measuring **prompt + generated tokens processed per wall-clock second**.

It should not be interpreted as generated-token-only goodput.

---

## 3. Mechanism Evidence

The first throughput reversal occurs between batch 24 and batch 32.

### Batch 24 — last preemption-free point

* `reported_tok_s` = **1607.4**
* `kv_cache_util` = **0.93**
* `preempted_seqs` = **0**
* `ttft_ms_p50` = **500.5 ms**
* `itl_ms_p50` = **96.07 ms**
* `e2e_ms_p95` = **69,221.3 ms**

### Batch 32 — first reversal

* `reported_tok_s` = **1384.0**
* `kv_cache_util` = **0.97**
* `preempted_seqs` = **7**
* `ttft_ms_p50` = **636.9 ms**
* `itl_ms_p50` = **101.79 ms**
* `e2e_ms_p95` = **97,465.7 ms**

Changes from batch 24 to batch 32:

$$
\text{reported\_tok\_s}:1607.4\rightarrow1384.0
$$

$$
\boxed{-13.90\%}
$$

$$
\text{kv\_cache\_util}:0.93\rightarrow0.97
$$

$$
\boxed{+4.30\%\text{ relative}}
$$

$$
\text{preempted\_seqs}:0\rightarrow7
$$

$$
\boxed{+7\text{ sequences}}
$$

The percentage change for preemptions is undefined because the baseline is zero.

Latency also worsens:

$$
500.5\rightarrow636.9\text{ ms}
=
\boxed{+27.25\%\text{ TTFT}}
$$

and:

$$
69,221.3\rightarrow97,465.7\text{ ms}
=
\boxed{+40.80\%\text{ p95 E2E}}
$$

The next row shows that the deterioration continues after preemption begins:

| Metric           |    Batch 32 |     Batch 48 |      Change |
| ---------------- | ----------: | -----------: | ----------: |
| `reported_tok_s` |      1384.0 |       1298.5 |  **−6.18%** |
| `kv_cache_util`  |        0.97 |         0.97 |       0.00% |
| `preempted_seqs` |           7 |           23 |     **+16** |
| `ttft_ms_p50`    |    636.9 ms |     955.4 ms | **+50.01%** |
| `e2e_ms_p95`     | 97,465.7 ms | 105,427.5 ms |  **+8.17%** |

### Mechanism

The evidence indicates that the throughput reversal begins when the workload reaches the KV-cache capacity boundary:

> **At batch 24, the workload remains preemption-free at 0.93 KV utilization. Increasing to batch 32 raises utilization to 0.97 and introduces 7 preempted sequences, while measured throughput falls and latency rises. Further increasing to batch 48 increases preemptions to 23 while throughput falls again.**

Therefore, the observed mechanism is **KV-cache saturation followed by scheduler preemption and associated scheduling/capacity-management overhead**, which prevents further useful throughput scaling.

This conclusion is based on the coincident changes in `kv_cache_util`, `preempted_seqs`, throughput, and latency. The log does not expose the scheduler's internal implementation, so no stronger claim about the exact internal preemption/recomputation process is made.

---

## 4. Configuration / Deployment Change

### Recommendation

Set the maximum concurrent sequences for this 3584-token prompt workload to the **largest observed preemption-free operating point: batch 24**.

Operationally, this can be implemented as:

* `max_num_seqs = 24`, or
* equivalent admission control that queues requests above 24 rather than admitting them into a preempting batch.

### Quantitative Prediction

The measured preemption-free operating point is:

$$
\boxed{1607.4\text{ reported tok/s at batch 24}}
$$

Relative to the first reversal row:

$$
\frac{1607.4-1384.0}{1384.0}\times100
=
\boxed{+16.14\%}
$$

Relative to the largest tested batch:

$$
\frac{1607.4-1298.5}{1298.5}\times100
=
\boxed{+23.79\%}
$$

Therefore, under the same 3584+512-token workload, keeping operation at the observed preemption-free batch-24 point is predicted to restore measured processed-token throughput by approximately **16.14% versus batch 32** or **23.79% versus batch 48**.

These are **data-derived predictions from the observed benchmark operating points**, not guarantees of the same improvement under different production workloads.

### Trade-off

The cap reduces maximum admitted concurrency. Requests beyond the cap must wait or be queued instead of causing KV-cache pressure and preemption.

The goal is therefore not maximum batch size; it is maximum **useful, preemption-free throughput**.

---

## Conclusion

The long-context sweep shows a clear throughput reversal at batch 24 → 32:

$$
1607.4\rightarrow1384.0
=
\boxed{-13.90\%}
$$

The reversal coincides with:

* KV utilization increasing from **0.93 to 0.97**
* preemptions appearing (**0 → 7**)
* TTFT increasing **27.25%**
* p95 E2E latency increasing **40.80%**

At batch 48, preemptions rise further to **23** and throughput falls again to **1298.5 tok/s**.

The evidence supports **KV-cache saturation and scheduler preemption** as the mechanism preventing further batch scaling.

The recommended operating point is therefore **batch 24 / `max_num_seqs=24` for this workload**, with an observed throughput advantage of **16.14% versus batch 32** and **23.79% versus batch 48**.
