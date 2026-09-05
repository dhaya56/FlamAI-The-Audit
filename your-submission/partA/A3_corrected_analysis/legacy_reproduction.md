# A3-0 — Legacy Method Reproduction

## Objective

Reproduce the original tokenizer-fertility methodology from the starter `fertility.py` on the complete A1 FLORES+ evaluation corpus.

This establishes the full-corpus baseline before applying the methodological corrections identified during A2.

## Evaluation Corpus

* Dataset: A1 FLORES+ dev evaluation corpus
* Languages: English, Hindi, Kannada, Tamil
* Sentences per language: 997
* Total evaluated sentences: 3,988
* Language files are aligned by the same FLORES+ sentence IDs.

## Legacy Methodology

The implementation intentionally follows the starter methodology:

* NFC normalization
* forced lowercasing
* word denominator: `line.split(" ")`
* character denominator: `len(line)`
* arithmetic mean of per-line ratios
* tokenizer special tokens disabled with `add_special_tokens=False`

This experiment is a reproduction baseline, not the corrected A3 methodology.

## Command

```text
python your-submission\partA\A3_corrected_analysis\legacy_reproduction.py
```

## Results

### GPT-2

Repository: `gpt2`

| Language | Fertility (tok/word) | Tok/char | Relative fertility vs English |
| -------- | -------------------: | -------: | ----------------------------: |
| English  |             1.282531 | 0.215159 |                     1.000000x |
| Hindi    |             7.823186 | 1.527631 |                     6.099802x |
| Kannada  |            22.148288 | 2.655457 |                    17.269202x |
| Tamil    |            24.733182 | 2.717075 |                    19.284665x |

### Sarvam-1

Repository: `sarvamai/sarvam-1`

| Language | Fertility (tok/word) | Tok/char | Relative fertility vs English |
| -------- | -------------------: | -------: | ----------------------------: |
| English  |             1.460539 | 0.244603 |                     1.000000x |
| Hindi    |             1.400991 | 0.274663 |                     0.959229x |
| Kannada  |             2.348439 | 0.284156 |                     1.607927x |
| Tamil    |             2.150157 | 0.237732 |                     1.472167x |

## Initial Observation

Under the legacy methodology, GPT-2 shows substantially higher Indic token workload than English:

* Hindi: 6.099802x English fertility
* Kannada: 17.269202x
* Tamil: 19.284665x

Sarvam-1 shows much lower Indic fertility relative to GPT-2.

The GPT-2 full-corpus results are consistent with the earlier A2 investigation and establish the legacy baseline on the complete aligned A1 corpus.

## Important Interpretation Limitation

The legacy fertility number should not be interpreted directly as a language-neutral serving-cost multiplier.

The denominator is whitespace-separated words, and the methodology also forces lowercasing and uses a literal `split(" ")`. A2 experiments showed that these choices can affect the reported metric.

Therefore, this experiment establishes the **before-state** only.

## Next Step

Run the corrected A3 methodology on the same full aligned corpus and compare the results against this legacy baseline.

The corrected analysis will:

* remove forced lowercasing;
* use `split()` for the whitespace-word denominator;
* retain sentence alignment;
* measure tokens per word, grapheme, and UTF-8 byte;
* report direct token workload;
* compare GPT-2 against the selected Indic-aware tokenizer, Sarvam-1.
