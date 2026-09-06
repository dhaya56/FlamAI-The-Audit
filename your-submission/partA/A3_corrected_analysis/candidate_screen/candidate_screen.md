# A3 Candidate Screening Log

## Purpose

Before the final A3 tokenizer comparison, a candidate screening step was performed to identify reproducible multilingual/Indic-aware tokenizer candidates for evaluation on the A1 FLORES+ corpus.

GPT-2 is retained as the legacy baseline because it is the tokenizer used by the starter audit. The remaining candidates were selected to provide coverage across Indic-focused, multilingual generative, and broad multilingual tokenizer families.

## Screening Environment

* Python: 3.13.5
* Transformers: 5.16.1
* SentencePiece: installed
* Hugging Face authentication: configured locally
* Evaluation languages: English, Hindi, Kannada, Tamil
* Initial test: one fixed sanity-check sentence per language
* Encoding: `add_special_tokens=False`
* Access test performed locally through `AutoTokenizer.from_pretrained(...)`

## Candidate Results

| Candidate      | Repository                          | Result | Vocab size | English | Hindi | Kannada | Tamil |
| -------------- | ----------------------------------- | -----: | ---------: | ------: | ----: | ------: | ----: |
| GPT-2          | `gpt2`                              |   PASS |     50,257 |      10 |    66 |     144 |   152 |
| IndicBERTv2-SS | `ai4bharat/IndicBERTv2-SS`          |   PASS |    200,000 |      10 |     9 |      39 |    50 |
| IndicTrans2    | `ai4bharat/indictrans2-en-indic-1B` |   FAIL |          — |       — |     — |       — |     — |
| Sarvam-1       | `sarvamai/sarvam-1`                 |   PASS |     68,096 |      10 |     9 |       9 |     9 |
| Qwen2.5-7B     | `Qwen/Qwen2.5-7B`                   |   PASS |    151,665 |      10 |    38 |      72 |    59 |
| Gemma-2-9B     | `google/gemma-2-9b`                 |   FAIL |          — |       — |     — |       — |     — |
| XLM-R          | `FacebookAI/xlm-roberta-base`       |   PASS |    250,002 |      11 |    10 |      10 |    11 |

## Reproducibility / Exclusion Notes

### IndicTrans2

The first loading attempt required `trust_remote_code=True`. A controlled retry with `trust_remote_code=True` progressed further but failed under the current environment with:

`ModuleNotFoundError: No module named 'transformers.onnx'`

This is recorded as an environment/tooling compatibility limitation, not as evidence that the tokenizer is inferior.

IndicTrans2 is therefore excluded from the current benchmark pool because it is not reproducibly loadable in the frozen environment used for this audit.

### Gemma-2-9B

Loading failed because the Hugging Face repository is gated and the current account/environment does not have access.

This is an access limitation, not a quality judgment. Gemma-2-9B is therefore excluded from the current benchmark pool.

## Frozen Benchmark Pool

The candidates retained for the empirical screening benchmark are:

1. GPT-2 — legacy baseline
2. IndicBERTv2-SS — Indic-focused
3. Sarvam-1 — Indic-focused generative
4. Qwen2.5-7B — multilingual generative
5. XLM-R — broad multilingual

## Interpretation

The one-sentence encoding results are only an access and sanity check. They are not used as benchmark evidence or as the basis for selecting the final A3 comparator.

The next experiment will evaluate the frozen candidate pool on a deterministic 100-sentence-per-language subset of the aligned A1 FLORES+ corpus using identical preprocessing and multiple denominator definitions.
