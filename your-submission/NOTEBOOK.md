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

## 2026-09-05 — A2 Experiment 8: paired sentence-level workload check

### Hypothesis

The denominator problem identified in the aligned-corpus analysis should remain visible when token workload is compared sentence-by-sentence across the same parallel content. If the result were only an artifact of corpus-level aggregation, paired sentence ratios would give a substantially different conclusion.

### Experiment

For each of the 997 FLORES+ sentence IDs, the target-language token count was divided by the corresponding English token count.

The tokenizer and preprocessing were held constant:

* GPT-2 via `tiktoken`
* NFC normalization
* lowercasing
* original v0 whitespace behavior

Two summaries were compared:

1. Mean of the 997 paired target/English token ratios.
2. Corpus-level target-token total divided by English-token total.

The distribution of paired ratios was also summarized using the median, minimum, maximum, and standard deviation.

Command:

```text
python your-submission\partA\A2_audit\experiments\exp08_paired_workload.py
```

### Result

| Language | Mean paired ratio | Median paired ratio | Min ratio |  Max ratio | Std. dev. | Corpus-level ratio |
| -------- | ----------------: | ------------------: | --------: | ---------: | --------: | -----------------: |
| Hindi    |         7.290745x |           7.153846x | 4.064516x | 12.142857x |  1.426133 |          7.186170x |
| Kannada  |        13.317866x |          13.086957x | 7.193548x | 24.928571x |  2.621160 |         13.103162x |
| Tamil    |        15.154565x |          14.944444x | 5.794118x | 28.500000x |  2.975863 |         14.878221x |

The paired means and corpus-level ratios were close for all three target languages. The paired ratios nevertheless showed substantial sentence-level variation.

### Interpretation

The aligned-content workload comparison is not explained by a single corpus-level aggregation artifact. Sentence-level paired ratios and corpus-level target/English token ratios lead to the same qualitative conclusion: Hindi, Kannada, and Tamil require substantially more model tokens than English for the corresponding FLORES+ content under the GPT-2 tokenizer.

The paired-ratio distributions also show that the workload multiplier varies across individual sentences. Hindi ranges from 4.06x to 12.14x, Kannada from 7.19x to 24.93x, and Tamil from 5.79x to 28.50x.

This strengthens the conceptual finding that whitespace-word normalization is not a sufficient cross-language workload denominator for a routing-and-cost decision.

This experiment does not establish that the paired target/English token ratio is universally the correct production metric. That final decision will be made in A3 after comparing at least two tokenizers and multiple denominator choices.

### Revision / next step

The paired sentence-level check strengthens the denominator finding: the target-to-English workload ratios remain consistent when examined both sentence-by-sentence and at corpus level.

After this check, the A2 conceptual investigation was considered complete. The next step was to verify the suspicious-looking `random.seed(1337)` statement as a harmless item required by the A2 rubric, without modifying the original starter file.

Following that final check, consolidate the A2 findings and move to A3, where the corrected analysis will compare two tokenizers on the fixed A1 corpus using multiple denominator definitions and determine the single operational metric for routing and cost.

## 2026-09-05 — A2 Experiment 9: unused random seed

### Hypothesis

The `random.seed(1337)` statement at the top of `fertility.py` appears suspicious because the script imports `random` and seeds it, but the tokenizer benchmark may not use randomness anywhere in the computation.

### Experiment

First, the original `fertility.py` was executed twice with the same inputs. Both runs produced identical output.

A second controlled experiment created a temporary copy of `fertility.py` with only the `random.seed(1337)` statement removed. The original script and temporary copy were then run with exactly the same command and inputs.

Command:

```text id="9c7v1j"
python your-submission\partA\A2_audit\experiments\exp09_random_seed.py
```

### Result

Original script with seed:

```text id="5q8z3x"
eng = 1.27
hin = 7.45
ratio = 5.89x
```

Temporary copy without seed:

```text id="r1nnb8"
eng = 1.27
hin = 7.45
ratio = 5.89x
```

The complete outputs were identical:

```text
outputs_identical: True
```

### Interpretation

The random seed is unused by the benchmark computation. Removing it from a temporary copy does not change any reported tokenizer result.

Therefore, this statement is suspicious-looking but harmless for this benchmark. It should not be reported as a numerical bug.

### Revision / next step

The A2 implementation audit is now complete. The remaining work is to consolidate the evidence into the final A2 findings and then perform the corrected A3 tokenizer comparison.

## A3 — Tokenizer Candidate Access Screening

### Hypothesis

Before performing the corrected A3 comparison, screen a predefined set of multilingual/Indic-aware tokenizer candidates for local reproducibility across the same four languages used in A1: English, Hindi, Kannada, and Tamil.

GPT-2 is retained as the legacy baseline because it is the tokenizer used by the starter audit. The screening is intended to determine which additional tokenizer candidates can be evaluated reproducibly; it is not intended to declare a tokenizer winner from a one-sentence sanity check.

### Experiment

Created:

`your-submission/partA/A3_corrected_analysis/candidate_screen/candidate_access_test.py`

The script attempts to load each candidate using Hugging Face `AutoTokenizer` and encode one fixed sanity-check sentence in each of the four A1 languages with:

`add_special_tokens=False`

Candidate pool tested:

* GPT-2 — `gpt2`
* IndicBERTv2-SS — `ai4bharat/IndicBERTv2-SS`
* IndicTrans2 — `ai4bharat/indictrans2-en-indic-1B`
* Sarvam-1 — `sarvamai/sarvam-1`
* Qwen2.5-7B — `Qwen/Qwen2.5-7B`
* Gemma-2-9B — `google/gemma-2-9b`
* XLM-R — `FacebookAI/xlm-roberta-base`

Environment:

* Python 3.13.5
* Transformers 5.16.1
* SentencePiece installed

Command:

`python your-submission\partA\A3_corrected_analysis\candidate_screen\candidate_access_test.py`

### Result

Five candidates loaded successfully and encoded all four languages:

| Candidate      | Vocab size | English | Hindi | Kannada | Tamil |
| -------------- | ---------: | ------: | ----: | ------: | ----: |
| GPT-2          |     50,257 |      10 |    66 |     144 |   152 |
| IndicBERTv2-SS |    200,000 |      10 |     9 |      39 |    50 |
| Sarvam-1       |     68,096 |      10 |     9 |       9 |     9 |
| Qwen2.5-7B     |    151,665 |      10 |    38 |      72 |    59 |
| XLM-R          |    250,002 |      11 |    10 |      10 |    11 |

IndicTrans2 was first rejected because its repository required `trust_remote_code=True`. A controlled retry with `trust_remote_code=True` progressed further but failed with:

`ModuleNotFoundError: No module named 'transformers.onnx'`

Therefore, IndicTrans2 was not reproducibly loadable in the frozen environment used for this audit.

Gemma-2-9B could not be loaded because the Hugging Face repository is gated and the current account does not have access.

### Interpretation

The one-sentence token counts are only an access and encoding sanity check. They are not used to rank the candidates or select the final A3 tokenizer because the sample is too small to support such a conclusion.

The five reproducibly loadable candidates were retained for the next screening experiment.

### Revision / Next Step

Do not select the final A3 comparator yet.

Next, evaluate the frozen five-candidate pool on a deterministic 100-sentence-per-language subset of the aligned A1 FLORES+ corpus using identical NFC preprocessing and multiple workload denominators. Use those empirical results to select the final multilingual/Indic-aware comparator for the complete A3 analysis.

## A3 — 100-Sentence Tokenizer Candidate Screen

### Hypothesis

The tokenizer candidate that appears most suitable for the final A3 comparison should remain strong when evaluated on a larger aligned sample and under more than one denominator definition, rather than being selected from a one-sentence sanity check.

### Experiment

Evaluated the five reproducibly loadable tokenizer candidates retained after the access screen:

* GPT-2
* IndicBERTv2-SS
* Sarvam-1
* Qwen2.5-7B
* XLM-R

Used the deterministic first 100 aligned FLORES+ sentence IDs for each of English, Hindi, Kannada, and Tamil.

Command:

`python your-submission\partA\A3_corrected_analysis\candidate_screen\candidate_screen_benchmark.py`

Preprocessing preserved the original text, removed line endings only, applied no lowercasing, and disabled special tokens.

Measured:

* tokens/sentence
* tokens/whitespace word
* tokens/grapheme
* tokens/UTF-8 byte
* relative total token workload versus English

### Result

GPT-2 produced the highest Indic token workload by a large margin:

* Hindi: 7.312x English
* Kannada: 13.218x English
* Tamil: 15.072x English

Sarvam-1 produced:

* Hindi: 1.103x
* Kannada: 1.248x
* Tamil: 1.149x

XLM-R produced:

* Hindi: 1.279x
* Kannada: 1.381x
* Tamil: 1.371x

IndicBERTv2-SS and Qwen2.5-7B were intermediate.

### Interpretation

The 100-sentence screen confirms that tokenizer choice materially changes Indic token workload and that GPT-2 has substantially higher Indic inflation than the other screened candidates.

Sarvam-1 and XLM-R are the strongest candidates from this screen, but no final tokenizer was selected yet.

### Revision / Next Step

Before final selection, compare the candidates using aggregated `tokens/word` and `tokens/UTF-8 byte` measurements.

Use the same raw screening results for this analysis rather than running another corpus experiment.

## A3 — Candidate Ranking and Final Comparator Selection

### Hypothesis

If a tokenizer is genuinely preferable for multilingual/Indic workloads, it should remain competitive across multiple denominator definitions rather than winning under only one metric.

### Experiment

Used the raw 100-sentence-per-language screening results and aggregated Hindi, Kannada, and Tamil using a simple mean.

Command:

`python your-submission\partA\A3_corrected_analysis\candidate_screen\analyze_screen.py`

Primary criterion: lower mean `tokens/word`.

Secondary criterion: lower mean `tokens/UTF-8 byte`.

### Result

| Candidate      | Mean tok/word | Mean tok/byte | Mean Indic vs English |
| -------------- | ------------: | ------------: | --------------------: |
| Sarvam-1       |        2.0268 |        0.1036 |               1.1666x |
| XLM-R          |        2.1531 |        0.1101 |               1.3436x |
| IndicBERTv2-SS |        5.1211 |        0.2347 |               3.0638x |
| Qwen2.5-7B     |        8.6179 |        0.4270 |               5.6332x |
| GPT-2          |       17.7657 |        0.8540 |              11.8671x |

### Interpretation

Sarvam-1 ranks first under both predefined denominator criteria. XLM-R ranks second under both.

The final A3 multilingual/Indic-aware comparator is therefore selected as Sarvam-1.

This is a screening-based selection, not a claim that Sarvam-1 is globally optimal.

### Revision / Next Step

Freeze Sarvam-1 as the second tokenizer for the final A3 comparison.

Evaluate GPT-2 and Sarvam-1 on the complete 997-sentence-per-language A1 FLORES+ corpus using the corrected preprocessing and the final denominator set.

## A3-0 — Legacy Method Reproduction

### Hypothesis

Before correcting the A3 methodology, reproduce the original `fertility.py` calculation on the complete aligned A1 FLORES+ corpus to establish an exact full-corpus before-state.

### Experiment

Created:

`your-submission/partA/A3_corrected_analysis/legacy_reproduction.py`

The script applies the original methodology:

* NFC normalization
* lowercasing
* `line.split(" ")`
* `len(line)` for the character denominator
* arithmetic mean of per-line ratios
* `add_special_tokens=False`

Evaluated GPT-2 and the selected Sarvam-1 tokenizer on all 997 sentences in each of English, Hindi, Kannada, and Tamil.

Command:

`python your-submission\partA\A3_corrected_analysis\legacy_reproduction.py`

### Result

GPT-2:

* English fertility: 1.282531
* Hindi fertility: 7.823186
* Kannada fertility: 22.148288
* Tamil fertility: 24.733182

Relative to English:

* Hindi: 6.099802x
* Kannada: 17.269202x
* Tamil: 19.284665x

Sarvam-1:

* English fertility: 1.460539
* Hindi fertility: 1.400991
* Kannada fertility: 2.348439
* Tamil fertility: 2.150157

Relative to English:

* Hindi: 0.959229x
* Kannada: 1.607927x
* Tamil: 1.472167x

### Interpretation

The legacy methodology reproduces a large GPT-2 Indic token-workload gap on the complete A1 corpus.

However, these fertility values are not treated as direct serving-cost multipliers because A2 identified problems with the lowercasing step, literal `split(" ")` denominator, and language-dependent denominator interpretation.

### Revision / Next Step

Use the same full aligned corpus for the corrected A3 analysis so that the effect of the methodological changes can be measured against this explicit before-state.

## A3-1 / A3-2 — Corrected Full-Corpus Analysis and Direct Workload Comparison

### Hypothesis

After correcting the methodological issues identified in A2, the tokenizer comparison should still show whether an Indic-aware tokenizer materially changes the actual model-token workload for the same multilingual content.

### Experiment

Evaluated GPT-2 and the selected Sarvam-1 tokenizer on all 997 aligned FLORES+ sentences for each of English, Hindi, Kannada, and Tamil.

Command:

`python your-submission\partA\A3_corrected_analysis\corrected_comparison.py`

Corrected preprocessing:

* NFC normalization only
* original case preserved
* internal whitespace preserved
* no lowercasing
* `split()` for the whitespace-word denominator
* Unicode grapheme counting
* UTF-8 byte counting
* `add_special_tokens=False`

### Result

GPT-2 token workload:

* English: 25,741
* Hindi: 191,828
* Kannada: 349,772
* Tamil: 397,163

Sarvam-1 token workload:

* English: 29,915
* Hindi: 34,206
* Kannada: 37,225
* Tamil: 34,539

Relative to English, GPT-2 produced 7.452236x, 13.588128x, and 15.429199x the token workload for Hindi, Kannada, and Tamil respectively.

Sarvam-1 produced 1.143440x, 1.244359x, and 1.154571x respectively.

### Direct Workload Experiment

Command:

`python your-submission\partA\A3_corrected_analysis\compare_token_reduction.py`

For the same aligned Indic content:

* Hindi: 82.17% fewer tokens with Sarvam-1
* Kannada: 89.36% fewer tokens
* Tamil: 91.30% fewer tokens

Combined Hindi + Kannada + Tamil:

* GPT-2: 938,763 tokens
* Sarvam-1: 105,970 tokens
* Reduction: 88.71%

### Legacy → Corrected Revision

Correcting the methodology changed the GPT-2 `tokens/word` value by:

* English: -4.22%
* Hindi: -0.35%
* Kannada: +2.35%
* Tamil: -0.47%

Sarvam-1 changed by:

* English: -2.25%
* Hindi: -0.78%
* Kannada: +2.73%
* Tamil: -0.44%

The qualitative tokenizer comparison therefore survives the methodological corrections.

### Interpretation

The primary routing/cost metric is direct model-token workload on equivalent aligned content, represented by total tokens or tokens per aligned sentence.

`Tokens/word` remains useful as a diagnostic normalization but is not treated as a direct cost multiplier because words are not a language-neutral workload unit.

Sarvam-1 has a clear Indic-language token-workload advantage in this evaluation, but uses 16.22% more tokens than GPT-2 on the evaluated English sentences. Therefore the evidence supports language-specific routing rather than a universal “Sarvam is cheaper” conclusion.

### Revision / Next Step

A3 quantitative comparison is complete.

Next, prepare the A4 one-page memo using the corrected headline numbers, routing recommendation, principal caveat, and one production metric to monitor.

## A4 — Recommendation Memo

### Hypothesis / Decision

Use the corrected A3 token-workload evidence to produce a production-oriented routing recommendation.

### Evidence Used

The recommendation is based on the complete aligned FLORES+ comparison of GPT-2 and Sarvam-1:

* Hindi: 82.17% fewer Sarvam-1 tokens
* Kannada: 89.36% fewer
* Tamil: 91.30% fewer
* Combined Hindi + Kannada + Tamil: 88.71% fewer tokens
* English: Sarvam-1 uses 16.22% more tokens than GPT-2

### Recommendation

Use language-aware routing: route Hindi, Kannada, and Tamil traffic to Sarvam-1 while retaining GPT-2 for English, subject to production quality validation.

The routing/cost decision is based primarily on direct model-token workload for equivalent aligned content rather than tokens per whitespace-defined word.

### Biggest Caveat

The experiment measures tokenizer token workload, not end-to-end latency, monetary serving cost, or task-quality parity. Lower token counts therefore do not by themselves prove lower production cost or equivalent model quality.

### Production Metric

Monitor p95 input tokens per request by language and tokenizer route.

This directly tests whether live traffic follows the token-workload assumptions established by the FLORES+ evaluation.

### Revision / Next Step

Part A is complete after the A4 memo is committed. Merge the completed Part-A branch into `main` before beginning Part B.

## B1 — KV-Cache Capacity Reconciliation

### Hypothesis

From the model specification alone, derive the KV-cache footprint per token and estimate how many complete 4096-token sequences the GPU can hold. Only after making that prediction, compare it with the benchmark log.

### Experiment

Created:

`your-submission/partB/B1/b1_capacity_reconciliation.py`

and:

`your-submission/partB/B1/b1_capacity_reconciliation.md`

Command:

`python your-submission\partB\B1\b1_capacity_reconciliation.py`

The calculation explicitly separates:

1. Prediction from model specification alone
2. Check against `bench_log.csv`
3. Reconciled calculation

The supplied `24 GB` GPU memory and `1.6 GB` non-KV overhead are treated as decimal GB (`1 GB = 10^9 bytes`) throughout the capacity calculation.

### Stage 1 — Prediction from Model Spec Alone

KV-cache bytes per token:

`2(K,V) × 28 layers × 8 KV heads × 128 head_dim × 2 bytes(fp16) = 114,688 bytes/token`

This is:

`114,688 / 1024 = 112 KiB/token`

One complete 4096-token sequence therefore requires:

`114,688 × 4096 = 469,762,048 bytes = 448 MiB`

Using the configured GPU budget:

`24 GB × 0.92 = 22.08 GB`

and subtracting only the stated non-KV overhead in the first pass:

`22.08 − 1.6 = 20.48 GB`

Initial capacity hypothesis:

`20,480,000,000 / 469,762,048 = 43.597 sequences`

Therefore the initial model-spec-only hypothesis was approximately **43.60 sequences**.

### Stage 2 — Check Against Benchmark Log

The relevant capacity-stress rows have:

`prompt_len + gen_len = 3584 + 512 = 4096`

Observed results:

* Batch 24: `preempted_seqs = 0`, `kv_cache_util = 0.93`
* Batch 32: `preempted_seqs = 7`, `kv_cache_util = 0.97`
* Batch 48: `preempted_seqs = 23`, `kv_cache_util = 0.97`

Inferred resident-sequence counts:

`32 − 7 = 25`

`48 − 23 = 25`

The initial ~43.60 prediction therefore does not match the observed capacity behavior.

### Stage 3 — Reconciled Calculation

The missing allocation in the initial calculation was model-weight memory.

For the 4.2B-parameter fp16 model:

`4.2 × 10^9 × 2 = 8.4 × 10^9 bytes = 8.4 GB`

Correct KV budget:

`22.08 − 8.4 − 1.6 = 12.08 GB`

Corrected capacity:

`12,080,000,000 / 469,762,048 = 25.715 sequences`

Therefore the reconciled capacity is approximately **25 concurrent 4096-token sequences**.

This agrees with both capacity-stress rows:

`32 − 7 = 25`

`48 − 23 = 25`

The reported KV utilization is also consistent: scaling the 24-sequence utilization gives approximately `0.93 × 25/24 = 0.969`, matching the observed `0.97`.

### Interpretation

The first-pass ~43.60-sequence result was a genuine incomplete memory-budget calculation because model weights had not been reserved.

After accounting for model weights and the stated non-KV overhead, the model-spec prediction becomes approximately 25 sequences, which is independently supported by the benchmark log.

### Revision / Next Step

B1 capacity reconciliation is complete.

Proceed to B2 using the long-context throughput rows, with particular attention to the relationship between `reported_tok_s`, `wall_clock_s`, `batch_size`, and the 3584-token prompt configuration.

## B2 — Long-Context Throughput Anomaly

### Initial Hypothesis

The `prompt_len = 3584` long-context sweep should show increasing `reported_tok_s` as batch size increases, until some capacity or serving constraint causes the scaling behavior to break.

The first analysis should identify any reversal from the data rather than assuming the location or cause of the anomaly.

### Experiment 1 — Long-Context Sweep Inspection

Created:

`your-submission/partB/B2/b2_anomaly_analysis.py`

Command:

`python your-submission\partB\B2\b2_anomaly_analysis.py`

Filtered the benchmark log to `prompt_len = 3584`.

Observed `reported_tok_s`:

* Batch 4: 565.4
* Batch 8: 902.6
* Batch 16: 1311.4
* Batch 24: 1607.4
* Batch 32: 1384.0
* Batch 48: 1298.5

The first throughput reversal is batch 24 → 32:

`1607.4 → 1384.0 tok/s`

which is a **13.90% decrease** despite the larger batch.

A second reversal occurs from batch 32 → 48:

`1384.0 → 1298.5 tok/s`

which is a **6.18% decrease**.

### Revision — Avoid Hard-Coded Conclusions

The initial analysis script contained a hard-coded statement identifying the anomaly.

That was revised because the experiment should **discover the throughput reversal from the benchmark data**, not be given the conclusion in advance.

The script was changed to detect a reversal whenever a larger batch has lower `reported_tok_s` than the preceding batch.

The revised script automatically identified:

* first reversal: batch 24 → 32
* second reversal: batch 32 → 48

### Experiment 2 — Verify What `reported_tok_s` Measures

The same B2 script independently reconstructed the reported throughput using:

`batch_size × (prompt_len + gen_len) / wall_clock_s`

For example, batch 24:

`(24 × (3584 + 512)) / 61.16 = 1607.33 tok/s`

reported value:

`1607.4 tok/s`

Similar agreement was observed for every row in the 3584-prompt sweep.

Interpretation:

`reported_tok_s` is effectively counting **prompt + generated tokens per wall-clock second**.

This changed the interpretation of the throughput column: it should not be described as generated-token-only throughput or as goodput.

### Experiment 3 — Mechanism Evidence

The first reversal was examined by comparing the automatically selected pre-reversal and reversal rows.

Batch 24:

* `reported_tok_s = 1607.4`
* `kv_cache_util = 0.93`
* `preempted_seqs = 0`
* `ttft_ms_p50 = 500.5 ms`
* `e2e_ms_p95 = 69,221.3 ms`

Batch 32:

* `reported_tok_s = 1384.0`
* `kv_cache_util = 0.97`
* `preempted_seqs = 7`
* `ttft_ms_p50 = 636.9 ms`
* `e2e_ms_p95 = 97,465.7 ms`

Changes from batch 24 to batch 32:

* `reported_tok_s`: **-13.90%**
* `kv_cache_util`: **0.93 → 0.97**
* `preempted_seqs`: **0 → 7**
* `ttft_ms_p50`: **+27.25%**
* `e2e_ms_p95`: **+40.80%**

The next row shows the deterioration continuing:

Batch 48:

* `reported_tok_s = 1298.5`
* `kv_cache_util = 0.97`
* `preempted_seqs = 23`
* `ttft_ms_p50 = 955.4 ms`
* `e2e_ms_p95 = 105,427.5 ms`

From batch 32 to batch 48:

* `reported_tok_s`: **-6.18%**
* `preempted_seqs`: **7 → 23**
* `ttft_ms_p50`: **+50.01%**

### Interpretation / Revision

The evidence supports the following mechanism:

Increasing batch size reaches a KV-cache capacity boundary. At the last preemption-free point (batch 24), KV utilization is 0.93 and no sequences are preempted. Increasing to batch 32 raises utilization to 0.97 and introduces 7 preempted sequences while throughput falls and latency rises. Further increasing to batch 48 increases preemptions to 23 and throughput falls again.

Therefore, the observed anomaly is associated with **KV-cache saturation followed by scheduler preemption and associated scheduling/capacity-management overhead**.

The benchmark does not expose internal scheduler behavior, so no stronger claim about the exact implementation of preemption or recomputation is made.

### Experiment 4 — Data-Derived Operating Point

The analysis automatically identified the **largest preemption-free batch** as batch 24.

Observed operating point:

* batch 24
* `reported_tok_s = 1607.4`
* `kv_cache_util = 0.93`
* `preempted_seqs = 0`

Observed comparison with the first reversal row:

`1384.0 → 1607.4 tok/s = +16.14%`

Observed comparison with the largest tested batch:

`1298.5 → 1607.4 tok/s = +23.79%`

### Final Recommendation

For the 3584-token prompt workload, use the largest observed preemption-free operating point as the concurrency cap:

**batch 24 / equivalent `max_num_seqs = 24`**

or use equivalent admission control that queues requests above this level rather than allowing the workload to enter the observed preempting regime.

The quantitative effects above are data-derived predictions based on the measured operating points, not guarantees for unrelated production workloads.

### Next Step

B2 is complete after recording the evidence and recommendation.

Proceed to B3, where the same `reported_tok_s` column must be interpreted carefully to determine why the v0 report concluded that longer prompts improve throughput and that batch 48 would reach approximately 3200 tok/s.

## B3 — Corrected interpretation of REPORT_v0 Section 2

### Question

`REPORT_v0` Section 2 claims that longer prompts give better throughput and that batch 48 should deliver approximately 3200 tok/s.

The task asks for the misread column, the honest goodput of the batch-24 long-prompt row using two independent derivations, and the corrected report conclusion.

### Source evidence

The relevant benchmark columns are:

```text
batch_size,prompt_len,gen_len,num_requests,wall_clock_s,reported_tok_s,...
```

For batch 24 with the long prompt:

```text
batch_size   = 24
prompt_len   = 3584
gen_len      = 512
wall_clock_s = 61.16
reported_tok_s = 1607.4
```

### Finding 1 — Misread column

The misread column is:

```text
reported_tok_s
```

`model_spec.md` identifies this as the harness's built-in throughput counter.

The batch-24 value can be reproduced as:

```text
24 × (3584 + 512) / 61.16
= 1607.33 tok/s
```

which matches the logged 1607.4 tok/s.

Therefore `reported_tok_s` already represents aggregate prompt-plus-generation token throughput for the workload. It must not be multiplied by batch size again.

### Finding 2 — The long-vs-short comparison does not establish that longer prompts improve GPU utilization

At batch 16:

```text
Long prompt:
16 × (3584 + 512) / 49.97
= 1311.5 tok/s
```

Logged value:

```text
1311.4 tok/s
```

Short prompt:

```text
16 × (512 + 256) / 13.91
= 883.3 tok/s
```

Logged value:

```text
883.2 tok/s
```

The long workload contains 4096 tokens/request while the short workload contains 768 tokens/request. Therefore the higher aggregate token rate for the long workload does not, by itself, demonstrate that longer prompts improve GPU utilization.

The complete long-prompt sweep shows:

```text
batch 4  = 565.4 tok/s
batch 8  = 902.6 tok/s
batch 16 = 1311.4 tok/s
batch 24 = 1607.4 tok/s
batch 32 = 1384.0 tok/s
batch 48 = 1298.5 tok/s
```

Observed pattern:

```text
565.4 → 902.6 → 1311.4 → 1607.4 → 1384.0 → 1298.5 tok/s
```

Throughput peaks at batch 24 and then decreases.

### Finding 3 — Honest batch-24 goodput

For this analysis, goodput is useful generated output tokens per second.

Method 1:

```text
24 × 512 = 12,288 generated tokens

12,288 / 61.16
= 200.92 generated tok/s
```

Method 2:

```text
24 / 61.16
= 0.39241 requests/s

0.39241 × 512
= 200.92 generated tok/s
```

Both methods agree.

```text
Honest batch-24 goodput ≈ 201 generated tok/s
```

### Finding 4 — Batch-48 extrapolation is invalid

`REPORT_v0` uses the approximately 1600 tok/s batch-24 value as though it were a per-L4 rate and then extrapolates to batch 48.

The actual batch-48 log row reports:

```text
1298.5 tok/s
```

The corresponding generated-output goodput is:

```text
48 × 512 / 151.41
= 162.31 generated tok/s
```

Therefore the approximately 3200 tok/s claim is not supported by the measurements.

### B3 conclusion

The report should have said that, for the tested long-prompt workload, aggregate prompt-plus-generation throughput increased with batch size up to batch 24 and then declined. Batch 24 was the highest observed aggregate throughput at 1607.4 tok/s. The honest generated-output goodput at that point was approximately 201 tok/s. The approximately 3200 tok/s batch-48 estimate was invalid because `reported_tok_s` was already an aggregate workload throughput and the actual batch-48 measurement was only 1298.5 tok/s.

---

## B4 — Serving metric to test the B2 mechanism

### Question

Choose one serving-stack counter or metric that would test the B2 mechanism and state the expected value.

### Metric selected

Use the scheduler's:

```text
KV-cache preemption counter
```

or equivalent count of sequences preempted by the serving scheduler.

### Reason

The B2 evidence indicates that the throughput reversal begins when KV-cache pressure becomes high and scheduler preemption appears.

Observed benchmark transition:

```text
Batch 24:
KV util = 0.93
preempted sequences = 0
throughput = 1607.4 tok/s

Batch 32:
KV util = 0.97
preempted sequences = 7
throughput = 1384.0 tok/s

Batch 48:
KV util = 0.97
preempted sequences = 23
throughput = 1298.5 tok/s
```

The expected operational signature is therefore:

```text
0 preemptions around batch 24
→ non-zero preemptions at batch 32
→ more preemptions at batch 48
```

The metric would strongly support the B2 mechanism if preemptions begin at the same concurrency where throughput reverses.

### B4 conclusion

The single most useful serving-stack metric is the scheduler's KV-cache preemption counter. Under the same workload, I would expect approximately 0 preemptions at batch 24, about 7 at batch 32, and about 23 at batch 48. This directly tests whether the scheduler begins preempting sequences at the same point where the observed throughput reversal occurs.

## Part C — Decision Memo: Conversational Register

### Part C scope

The Part C task is a decision-memo problem rather than an empirical benchmark task. I therefore did not claim to have measured production quality, A100 throughput, reviewer speed, or model latency when those values were not supplied. The notebook records the decision analysis, assumptions considered, external-review feedback, arithmetic, rejected approaches, and the final recommendation.

---

### C0 — Initial framing

**Hypothesis**

One of the three listed paths should be selected as the best way to make responses more casual and conversational:

* (a) SFT on synthetic casualized pairs
* (b) ≤1B inference-time rewriter
* (c) prompt engineering only

**Initial reasoning**

The first instinct was that prompt engineering might be preferable because it is reversible and does not require training.

**Risk identified**

This was only an intuition. The scenario does not provide evidence that prompt engineering is sufficiently effective across all six languages.

**Revision**

Do not choose A, B, or C solely from generic claims about the techniques. Compare them under the actual resource constraints and explicitly identify what must be assumed.

---

### C1 — Constraint audit

**Given constraints**

```text
Target languages:
Hindi, Kannada, Tamil, Telugu, Bengali, Marathi

Compute:
1 × A100-80GB for 2 weeks

Human review:
1 native-speaker reviewer
Hindi + Kannada only
10 h/week

Timeline:
launch review in 3 weeks

External APIs:
$0 budget
```

**Observation**

The reviewer is a deliberately specified scarce resource. Native-speaker review is available only for 2 of the 6 languages, so any strategy that changes model behavior globally creates a validation gap for four languages.

**Revision**

Use the reviewer as a decision resource across methods rather than associating the reviewer with only one path.

---

### C2 — First external review: Gemini

**Hypothesis challenged**

Prompt engineering is likely sufficient under the constraints.

**Gemini Round 1 result**

Recommended path (c) prompt engineering, mainly because it is reversible, requires no training, and avoids synthetic-data risks.

**Issues identified in review**

Several numerical claims were not grounded in the scenario, including assumed 27B–70B local inference throughput, rewriter latency, reviewer speed, and synthetic-data requirements. These values were treated as assumptions but were presented too confidently.

**Revision**

Do not use external numerical claims as facts. Every number in the final memo must be either:

1. given by the scenario,
2. explicitly labelled as an assumption, or
3. derived from those values.

---

### C3 — Second external review: Claude Round 1

**Independent result**

Claude recommended path (b), but only conditionally: test prompt engineering first, then use the rewriter if prompting is inadequate.

**Important finding**

Claude identified that committing to prompt engineering without testing it is itself an unsupported claim. It also highlighted semantic drift as the key risk for a ≤1B rewriter.

**Revision**

The decision should not be framed as “C is best” or “B is best” before considering evidence. A staged strategy is a valid candidate.

---

### C4 — External-review adversarial pass

**Action**

Both Gemini and Claude were given an adversarial analysis request requiring them to:

* separate facts from assumptions,
* identify hidden weaknesses of A/B/C,
* identify quantities that must be estimated,
* avoid unsupported GPU-throughput claims,
* propose Day-1 experiments.

**Finding**

Both analyses converged on the same structural issue: all three paths depend on the ability to produce sufficiently good casual, faithful behavior across six languages, while only Hindi and Kannada have native-speaker validation.

**Important disagreement with earlier reasoning**

The low cost of prompt engineering does not by itself make it the best first decision. The relevant question is information gained and probability of meeting the product requirement under the resource limits.

**Revision**

Evaluate combinations and staged strategies rather than assuming A/B/C are mutually exclusive final choices.

---

### C5 — Hybrid strategy considered

**Hypothesis**

A language-conditional strategy may be better than forcing one intervention across all six languages:

```text
Prompt engineering
        ↓
language meets quality gate?
   YES → retain prompt-only
   NO  → add ≤1B rewriter
        ↓
still fails → consider SFT
```

**Reasoning**

This allows:

* prompt-only deployment where it is sufficient,
* stronger intervention only where needed,
* no unnecessary serving component for languages that already pass,
* SFT reserved for cases where lighter interventions fail.

**Risk**

The language split must not be chosen arbitrarily. For example, selecting Hindi or English for the rewriter before observing evidence would be an unsupported assumption.

**Revision**

The final strategy should be **language-conditional**, with the allocation determined by the predefined quality gate.

---

### C6 — “Test all three” idea evaluated

**Hypothesis**

Because there is no single prescribed correct path, it may be useful to compare all three approaches rather than committing immediately.

**Finding**

A full implementation of all three would unnecessarily consume engineering and GPU resources. However, small decision-oriented pilots can compare the approaches without fully deploying them.

**Revision**

Do not fully train or deploy all three on Day 1. Use a small controlled comparison to determine whether additional complexity is justified.

---

### C7 — SFT-first hypothesis rejected

**Hypothesis considered**

Use the available A100 to perform SFT immediately because the compute constraint appears feasible.

**Finding**

The principal objection is not raw GPU availability. SFT has the largest validation burden because it changes shared model weights, requires high-quality casual targets, and can create regressions in the four languages without native review.

The lack of an external API budget also means that synthetic casual targets must be generated or curated locally.

**Revision**

Do not start with SFT. Reserve SFT as a fallback only after lighter interventions fail and a small SFT pilot demonstrates a clear gain.

---

### C8 — Part B model information explicitly excluded

**Potential contamination identified**

Part B contains a concrete model specification and serving benchmark. It would be tempting to reuse those values for Part C.

**Finding**

Part C is a separate scenario and does not specify that it uses the Part B model or serving stack.

**Revision**

Do not use Part B model size, L4 results, KV-cache arithmetic, or serving measurements as evidence for Part C. Any Part C compute estimate must be based only on Part C's stated constraints and clearly labelled assumptions.

---

### C9 — Quantitative planning

**Reviewer capacity**

Given:

```text
10 h/week × 3 weeks = 30 reviewer-hours
```

Planning assumption:

```text
2 min/response = 30 responses/hour
```

Therefore:

```text
30 × 30 = 900 response evaluations
```

Initial blind comparison:

```text
30 prompts
× 2 native-reviewed languages
× 3 conditions
= 180 response evaluations
```

Reviewer time:

```text
180 × 2 min
= 360 min
= 6 h
```

Remaining reviewer capacity:

```text
30 - 6 = 24 h
24 × 30 = 720 further evaluations
```

**Data planning assumption for rewriter**

```text
500 usable formal→casual pairs/language
× 6 languages
= 3,000 usable pairs
```

Assuming 200 source+target tokens/pair:

```text
3,000 × 200 = 600,000 tokens/epoch
```

At 3 epochs:

```text
600,000 × 3 = 1.8M token presentations
```

These are planning assumptions, not experimentally established minimum requirements.

**GPU-budget planning**

Assuming continuous A100 availability:

```text
14 × 24 = 336 GPU-hours
```

Because Part C provides no model architecture or measured training throughput, an exact training-hour number would be false precision.

Therefore:

```text
25% of 336 GPU-hours = 84 GPU-hours
```

was selected as a planning ceiling for an initial training commitment, with the remaining compute reserved for iteration and validation.

**Revision**

Use formulas and explicit assumptions rather than inventing exact A100 training times.

---

### C10 — Success metric selected

**Candidate metrics considered**

* casualness score
* 1–5 Likert rating
* pairwise preference
* casual + faithful binary pass

**Decision**

Use:

```text
PASS = casual AND faithful
```

Primary metric:

```text
casual-and-faithful pass rate
= PASS responses / reviewed responses
```

Chosen launch threshold:

```text
≥75% pass rate
```

The threshold is a predeclared decision rule, not an assignment-provided fact.

For the rewriter to justify its additional serving complexity:

```text
≥75% pass rate
AND
≥10 percentage-point improvement over prompt-only
```

---

### C11 — Day-1 experiment defined

**Objective**

Determine whether prompt engineering is sufficient and whether the additional complexity of a ≤1B rewriter is justified.

**Controlled inputs**

Use the same 30 prompts across all six languages.

**Conditions**

```text
C0 = current/default prompting

C1 = improved casual-register prompting

B  = C1 output followed by the ≤1B rewriter
```

**Human validation**

Hindi and Kannada receive blind native-speaker evaluation for:

```text
casual?
faithful?
PASS?
```

**Other four languages**

Tamil, Telugu, Bengali and Marathi receive structural/semantic sanity checks, explicitly marked as lower-confidence because native-speaker validation is unavailable.

**Revision**

Do not claim that the Day-1 experiment proves all six languages are correct. It is a decision gate for allocating additional resources.

---

### C12 — Kill criterion defined

**Problem with initial proposal**

An earlier idea used a fixed Day-8 cutoff. This was rejected because the assignment provides a two-week compute window and a three-week launch review, so the criterion should align with the resource boundary.

**Final rule**

By the end of Week 2:

```text
abandon B for a language if:
1. best tested configuration <75% casual-and-faithful pass rate
OR
2. B improves over prompt-only by <10 percentage points
```

If the rewriter does not justify its added complexity, fall back to prompt-only.

SFT is considered only if a prior SFT pilot has already demonstrated a clear quality gain and sufficient validation time remains.

---

### C13 — Final recommendation

**Conclusion**

Recommend:

```text
Prompt engineering across all six languages
+
selective ≤1B rewriter only where the prompt-only configuration
fails the predefined quality gate
+
SFT reserved as a fallback
```

**Why this strategy**

* It does not assume one technique is universally best.
* It uses the reviewer where native validation is available.
* It avoids unnecessary rewriter serving cost for languages that already pass.
* It avoids immediately modifying shared model weights before establishing that a weight-level intervention is necessary.
* It preserves the ability to escalate if prompt-only output is inadequate.
* It keeps the decision tied to explicit quality and resource thresholds rather than intuition.

**Final status**

Part C memo completed using only the Part C scenario, explicit assumptions, and derived planning arithmetic. No Part B model or serving measurements were used.
