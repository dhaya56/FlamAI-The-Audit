# B2 — Long-Prompt Throughput Anomaly

## Question

For the `prompt_len = 3584` sweep, identify the throughput anomaly, explain the mechanism using evidence from the benchmark log, and recommend one serving/deployment change with a quantitative effect.

## Experiment

Source log:

```text
starter_kit/bench/bench_log.csv
```

Command:

```bash
python your-submission/partB/B2/b2_mechanism_analysis.py
```

The script filters the long-context sweep:

```text
prompt_len = 3584
gen_len    = 512
```

Therefore every request contains:

```text
3584 + 512 = 4096 tokens
```

The script also verifies that `reported_tok_s` is consistent with:

```text
batch_size × 4096 / wall_clock_s
```

The values match to rounding error, so `reported_tok_s` represents total prompt-plus-generation token throughput for the batch.

Example for batch 24:

```text
24 × 4096 / 61.16 = 1607.33 tok/s
reported_tok_s   = 1607.40 tok/s
```

## Observed throughput

| Batch | Wall clock (s) | Reported tok/s | KV util | Preempted seqs |
| ----: | -------------: | -------------: | ------: | -------------: |
|     4 |          28.98 |          565.4 |    0.16 |              0 |
|     8 |          36.30 |          902.6 |    0.31 |              0 |
|    16 |          49.97 |         1311.4 |    0.62 |              0 |
|    24 |          61.16 |         1607.4 |    0.93 |              0 |
|    32 |          94.71 |         1384.0 |    0.97 |              7 |
|    48 |         151.41 |         1298.5 |    0.97 |             23 |

### Throughput anomaly

Throughput increases normally from batch 4 through batch 24:

```text
565.4 → 902.6 → 1311.4 → 1607.4 tok/s
```

The first reversal occurs when batch size increases from 24 to 32:

```text
1607.4 → 1384.0 tok/s
```

Percentage change:

```text
(1384.0 - 1607.4) / 1607.4 × 100
= -13.90%
```

A second reversal occurs from batch 32 to 48:

```text
1384.0 → 1298.5 tok/s
```

Percentage change:

```text
(1298.5 - 1384.0) / 1384.0 × 100
= -6.18%
```

So increasing concurrency beyond batch 24 reduces total throughput instead of increasing it.

---

## Mechanism evidence

The strongest evidence appears at the first reversal, batch 24 to batch 32.

| Metric               |     Batch 24 |     Batch 32 |  Change |
| -------------------- | -----------: | -----------: | ------: |
| Reported throughput  | 1607.4 tok/s | 1384.0 tok/s | -13.90% |
| KV-cache utilization |         0.93 |         0.97 |  +4.30% |
| Preempted sequences  |            0 |            7 |      +7 |
| TTFT p50             |     500.5 ms |     636.9 ms | +27.25% |
| ITL p50              |     96.07 ms |    101.79 ms |  +5.95% |
| E2E p95              |  69,221.3 ms |  97,465.7 ms | +40.80% |

The important transition is:

```text
batch 24:
KV util = 0.93
preempted = 0
throughput = 1607.4 tok/s
```

to:

```text
batch 32:
KV util = 0.97
preempted = 7
throughput = 1384.0 tok/s
```

This is consistent with the system reaching a KV-cache capacity boundary. Once the operating point moves past the last preemption-free batch, preemption begins and throughput falls while latency rises.

The larger batch 48 reinforces the same interpretation:

| Metric               |     Batch 32 |     Batch 48 |  Change |
| -------------------- | -----------: | -----------: | ------: |
| Reported throughput  | 1384.0 tok/s | 1298.5 tok/s |  -6.18% |
| KV-cache utilization |         0.97 |         0.97 |   0.00% |
| Preempted sequences  |            7 |           23 |     +16 |
| TTFT p50             |     636.9 ms |     955.4 ms | +50.01% |
| ITL p50              |    101.79 ms |    100.00 ms |  -1.76% |
| E2E p95              |  97,465.7 ms | 105,427.5 ms |  +8.17% |

The log directly shows increasing preemptions and worsening latency as concurrency is pushed beyond the efficient operating region.

The log does **not** prove the exact internal scheduler implementation or whether preemption causes a specific kind of recomputation. Therefore the defensible conclusion is that KV-cache saturation and resulting preemption/capacity-management overhead explain the observed throughput reversal.

---

## Recommended configuration change

Use the largest observed preemption-free operating point as the concurrency cap:

```text
batch size / max concurrent sequences = 24
```

For a serving system exposing a parameter such as `max_num_seqs`, set:

```text
max_num_seqs = 24
```

or use equivalent admission control to prevent the workload from routinely entering the batch-32+ regime.

### Quantitative effect observed in this benchmark

Compared with batch 32:

```text
1607.4 / 1384.0 - 1 = +16.14%
```

So operating at batch 24 gives approximately:

```text
+16.14% higher observed throughput
```

than the first overloaded point.

Compared with batch 48:

```text
1607.4 / 1298.5 - 1 = +23.79%
```

So the same operating point gives approximately:

```text
+23.79% higher observed throughput
```

than the largest tested batch.

These are measured differences under this benchmark workload, not guarantees for every production workload.

---

## Final conclusion

The long-context sweep shows a clear throughput reversal after batch 24. Batch 24 is the last tested point with zero preemptions and 0.93 KV-cache utilization. Increasing to batch 32 raises utilization to 0.97, introduces 7 preempted sequences, increases TTFT by 27.25% and E2E p95 by 40.80%, while reducing throughput by 13.90%. Batch 48 causes even more preemptions and lower throughput. The evidence supports KV-cache saturation followed by preemption and capacity-management overhead as the mechanism. The recommended deployment change is to cap concurrency at 24 sequences; in this benchmark that corresponds to 16.14% higher throughput than batch 32 and 23.79% higher throughput than batch 48.
