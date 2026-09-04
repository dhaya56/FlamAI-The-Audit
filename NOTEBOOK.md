# FlamAI — The Audit Lab Notebook

## 2026-09-05 — Baseline Reproduction

### Hypothesis
The supplied `fertility.py`, sample corpora, and `gpt2` tokenizer should reproduce the headline tokenizer numbers reported in `REPORT_v0.md`.

### Experiment

**Command:**
```bash
python starter_kit/fertility.py --corpus eng=starter_kit/corpus_sample/eng_sample.txt --corpus hin=starter_kit/corpus_sample/hin_sample.txt --tokenizer gpt2
```

**Environment:**
* **Python:** 3.13.5
* **tiktoken:** 0.14.0

### Result
* **Tokenizer:** `gpt2`

| Language | Fertility (tok/word) | Tok/Char |
| :--- | :---: | :---: |
| **eng** | 1.27 | 0.226 |
| **hin** | 7.45 | 1.579 |

> **Key Finding:** `hin` exhibits **5.89x** the fertility of `eng` (worse tokenization).

### Interpretation
The supplied implementation and toy corpora reproduce the tokenizer numbers in `REPORT_v0.md` exactly.

### Revision / Next Steps
* Treat the reproduced result as the **v0 baseline**.
* Do **not** modify the original implementation yet.
* Audit the metric and implementation using controlled experiments and the assignment's evidence rule.