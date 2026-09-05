# A3-1 — Corrected Full-Corpus Comparison

## Objective

Apply the corrected methodology to the complete A1 FLORES+ evaluation corpus and compare the legacy GPT-2 tokenizer against the selected Indic-aware comparator, Sarvam-1.

## Evaluation Corpus

* Dataset: A1 FLORES+ dev evaluation corpus
* Languages: English, Hindi, Kannada, Tamil
* Sentences per language: 997
* Total sentences: 3,988
* Sentences are aligned across languages by the same FLORES+ sentence IDs.

## Corrected Methodology

* NFC normalization only.
* Original case preserved.
* Internal whitespace preserved.
* No forced lowercasing.
* Whitespace-word denominator uses `split()`.
* Grapheme denominator uses Unicode extended grapheme clusters (`\X`).
* Byte denominator uses UTF-8 byte count.
* Special tokens disabled with `add_special_tokens=False`.
* Corpus-level ratios are computed from total tokens divided by total denominator units.
* Sentence-level distributions are also retained for workload analysis.

## Command

```text
python your-submission\partA\A3_corrected_analysis\corrected_comparison.py
```

## GPT-2 Results

| Language | Total tokens | Tok/sentence |  Tok/word | Tok/grapheme | Tok/byte |
| -------- | -----------: | -----------: | --------: | -----------: | -------: |
| English  |       25,741 |    25.818455 |  1.228453 |     0.205609 | 0.205451 |
| Hindi    |      191,828 |   192.405216 |  7.795668 |     2.327897 | 0.594557 |
| Kannada  |      349,772 |   350.824473 | 22.668308 |     4.058763 | 0.978635 |
| Tamil    |      397,163 |   398.358074 | 24.616524 |     4.204251 | 0.995908 |

Relative token workload vs aligned English:

| Language |      Ratio |
| -------- | ---------: |
| Hindi    |  7.452236x |
| Kannada  | 13.588128x |
| Tamil    | 15.429199x |

## Sarvam-1 Results

| Language | Total tokens | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte |
| -------- | -----------: | -----------: | -------: | -----------: | -------: |
| English  |       29,915 |    30.005015 | 1.427651 |     0.238949 | 0.238766 |
| Hindi    |       34,206 |    34.308927 | 1.390092 |     0.415101 | 0.106019 |
| Kannada  |       37,225 |    37.337011 | 2.412508 |     0.431960 | 0.104153 |
| Tamil    |       34,539 |    34.642929 | 2.140759 |     0.365620 | 0.086608 |

Relative token workload vs aligned English:

| Language |     Ratio |
| -------- | --------: |
| Hindi    | 1.143440x |
| Kannada  | 1.244359x |
| Tamil    | 1.154571x |

## Legacy → Corrected Comparison

### GPT-2

| Language | Legacy tok/word | Corrected tok/word | Change |
| -------- | --------------: | -----------------: | -----: |
| English  |        1.282531 |           1.228453 | -4.22% |
| Hindi    |        7.823186 |           7.795668 | -0.35% |
| Kannada  |       22.148288 |          22.668308 | +2.35% |
| Tamil    |       24.733182 |          24.616524 | -0.47% |

### Sarvam-1

| Language | Legacy tok/word | Corrected tok/word | Change |
| -------- | --------------: | -----------------: | -----: |
| English  |        1.460539 |           1.427651 | -2.25% |
| Hindi    |        1.400991 |           1.390092 | -0.78% |
| Kannada  |        2.348439 |           2.412508 | +2.73% |
| Tamil    |        2.150157 |           2.140759 | -0.44% |

The original and corrected approaches therefore produce broadly consistent tokenizer ordering, although the reported normalized ratios change.

## Interpretation

The corrected full-corpus analysis confirms that GPT-2 produces substantially higher token workload for Hindi, Kannada, and Tamil than Sarvam-1 on the same aligned content.

The corrected methodology also demonstrates why `tokens/word` should not be treated as a direct serving-cost multiplier. The metric is useful as a normalization diagnostic, but actual serving workload is determined by the number of model tokens generated for the same amount of content.

The final A3 routing/cost analysis therefore prioritizes direct aligned token workload, with denominator-based metrics used to explain and validate the result.
