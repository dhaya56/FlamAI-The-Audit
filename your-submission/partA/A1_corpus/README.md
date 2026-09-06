# A1 — Multilingual Evaluation Corpus

## Dataset

**Dataset:** FLORES+
**Dataset repository:** `openlanguagedata/flores_plus`
**Pinned revision:** `5fec6c13f9e5a4db2f745d4ec0d7c9721ddc4f06`
**Split:** `dev`

The evaluation set contains four languages:

| Language | FLORES+ code | Family / script            |
| -------- | ------------ | -------------------------- |
| English  | `eng_Latn`   | Indo-European / Latin      |
| Hindi    | `hin_Deva`   | Indo-European / Devanagari |
| Kannada  | `kan_Knda`   | Dravidian / Kannada        |
| Tamil    | `tam_Taml`   | Dravidian / Tamil          |

Each language contains **997 sentences**, giving **3,988 language-sentences** in total. The four language splits contain the same **997 sentence IDs**, providing sentence-level alignment across the selected languages.

## Corpus domain

Each language contains the same domain distribution:

* Wikibooks: 301 sentences
* Wikinews: 348 sentences
* Wikivoyage: 348 sentences

This gives a controlled multilingual evaluation set in which the same underlying sentence IDs are available across all four languages.

## Preprocessing

The preparation script performs **Unicode NFC normalization only**.

The following are intentionally preserved:

* original case
* punctuation
* whitespace
* sentence text

No lowercasing, punctuation removal, transliteration, whitespace collapsing, or other tokenization-specific preprocessing is performed during corpus preparation.

The exact dataset revision is pinned in `prepare_corpus.py` so that the experiment can be reproduced against the same dataset snapshot.

## Alignment validation

The corpus was validated locally before preparation.

Observed results:

```text
row_counts:
eng_Latn 997
hin_Deva 997
kan_Knda 997
tam_Taml 997

unique_ids:
eng_Latn 997
hin_Deva 997
kan_Knda 997
tam_Taml 997

same_id_set: True
```

Thus, all four selected language splits contain 997 unique sentence IDs and the same ID set.

## Why this corpus was chosen

The starter corpus supplied with the assignment contains only approximately ten sentences per language and is explicitly intended as a smoke-test corpus. A larger parallel evaluation set is required for a meaningful cross-language tokenizer comparison.

FLORES+ provides a substantially larger evaluation set with four required languages, including Hindi and two Dravidian languages, while maintaining aligned sentence IDs across languages. The dataset therefore allows the corrected analysis in A3 to compare tokenizer behavior on corresponding multilingual content rather than relying only on the small starter files.

## What this corpus cannot tell us

This corpus is an evaluation benchmark, not a sample of our production traffic. Its 997 sentences per language and its source domains do not establish how tokenizer behavior will look on the full distribution of real user requests. In particular, the measurements should not be interpreted as a complete characterization of conversational traffic, code-mixed language, user-generated spelling variation, domain-specific terminology, very long contexts, or other production distributions that may differ from this evaluation set. The results therefore support a controlled comparison of the selected languages and tokenizers, but they do not by themselves guarantee production cost ratios or routing performance.

## Reproduction

From the repository root, authenticate with Hugging Face and run:

```text
python your-submission\partA\A1_corpus\prepare_corpus.py
```

The script validates the expected row counts and cross-language ID alignment before materializing the local evaluation files.
