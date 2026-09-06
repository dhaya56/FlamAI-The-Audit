# B3 — Correcting REPORT_v0 Section 2

## Question

`REPORT_v0.md` Section 2 concludes that longer prompts give better throughput and that batch 48 will deliver approximately 3200 tok/s.

Both conclusions come from the same misreading of one column.

The task is to identify that column, derive the honest goodput of the batch-24 long-prompt row in two independent ways, and state what the report should have said.

---

## 1. Misread column

The misread column is:

```text
reported_tok_s
```

`model_spec.md` describes this as the harness's built-in throughput counter.

The benchmark log shows that this value is an aggregate token rate for the full workload, including both prompt tokens and generated tokens.

For the batch-24 long-prompt row:

```text
batch_size   = 24
prompt_len   = 3584
gen_len      = 512
wall_clock_s = 61.16
reported_tok_s = 1607.4
```

Each request contains:

```text
3584 + 512 = 4096 tokens
```

Therefore the reported throughput can be reproduced from the log as:

```text
24 × 4096 / 61.16
= 1607.33 tok/s
```

This matches the logged:

```text
1607.4 tok/s
```

So `reported_tok_s` is already the aggregate prompt-plus-generation token throughput. It must not be multiplied by batch size again.

---

## 2. Why the "longer prompts give better throughput" conclusion is unsupported

`REPORT_v0` compares batch 16:

```text
Long prompt:  1311.4 tok/s
Short prompt:  883.2 tok/s
```

However, the two workloads contain different numbers of tokens per request:

```text
Short prompt:
512 prompt + 256 generated = 768 tokens/request

Long prompt:
3584 prompt + 512 generated = 4096 tokens/request
```

Therefore the higher `reported_tok_s` value for the long-prompt workload does not, by itself, demonstrate better GPU utilization caused by longer prompts.

The complete long-prompt sweep provides the stronger evidence:

| Batch | Prompt | Gen | Reported tok/s | Preempted |
| ----: | -----: | --: | -------------: | --------: |
|     4 |   3584 | 512 |          565.4 |         0 |
|     8 |   3584 | 512 |          902.6 |         0 |
|    16 |   3584 | 512 |         1311.4 |         0 |
|    24 |   3584 | 512 |         1607.4 |         0 |
|    32 |   3584 | 512 |         1384.0 |         7 |
|    48 |   3584 | 512 |         1298.5 |        23 |

Observed trend:

```text
565.4 → 902.6 → 1311.4 → 1607.4 → 1384.0 → 1298.5 tok/s
```

Throughput increases through batch 24, reaches the highest observed value of 1607.4 tok/s, and then decreases.

Therefore the experiment does not support the statement that longer prompts inherently give better throughput or that clients should be encouraged to pack more context.

---

## 3. Honest goodput of the batch-24 long-prompt row

For this analysis, "goodput" means useful generated output tokens completed per second, rather than counting the input prompt tokens as output work.

### Method 1 — Generated tokens divided by wall-clock time

There are 24 requests and each generates exactly 512 tokens:

```text
24 × 512
= 12,288 generated tokens
```

Divide by the measured wall-clock time:

```text
12,288 / 61.16
= 200.92 generated tok/s
```

So the goodput is approximately:

```text
200.9 generated tok/s
```

### Method 2 — Request completion rate multiplied by generated tokens/request

Request completion rate:

```text
24 / 61.16
= 0.39241 requests/s
```

Each request generates:

```text
512 tokens
```

Therefore:

```text
0.39241 × 512
= 200.92 generated tok/s
```

The two independent calculations agree.

Therefore:

```text
Honest batch-24 goodput ≈ 201 generated tok/s
```

---

## 4. Why the batch-48 estimate of ~3200 tok/s is wrong

The original report says:

> "assume ~1600 tok/s per L4 (best observed) and scale linearly with batch size, so batch 48 should give us ~3200 tok/s."

The problem is that the approximately 1600 tok/s value is already an observed aggregate throughput, not a per-sequence rate.

At batch 24:

```text
reported_tok_s = 1607.4 tok/s
```

That is the throughput for the entire 24-request workload.

The actual batch-48 measurement is:

```text
reported_tok_s = 1298.5 tok/s
```

not approximately 3200 tok/s.

The batch-48 generated-output goodput is also only:

```text
48 × 512 / 151.41
= 162.31 generated tok/s
```

So the ~3200 tok/s extrapolation is not supported by the benchmark.

---

## 5. What REPORT_v0 should have said

A defensible replacement for Section 2 is:

> For the tested long-prompt workload (3584 prompt tokens and 512 generated tokens), aggregate prompt-plus-generation throughput increases from 565.4 tok/s at batch 4 to a peak of 1607.4 tok/s at batch 24, then decreases to 1384.0 tok/s at batch 32 and 1298.5 tok/s at batch 48. The higher batch-16 value for long prompts (1311.4 tok/s versus 883.2 tok/s for short prompts) does not establish that longer prompts improve GPU utilization because the two workloads contain different amounts of work per request. For the batch-24 long-prompt row, the measured output goodput is approximately 201 generated tok/s, derived independently as 24 × 512 / 61.16 and as (24 / 61.16) × 512. The batch-48 throughput should not be extrapolated from the batch-24 value; the actual batch-48 measurement is 1298.5 tok/s.

---

## Evidence used

The benchmark log provides the batch, prompt length, generation length, wall-clock time, reported throughput, and preemption values used above.

The model specification defines `reported_tok_s` as the harness's throughput counter and confirms that every request generates exactly the specified `gen_len` tokens with no early stopping.
