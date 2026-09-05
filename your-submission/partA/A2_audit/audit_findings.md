# A2 — Script and Metric Audit

## Audit baseline

The supplied `fertility.py` computes per-line fertility as `len(tokens) / len(words)` and averages those per-line ratios. It also computes `tokens / len(line)` as `tok/char`. The script lowercases each line before tokenization.

The original benchmark was reproduced exactly on the supplied English/Hindi starter corpus:

```text
eng fertility = 1.27
hin fertility = 7.45
hin/eng       = 5.89x
```

The reproduced baseline matches `REPORT_v0.md`.

---

## Finding 1 — Literal-space splitting mishandles repeated whitespace

### Classification

Confirmed implementation bug.

### Claim

The expression `line.split(" ")` treats consecutive spaces as empty fields, inflating the word denominator and lowering tokens-per-word fertility. The supplied script uses this expression directly.

### Evidence

Controlled experiment:

```text
python your-submission\partA\A2_audit\experiments\exp01_whitespace.py
```

The exact starter corpus was measured using the original split and a whitespace-aware `split()` comparison.

| Language | Original | `split()` | Relative change |
| -------- | -------: | --------: | --------------: |
| English  | 1.265206 |  1.283063 |          +1.41% |
| Hindi    | 7.448452 |  7.598452 |          +2.01% |

The supplied corpus contains repeated spaces in both the English and Hindi files.

### Why the delta supports the claim

Only the whitespace splitting operation changed, while tokenizer, normalization, input text, and per-line aggregation were held constant. The fertility increase therefore measures the effect of counting empty fields created by repeated spaces.

### Impact

The bug is real but does not explain the large cross-language gap by itself. Its measured effect on the supplied corpus is 1.41% for English and 2.01% for Hindi.

---

## Finding 2 — Forced lowercasing introduces an asymmetric preprocessing effect

### Classification

Confirmed benchmark methodology issue.

### Claim

The script lowercases text immediately before tokenization. This changes the English tokenization distribution while leaving the Hindi result unchanged on the supplied corpus. The operation is intentional in the source comment, so the issue is the benchmark methodology rather than an accidental coding mistake.

### Evidence

Controlled experiment:

```text
python your-submission\partA\A2_audit\experiments\exp04_lowercase.py
```

| Language          | With `.lower()` | Without `.lower()` | Relative change |
| ----------------- | --------------: | -----------------: | --------------: |
| English fertility |        1.265206 |           1.229329 |          -2.84% |
| Hindi fertility   |        7.448452 |           7.448452 |           0.00% |

Cross-language ratio:

```text
with lowercasing    = 5.887148x
without lowercasing = 6.058958x
relative change     = +2.92%
```

### Why the delta supports the claim

Only lowercasing was toggled. The tokenizer, corpus, normalization, whitespace handling, and aggregation remained fixed. The resulting 2.92% change in the cross-language ratio demonstrates an asymmetric effect on the comparison.

### Impact

The preprocessing choice shifts the reported English/Hindi ratio by 2.92% on the supplied corpus. It should therefore not be treated as neutral preprocessing for a cross-language benchmark.

---

## Finding 3 — `tokens/word` is a conceptual problem for the routing/cost conclusion

### Classification

Confirmed conceptual problem.

### Claim

The code computes `tokens/word` exactly as defined, but using whitespace-separated words as the cross-language denominator is not a controlled measure of comparable workload. A word does not represent a constant amount of underlying content across languages.

The issue becomes important when the resulting ratio is used to infer serving cost. `REPORT_v0` states that Hindi is 5.89x worse and recommends budgeting approximately 6x serving cost.

### Evidence

Using the properly aligned A1 FLORES+ corpus, the same GPT-2 tokenizer and the same tokenizer-side preprocessing were held constant while comparing tokens per whitespace word with tokens per aligned sentence.

Controlled experiment:

```text
python your-submission\partA\A2_audit\experiments\exp07_aligned_denominators.py
```

| Language | Tokens/word | Tokens/sentence | Word-based ratio vs English | Sentence-based ratio vs English |
| -------- | ----------: | --------------: | --------------------------: | ------------------------------: |
| Hindi    |    7.823186 |      192.419258 |                   6.099802x |                       7.186170x |
| Kannada  |   22.148288 |      350.854564 |                  17.269202x |                      13.103162x |
| Tamil    |   24.733182 |      398.384152 |                  19.284665x |                      14.878221x |

A paired sentence-level consistency check was also performed:

```text
python your-submission\partA\A2_audit\experiments\exp08_paired_workload.py
```

| Language | Mean paired target/English ratio |     Median | Corpus-level ratio |
| -------- | -------------------------------: | ---------: | -----------------: |
| Hindi    |                        7.290745x |  7.153846x |          7.186170x |
| Kannada  |                       13.317866x | 13.086957x |         13.103162x |
| Tamil    |                       15.154565x | 14.944444x |         14.878221x |

### Why the delta supports the claim

The language multiplier changes materially when the denominator is changed while the aligned underlying sentence content is held constant. The paired sentence-level analysis also produces ratios close to the corpus-level aligned-content ratios, showing that the observation is not explained by a single aggregation artifact.

### Impact

The v0 5.89x word-normalized result should not be treated as a universal language-specific serving-cost multiplier. The final operational metric requires a workload denominator that is appropriate to the routing/cost question; this is addressed formally in A3.

---

## Finding 4 — `tok/char` is not an independent confirmation of `tok/word`

### Classification

Confirmed metric-interpretation problem.

### Claim

`REPORT_v0` treats `tok/char` as independent confirmation of the `tok/word` conclusion.

However, both metrics use the same token counts and differ only in their denominator. Therefore agreement in direction does not constitute independent validation.

The `tok/char` result is also highly sensitive to the definition of "character."

### Evidence

Controlled experiment:

```text
python your-submission\partA\A2_audit\experiments\exp05_char_denominator.py
```

The GPT-2 token counts were held constant while the denominator was changed.

| Denominator         |  English |    Hindi | Hindi/English |
| ------------------- | -------: | -------: | ------------: |
| Unicode code points | 0.225636 | 1.579108 |     6.998478x |
| Grapheme clusters   | 0.225636 | 2.449732 |    10.857013x |
| UTF-8 bytes         | 0.225636 | 0.598992 |     2.654683x |

### Why the delta supports the claim

Only the denominator changed. The resulting Hindi/English ratio varied from 2.65x to 10.86x without changing the underlying tokenizer output.

### Impact

The report's statement that `tok/char` "confirms" the `tok/word` result is not robust. The metric is denominator-dependent and should be treated as a separate diagnostic, not independent confirmation.

---

## Finding 5 — Per-line macro averaging was investigated but was not material

### Classification

Tested alternative; not treated as a principal flaw.

### Hypothesis

The per-line mean of token/word ratios might materially differ from the corpus-level token total divided by word total.

### Evidence

```text
python your-submission\partA\A2_audit\experiments\exp02_aggregation.py
```

| Language | Per-line average | Corpus-level ratio | Relative change |
| -------- | ---------------: | -----------------: | --------------: |
| English  |         1.265206 |           1.253165 |          -0.95% |
| Hindi    |         7.448452 |           7.403226 |          -0.61% |

Cross-language ratio:

```text
per-line method = 5.887148x
corpus-level    = 5.907625x
relative change = +0.35%
```

### Interpretation

The aggregation method changes the individual fertility estimates slightly, but the English/Hindi conclusion changes by only 0.35% on the supplied corpus. It is therefore not treated as a material explanation for the v0 finding.

---

## Finding 6 — NFC normalization was investigated and found harmless for this benchmark

### Classification

Suspicious-looking but not a demonstrated problem.

### Evidence

```text
python your-submission\partA\A2_audit\experiments\exp06_nfc.py
```

| Measurement | English change | Hindi change |
| ----------- | -------------: | -----------: |
| Fertility   |          0.00% |        0.00% |
| `tok/char`  |          0.00% |        0.00% |

Cross-language ratio:

```text
NFC = 5.887148x
Raw = 5.887148x
Change = 0.00%
```

### Interpretation

NFC normalization produced no measurable change on the supplied starter corpus with GPT-2. It should therefore not be reported as a benchmark bug from this evidence.

---

## Finding 7 — Unused random seed is suspicious-looking but harmless

### Classification

Suspicious-looking but actually fine.

### Evidence

```text
python your-submission\partA\A2_audit\experiments\exp09_random_seed.py
```

The original script containing `random.seed(1337)` and a temporary copy with that line removed produced identical benchmark output:

```text
with seed:
eng = 1.27
hin = 7.45
ratio = 5.89x

without seed:
eng = 1.27
hin = 7.45
ratio = 5.89x

outputs_identical: True
```

The source contains the import and seed, but no subsequent random operation is used by the benchmark.

### Interpretation

The seed is unnecessary for this deterministic computation, but it does not alter the results. It is therefore a suspicious-looking but harmless piece of setup rather than a numerical bug.

---

## Overall A2 conclusion

The audit identified two measurable implementation/preprocessing problems, one central conceptual metric problem, and one metric-interpretation problem:

1. Literal-space splitting mishandles repeated whitespace.
2. Forced lowercasing introduces an asymmetric preprocessing effect.
3. `tokens/word` is not a sufficient cross-language workload denominator for a routing/cost decision.
4. `tok/char` does not independently validate `tok/word` and is highly denominator-dependent.

The audit also tested two plausible alternatives that were not material on the supplied benchmark:

* macro versus micro aggregation;
* NFC versus raw Unicode normalization.

Finally, the apparently unnecessary `random.seed(1337)` was experimentally shown to be harmless.

The corrected multilingual tokenizer analysis and final routing/cost metric are deferred to A3, using the fixed A1 evaluation corpus and at least two tokenizers.
