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

## 2026-09-05 — A1 corpus selection and validation

### Hypothesis

The supplied English/Hindi smoke-test corpus is too small for the corrected multilingual tokenizer comparison required in A3. A proper evaluation corpus should contain at least four languages, including English, Hindi, and two Dravidian languages, with aligned sentence IDs.

### Decision

Selected FLORES+ `dev` with the following languages:

* `eng_Latn`
* `hin_Deva`
* `kan_Knda`
* `tam_Taml`

The dataset revision was pinned to:

`5fec6c13f9e5a4db2f745d4ec0d7c9721ddc4f06`

### Experiment 1 — Dataset access and row counts

Command:

```text
python -c "from datasets import load_dataset; langs=['eng_Latn','hin_Deva','kan_Knda','tam_Taml']; [(print(x, len(load_dataset('openlanguagedata/flores_plus',x,split='dev')))) for x in langs]"
```

Result:

```text
eng_Latn 997
hin_Deva 997
kan_Knda 997
tam_Taml 997
```

### Experiment 2 — Alignment validation

Command:

```text
python -c "from datasets import load_dataset; langs=['eng_Latn','hin_Deva','kan_Knda','tam_Taml']; ds={x:load_dataset('openlanguagedata/flores_plus',x,split='dev') for x in langs}; ids={x:[r['id'] for r in ds[x]] for x in langs}; print('row_counts:', {x:len(ds[x]) for x in langs}); print('unique_ids:', {x:len(set(ids[x])) for x in langs}); print('same_id_set:', all(set(ids[x])==set(ids['eng_Latn']) for x in langs[1:])); print('first_10_ids:', {x:ids[x][:10] for x in langs})"
```

Result:

```text
row_counts: {'eng_Latn': 997, 'hin_Deva': 997, 'kan_Knda': 997, 'tam_Taml': 997}
unique_ids: {'eng_Latn': 997, 'hin_Deva': 997, 'kan_Knda': 997, 'tam_Taml': 997}
same_id_set: True
first_10_ids: {'eng_Latn': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'hin_Deva': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'kan_Knda': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'tam_Taml': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
```

### Experiment 3 — Reproducible materialization

The corpus preparation script was executed with the pinned dataset revision.

Result:

```text
dataset: openlanguagedata/flores_plus
split: dev
languages: eng_Latn, hin_Deva, kan_Knda, tam_Taml
sentences per language: 997
total language-sentences: 3988
shared aligned IDs: 997
```

The local metadata records Unicode NFC normalization only and preservation of case, punctuation, and whitespace.

### Interpretation

The selected corpus satisfies the A1 language and size requirements and has experimentally verified sentence-ID alignment across all four languages. The fixed dataset revision and preparation script make the corpus construction reproducible.

### Revision / next step

Use this corpus as the fixed evaluation set for the corrected tokenizer analysis. Do not change the corpus based on tokenizer results. Next, audit the original `fertility.py` and its metrics using isolated experiments against the verified v0 baseline.

## 2026-09-05 — A2 Experiment 1: repeated-whitespace handling

### Hypothesis

The expression `line.split(" ")` in `fertility.py` may incorrectly count empty fields as words when consecutive spaces occur, biasing the fertility metric.

### Experiment

The tokenizer, normalization, per-line averaging, and input corpora were held constant. Only the word-count operation was changed:

* Original: `line.split(" ")`
* Comparison: `line.split()`

Command:

```text
python your-submission\partA\A2_audit\experiments\exp01_whitespace.py
```

### Result

| Language | Original `split(" ")` | `split()` | Absolute delta | Relative delta |
| -------- | --------------------: | --------: | -------------: | -------------: |
| English  |              1.265206 |  1.283063 |      +0.017857 |         +1.41% |
| Hindi    |              7.448452 |  7.598452 |      +0.150000 |         +2.01% |

A separate controlled sentence test showed that the difference occurs only when consecutive whitespace is present; single-space input produced identical fertility.

### Interpretation

The suspected implementation issue is confirmed. `split(" ")` creates an empty field for consecutive spaces, increasing the word denominator and therefore lowering tokens-per-word fertility. On the supplied starter corpora, this causes a 1.41% downward distortion for English and a 2.01% downward distortion for Hindi.

The bug is real but small relative to the overall reported Hindi-versus-English fertility gap, so it does not by itself explain the large 5.89× ratio.

### Revision / next step

Do not treat the whitespace bug as the primary explanation for the report's conclusion. Investigate the metric definition and other implementation choices independently. The next experiment should test whether the way the script aggregates per-line fertility changes the cross-language result.

## 2026-09-05 — A2 Experiment 2: aggregation method

### Hypothesis

The existing script computes a per-line fertility ratio and then averages those ratios. A corpus-level ratio may produce a materially different cross-language comparison.

### Experiment

The tokenizer, corpus, normalization, and word-count definition were held constant. Only the aggregation method was changed.

Original aggregation:

```text
mean(T_i / W_i)
```

Comparison:

```text
sum(T_i) / sum(W_i)
```

Command:

```text id="qz7vgo"
python your-submission\partA\A2_audit\experiments\exp02_aggregation.py
```

### Result

| Language | Per-line average | Corpus-level ratio | Relative change |
| -------- | ---------------: | -----------------: | --------------: |
| English  |         1.265206 |           1.253165 |          -0.95% |
| Hindi    |         7.448452 |           7.403226 |          -0.61% |

Cross-language ratio:

| Method             | Hindi / English |
| ------------------ | --------------: |
| Per-line average   |       5.887148× |
| Corpus-level ratio |       5.907625× |

The cross-language ratio changes by only **+0.35%**.

### Interpretation

The alternative aggregation method changes the individual language fertility estimates slightly, but it produces only a 0.35% change in the English-to-Hindi comparison on the supplied corpus.

Therefore, this experiment does not provide evidence that the aggregation method materially explains the headline 5.89× conclusion.

### Revision / next step

Do not present the aggregation choice as a major confirmed flaw based on this experiment. Continue the audit by investigating the definition of the denominator and whether tokens-per-word is an appropriate cross-language metric for a routing-and-cost decision.

## 2026-09-05 — A2 Experiment 3: denominator sensitivity — dead end and revision

### Hypothesis

Changing the denominator from words to sentences may materially change the reported English-to-Hindi tokenizer ratio, because a whitespace-separated word is not necessarily a comparable unit across languages.

### Experiment

The original tokenizer and v0-style per-line averaging were retained. The denominator was changed from words to one sentence per observation.

Command:

```text id="e7yq1k"
python your-submission\partA\A2_audit\experiments\exp03_denominator.py
```

### Result

```text id="8chqm5"
English tokens/word      = 1.265206
Hindi tokens/word        = 7.448452

English tokens/sentence = 9.900000
Hindi tokens/sentence   = 45.900000

Word-normalized ratio    = 5.887148x
Sentence-normalized ratio = 4.636364x
Relative change           = -21.25%
```

### Dead end / validity issue

Although the denominator change produced a large difference, this experiment does not establish the correct cross-language metric. The starter English and Hindi files are only smoke-test corpora and are not consistently aligned sentence-by-sentence. In addition, the earlier aggregation experiment showed that changing aggregation can itself affect ratios, so denominator experiments must isolate aggregation and denominator choices explicitly.

Therefore the 21.25% change is recorded as an observation, not as evidence that tokens-per-sentence is the correct production metric.

### Revision

Test denominator choice on the properly aligned A1 evaluation corpus, where the same sentence IDs represent corresponding multilingual content. Keep tokenizer, aggregation, and preprocessing fixed while changing only the denominator.

### Next experiment

Compare tokens per parallel sentence with tokens per whitespace word on the fixed FLORES+ evaluation set. Use the result to determine what the denominator should hold constant for a routing-and-cost decision.

