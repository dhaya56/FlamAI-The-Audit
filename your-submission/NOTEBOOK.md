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

The denominator appears capable of materially changing the reported cross-language ratio, but the starter corpus is not a consistently aligned multilingual evaluation set. Therefore the toy-corpus result cannot establish which denominator is appropriate for the final routing/cost decision.

The next investigation was expanded to audit other transformations in `fertility.py` before making the final conceptual classification.

### Next experiment

First test whether preprocessing operations applied before tokenization, particularly forced lowercasing, create measurable asymmetric effects between English and Hindi.

After completing the implementation audit, test denominator choice on the properly aligned A1 evaluation corpus, keeping tokenizer, aggregation, and preprocessing fixed while changing only the denominator. Use that experiment to determine what the denominator should hold constant for a routing-and-cost decision.

## 2026-09-05 — A2 Experiment 4: forced lowercasing

### Hypothesis

The `line.lower()` operation may alter tokenizer fertility because casing is part of the input seen by a cased tokenizer. Because Hindi does not have the same case distinction, the preprocessing may affect English and Hindi asymmetrically.

### Experiment

The tokenizer, corpus, NFC normalization, whitespace handling, and per-line averaging were held constant. Only the lowercasing operation was changed.

Command:

```text
python your-submission\partA\A2_audit\experiments\exp04_lowercase.py
```

### Result

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

### Interpretation

Forced lowercasing has a measurable asymmetric effect on the benchmark. English fertility changes by 2.84% while Hindi fertility is unchanged in the supplied corpus. Consequently, the Hindi/English fertility ratio changes by 2.92%.

The implementation is intentional—the source comment says lowercasing is used so casing does not add noise—but the transformation changes the English input distribution while leaving Hindi unaffected. Therefore the preprocessing choice can bias the cross-language comparison.

### Revision / next step

Treat lowercasing as a confirmed benchmark methodology issue rather than assuming it is harmless. Continue auditing the character denominator and other transformations before finalizing the A2 classification.

## 2026-09-05 — A2 Experiment 5: character-denominator sensitivity

### Hypothesis

The `tok/char` metric may depend strongly on how a "character" is defined. The source script uses Python `len(line)`, which counts Unicode code points. A cross-script comparison may change materially when using other reasonable Unicode units.

### Experiment

The tokenizer, text normalization, lowercasing, word handling, and per-line averaging were held constant. Only the character denominator was changed:

1. Unicode code points: `len(line)`
2. Unicode grapheme clusters: `len(regex.findall(r"\X", line))`
3. UTF-8 bytes: `len(line.encode("utf-8"))`

Command:

```text id="5n3smd"
python your-submission\partA\A2_audit\experiments\exp05_char_denominator.py
```

### Result

| Denominator         | English tok/denominator | Hindi tok/denominator | Hindi/English ratio |
| ------------------- | ----------------------: | --------------------: | ------------------: |
| Unicode code points |                0.225636 |              1.579108 |           6.998478× |
| Grapheme clusters   |                0.225636 |              2.449732 |          10.857013× |
| UTF-8 bytes         |                0.225636 |              0.598992 |           2.654683× |

Relative to the code-point ratio:

* Grapheme ratio: +55.13%
* UTF-8 byte ratio: -62.07%

### Interpretation

The `tok/char` comparison is highly sensitive to the definition of "character" for non-Latin scripts. The same token counts produce materially different cross-language ratios under reasonable denominator definitions.

Therefore, the `tok/char` result should not be presented as an independent confirmation of the `tok/word` result. The experiment demonstrates denominator sensitivity, but does not by itself establish which denominator is the correct production cost metric.

### Revision / next step

Retain this as evidence against treating `tok/char` as a robust independent confirmation. Next, test the suspicious Unicode NFC normalization step for material effect, then evaluate denominator choice on the properly aligned A1 corpus.

## 2026-09-05 — A2 Experiment 6: NFC normalization

### Hypothesis

The explicit Unicode NFC normalization in `fertility.py` may alter the text representation seen by the tokenizer and therefore change fertility measurements.

### Experiment

The tokenizer, corpus, lowercasing, whitespace handling, character counting, and aggregation were held constant. Only NFC normalization was toggled.

Command:

```text
python your-submission\partA\A2_audit\experiments\exp06_nfc.py
```

### Result

| Language | NFC fertility | Raw fertility | Relative change |
| -------- | ------------: | ------------: | --------------: |
| English  |      1.265206 |      1.265206 |           0.00% |
| Hindi    |      7.448452 |      7.448452 |           0.00% |

The `tok/char` values were also unchanged.

Cross-language ratio:

```text
NFC  = 5.887148x
Raw  = 5.887148x
Change = 0.00%
```

### Interpretation

NFC normalization produced no measurable change on the supplied starter corpus with the GPT-2 tokenizer. Therefore, although the normalization step may initially appear capable of affecting Unicode tokenization, this experiment provides no evidence that it distorts the reported numbers for this benchmark.

### Revision / next step

Do not classify NFC normalization as a bug based on this evidence. It remains a documented preprocessing choice. The next major task is to test the denominator question on the properly aligned A1 evaluation corpus, which is the strongest candidate for the conceptual problem identified in A2.

## 2026-09-05 — A2 Experiment 7: denominator choice on aligned multilingual corpus

### Hypothesis

The v0 `tokens/word` metric may be conceptually unsuitable for cross-language routing and cost comparisons because a whitespace-separated word does not represent a controlled amount of underlying content across languages. A parallel-sentence denominator may produce a materially different estimate of relative token workload when the same underlying sentence content is held constant.

### Experiment

The fixed A1 FLORES+ `dev` corpus was used with the same 997 aligned sentence IDs for English, Hindi, Kannada, and Tamil.

The tokenizer and tokenizer-side preprocessing were held constant:

* GPT-2 via `tiktoken`
* Unicode NFC normalization
* lowercasing
* original v0 whitespace definition
* per-line averaging

The experiment was deliberately narrowed to compare only:

1. tokens per whitespace word
2. tokens per parallel sentence

This isolates the denominator question without simultaneously changing other metric definitions.

Command:

```text
python your-submission\partA\A2_audit\experiments\exp07_aligned_denominators.py
```

### Result

| Language | tokens/word | tokens/sentence |
| -------- | ----------: | --------------: |
| English  |    1.282531 |       26.776329 |
| Hindi    |    7.823186 |      192.419258 |
| Kannada  |   22.148288 |      350.854564 |
| Tamil    |   24.733182 |      398.384152 |

Relative to English:

| Language | tokens/word ratio | tokens/sentence ratio |
| -------- | ----------------: | --------------------: |
| Hindi    |         6.099802× |             7.186170× |
| Kannada  |        17.269202× |            13.103162× |
| Tamil    |        19.284665× |            14.878221× |

### Interpretation

The relative language penalty changes substantially depending on the denominator. Hindi changes from 6.10× to 7.19×, Kannada from 17.27× to 13.10×, and Tamil from 19.28× to 14.88×.

This supports the hypothesis that `tokens/word` is not a sufficient cross-language normalization for a routing-and-cost decision. A whitespace word is not a controlled unit of underlying content across languages, whereas aligned sentence IDs allow corresponding multilingual content to be compared.

The experiment does not establish that tokens per sentence is universally the correct production metric. It establishes that denominator choice is consequential and that the v0 5.89× headline cannot be treated as a universal language-specific serving-cost multiplier.

### Revision / next step

Treat denominator choice as the leading conceptual issue in the v0 analysis. Perform one final paired sentence-level consistency check on the aligned corpus to strengthen the evidence for the conceptual conclusion. Then use the validated denominator alternatives as inputs to the A3 corrected analysis with a second tokenizer.


