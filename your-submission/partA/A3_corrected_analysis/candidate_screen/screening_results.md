# A3 Candidate Screening — 100-Sentence Candidate Benchmark

## Objective

After the initial tokenizer access screening, five reproducibly loadable candidates were evaluated on a deterministic 100-sentence-per-language subset of the A1 FLORES+ evaluation corpus.

The purpose of this experiment is candidate screening only. It is not the final A3 tokenizer comparison and does not by itself establish a final tokenizer choice.

## Evaluation Corpus

* Dataset: A1 FLORES+ dev evaluation corpus
* Languages: English, Hindi, Kannada, Tamil
* Sentences per language: 100
* Total evaluated sentences: 400
* Sentences are aligned by the same FLORES+ sentence IDs across languages.

## Preprocessing and Measurement

* Original sentence text preserved.
* Line endings removed only.
* No lowercasing.
* Special tokens disabled using `add_special_tokens=False`.
* Whitespace word count uses Python `split()`.
* Grapheme count uses Unicode extended grapheme clusters (`\X`).
* UTF-8 byte count uses `len(text.encode("utf-8"))`.

Command used:

`python your-submission\partA\A3_corrected_analysis\candidate_screen\candidate_screen_benchmark.py`

## Raw Screening Results

### GPT-2

Repository: `gpt2`
Vocabulary size: 50,257

| Language | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte | Relative to English |
| -------- | -----------: | -------: | -----------: | -------: | ------------------: |
| English  |       27.960 |    1.259 |       0.2103 |   0.2101 |              1.000x |
| Hindi    |      204.430 |    7.744 |       2.3055 |   0.5924 |              7.312x |
| Kannada  |      369.570 |   21.487 |       4.0088 |   0.9766 |             13.218x |
| Tamil    |      421.410 |   24.067 |       4.1753 |   0.9931 |             15.072x |

### IndicBERTv2-SS

Repository: `ai4bharat/IndicBERTv2-SS`
Vocabulary size: 200,000

| Language | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte | Relative to English |
| -------- | -----------: | -------: | -----------: | -------: | ------------------: |
| English  |       30.260 |    1.362 |       0.2276 |   0.2274 |              1.000x |
| Hindi    |       32.850 |    1.244 |       0.3705 |   0.0952 |              1.086x |
| Kannada  |      107.960 |    6.277 |       1.1711 |   0.2853 |              3.568x |
| Tamil    |      137.320 |    7.842 |       1.3605 |   0.3236 |              4.538x |

### Sarvam-1

Repository: `sarvamai/sarvam-1`
Vocabulary size: 68,096

| Language | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte | Relative to English |
| -------- | -----------: | -------: | -----------: | -------: | ------------------: |
| English  |       33.790 |    1.521 |       0.2541 |   0.2540 |              1.000x |
| Hindi    |       37.280 |    1.412 |       0.4204 |   0.1080 |              1.103x |
| Kannada  |       42.170 |    2.452 |       0.4574 |   0.1114 |              1.248x |
| Tamil    |       38.810 |    2.216 |       0.3845 |   0.0915 |              1.149x |

### Qwen2.5-7B

Repository: `Qwen/Qwen2.5-7B`
Vocabulary size: 151,665

| Language | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte | Relative to English |
| -------- | -----------: | -------: | -----------: | -------: | ------------------: |
| English  |       29.070 |    1.309 |       0.2186 |   0.2185 |              1.000x |
| Hindi    |      124.960 |    4.733 |       1.4093 |   0.3621 |              4.299x |
| Kannada  |      194.650 |   11.317 |       2.1114 |   0.5144 |              6.696x |
| Tamil    |      171.660 |    9.804 |       1.7008 |   0.4045 |              5.905x |

### XLM-R

Repository: `FacebookAI/xlm-roberta-base`
Vocabulary size: 250,002

| Language | Tok/sentence | Tok/word | Tok/grapheme | Tok/byte | Relative to English |
| -------- | -----------: | -------: | -----------: | -------: | ------------------: |
| English  |       31.200 |    1.405 |       0.2347 |   0.2345 |              1.000x |
| Hindi    |       39.890 |    1.511 |       0.4499 |   0.1156 |              1.279x |
| Kannada  |       43.100 |    2.506 |       0.4675 |   0.1139 |              1.381x |
| Tamil    |       42.770 |    2.443 |       0.4238 |   0.1008 |              1.371x |

## Initial Observation

The screening shows large differences in Indic token workload across tokenizer families.

GPT-2 produces substantially higher token counts for Hindi, Kannada, and Tamil than the other screened candidates. Its relative token workload versus English is 7.312x for Hindi, 13.218x for Kannada, and 15.072x for Tamil.

Sarvam-1 and XLM-R show the lowest relative token workload among the screened candidates across the three Indic languages. IndicBERTv2-SS improves substantially over GPT-2 but remains higher for Kannada and Tamil. Qwen2.5-7B also improves over GPT-2 but retains materially higher Indic token workload than Sarvam-1 and XLM-R.

## Interpretation

These results are screening evidence only.

The results do not yet establish which tokenizer should drive the final A3 routing recommendation. In particular, the choice of denominator affects the interpretation of token workload, so a separate denominator comparison is required before selecting the final multilingual/Indic-aware comparator.

The machine-readable benchmark outputs are:

* `candidate_screen_results.json`
* `candidate_screen_summary.csv`

The next experiment will compare candidate performance using aggregated `tok/word` and `tok/UTF-8 byte` measurements before making the final candidate selection.

## Reproducibility

The benchmark implementation is:

`candidate_screen_benchmark.py`

The candidate pool and access-screen evidence are documented in:

`candidate_screen.md`

## Candidate Ranking Analysis

### Experiment

The raw 100-sentence-per-language screening results were aggregated across the three Indic languages (Hindi, Kannada, Tamil) using the candidate-screen CSV output.

Command:

`python your-submission\partA\A3_corrected_analysis\candidate_screen\analyze_screen.py`

Aggregation:

* Simple mean across Hindi, Kannada, and Tamil.
* Primary ranking metric: mean tokens per whitespace-separated word.
* Secondary ranking metric: mean tokens per UTF-8 byte.

### Result

| Candidate      | Mean tok/word | Mean tok/byte | Mean Indic vs English |
| -------------- | ------------: | ------------: | --------------------: |
| Sarvam-1       |        2.0268 |        0.1036 |               1.1666x |
| XLM-R          |        2.1531 |        0.1101 |               1.3436x |
| IndicBERTv2-SS |        5.1211 |        0.2347 |               3.0638x |
| Qwen2.5-7B     |        8.6179 |        0.4270 |               5.6332x |
| GPT-2          |       17.7657 |        0.8540 |              11.8671x |

### Interpretation

Sarvam-1 ranks first under both the primary mean `tokens/word` criterion and the secondary mean `tokens/UTF-8 byte` criterion.

XLM-R ranks second under both criteria and is substantially stronger than IndicBERTv2-SS and Qwen2.5-7B on this screening corpus.

Therefore, Sarvam-1 is selected as the multilingual/Indic-aware comparator for the final A3 comparison, while XLM-R is retained as a screening reference.

This selection is based on measured behavior on the same aligned A1 corpus rather than on a pre-declared preference for a particular tokenizer family.

### Scope

This ranking is based on the deterministic 100-sentence-per-language screening subset. The full A3 comparison will use all 997 aligned sentences per language.

The screening does not establish that Sarvam-1 is globally the best tokenizer. It establishes that, among the candidates reproducibly evaluated here, Sarvam-1 had the lowest observed mean `tokens/word` and `tokens/UTF-8 byte` across Hindi, Kannada, and Tamil.

