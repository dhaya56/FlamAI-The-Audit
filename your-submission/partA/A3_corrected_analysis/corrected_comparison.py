from __future__ import annotations

import csv
import json
import statistics
import unicodedata
from pathlib import Path

import regex
from transformers import AutoTokenizer


# ---------------------------------------------------------------------
# Paths and configuration
# ---------------------------------------------------------------------

# File is:
# repo\your-submission\partA\A3_corrected_analysis\corrected_comparison.py
# parents[3] = repository root
ROOT = Path(__file__).resolve().parents[3]

CORPUS_DIR = (
    ROOT
    / "your-submission"
    / "partA"
    / "A1_corpus"
    / "eval_corpus"
)

OUTPUT_DIR = Path(__file__).resolve().parent

LANGUAGES = ["eng", "hin", "kan", "tam"]

TOKENIZERS = [
    ("GPT-2", "gpt2"),
    ("Sarvam-1", "sarvamai/sarvam-1"),
]

EXPECTED_SENTENCES = 997


# ---------------------------------------------------------------------
# Text measurement helpers
# ---------------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    """
    Read the A1 corpus and apply only NFC normalization.

    A3 corrected analysis intentionally does NOT:
    - lowercase text
    - strip internal whitespace
    - collapse whitespace
    """
    lines = []

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")

            if not line.strip():
                continue

            line = unicodedata.normalize("NFC", line)
            lines.append(line)

    return lines


def count_words(text: str) -> int:
    """
    Corrected whitespace-word denominator.

    split() treats runs of whitespace as one separator and
    does not create empty word fields from repeated spaces.
    """
    return len(text.split())


def count_graphemes(text: str) -> int:
    """
    Count Unicode extended grapheme clusters.

    This is a script-aware structural denominator, not a
    linguistic morpheme count.
    """
    return len(regex.findall(r"\X", text))


def count_bytes(text: str) -> int:
    """Count UTF-8 encoded bytes."""
    return len(text.encode("utf-8"))


# ---------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------

def load_corpus() -> dict[str, list[str]]:
    corpus = {}

    for lang in LANGUAGES:
        path = CORPUS_DIR / f"{lang}.txt"

        if not path.exists():
            raise FileNotFoundError(f"Missing corpus file: {path}")

        lines = read_lines(path)

        if len(lines) != EXPECTED_SENTENCES:
            raise ValueError(
                f"{lang}: expected {EXPECTED_SENTENCES} sentences, "
                f"found {len(lines)}"
            )

        corpus[lang] = lines

    # Verify language files remain aligned by position.
    for i in range(EXPECTED_SENTENCES):
        for lang in LANGUAGES:
            if not isinstance(corpus[lang][i], str):
                raise TypeError(
                    f"Unexpected non-string value at {lang}[{i}]"
                )

    return corpus


# ---------------------------------------------------------------------
# Tokenization and measurement
# ---------------------------------------------------------------------

def analyze_language(
    texts: list[str],
    tokenizer,
) -> dict:
    token_counts = []

    word_counts = []
    grapheme_counts = []
    byte_counts = []

    sentence_tok_word = []
    sentence_tok_grapheme = []
    sentence_tok_byte = []

    for text in texts:
        tokens = tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        token_count = len(tokens)
        word_count = count_words(text)
        grapheme_count = count_graphemes(text)
        byte_count = count_bytes(text)

        token_counts.append(token_count)
        word_counts.append(word_count)
        grapheme_counts.append(grapheme_count)
        byte_counts.append(byte_count)

        sentence_tok_word.append(
            token_count / word_count
        )

        sentence_tok_grapheme.append(
            token_count / grapheme_count
        )

        sentence_tok_byte.append(
            token_count / byte_count
        )

    total_tokens = sum(token_counts)
    total_words = sum(word_counts)
    total_graphemes = sum(grapheme_counts)
    total_bytes = sum(byte_counts)

    return {
        "sentences": len(texts),
        "total_tokens": total_tokens,
        "total_words": total_words,
        "total_graphemes": total_graphemes,
        "total_bytes": total_bytes,

        # Corpus-level ratios
        "corpus_tok_per_sentence": (
            total_tokens / len(texts)
        ),
        "corpus_tok_per_word": (
            total_tokens / total_words
        ),
        "corpus_tok_per_grapheme": (
            total_tokens / total_graphemes
        ),
        "corpus_tok_per_byte": (
            total_tokens / total_bytes
        ),

        # Distribution of sentence-level ratios
        "mean_sentence_tok_per_word": (
            statistics.mean(sentence_tok_word)
        ),
        "median_sentence_tok_per_word": (
            statistics.median(sentence_tok_word)
        ),
        "p95_sentence_tok_per_word": (
            statistics.quantiles(
                sentence_tok_word,
                n=100,
                method="inclusive",
            )[94]
        ),

        "mean_sentence_tok_per_grapheme": (
            statistics.mean(sentence_tok_grapheme)
        ),
        "median_sentence_tok_per_grapheme": (
            statistics.median(sentence_tok_grapheme)
        ),

        "mean_sentence_tok_per_byte": (
            statistics.mean(sentence_tok_byte)
        ),
        "median_sentence_tok_per_byte": (
            statistics.median(sentence_tok_byte)
        ),
    }


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("A3 Corrected Full-Corpus Comparison")
    print()
    print(f"Corpus: {CORPUS_DIR}")
    print(f"Languages: {', '.join(LANGUAGES)}")
    print(f"Sentences per language: {EXPECTED_SENTENCES}")
    print("Preprocessing: NFC only; original case and internal whitespace preserved")
    print("Word denominator: split()")
    print("Grapheme denominator: Unicode extended grapheme clusters (\\X)")
    print("Byte denominator: UTF-8 bytes")
    print("Special tokens: disabled")
    print("Aggregation: corpus totals plus sentence-level distributions")
    print()

    corpus = load_corpus()

    all_results = []

    for tokenizer_name, repo in TOKENIZERS:
        print("=" * 90)
        print(f"Tokenizer: {tokenizer_name}")
        print(f"Repository: {repo}")

        tokenizer = AutoTokenizer.from_pretrained(
            repo,
            use_fast=False,
        )

        candidate_results = {
            "tokenizer": tokenizer_name,
            "repository": repo,
            "vocab_size": len(tokenizer),
            "languages": {},
        }

        for lang in LANGUAGES:
            result = analyze_language(
                corpus[lang],
                tokenizer,
            )

            candidate_results["languages"][lang] = result

            print(
                f"{lang}: "
                f"tokens={result['total_tokens']} | "
                f"tok/sent={result['corpus_tok_per_sentence']:.6f} | "
                f"tok/word={result['corpus_tok_per_word']:.6f} | "
                f"tok/grapheme={result['corpus_tok_per_grapheme']:.6f} | "
                f"tok/byte={result['corpus_tok_per_byte']:.6f}"
            )

        # -------------------------------------------------------------
        # Relative workload vs aligned English
        # -------------------------------------------------------------

        eng_tokens = candidate_results["languages"]["eng"]["total_tokens"]

        for lang in LANGUAGES:
            candidate_results["languages"][lang][
                "token_ratio_vs_eng"
            ] = (
                candidate_results["languages"][lang]["total_tokens"]
                / eng_tokens
            )

        print()
        print("Token workload relative to English:")

        for lang in LANGUAGES:
            if lang == "eng":
                continue

            ratio = candidate_results["languages"][lang][
                "token_ratio_vs_eng"
            ]

            print(f"{lang}: {ratio:.6f}x")

        all_results.append(candidate_results)
        print()

    # -----------------------------------------------------------------
    # Save JSON
    # -----------------------------------------------------------------

    json_path = OUTPUT_DIR / "corrected_comparison_results.json"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # -----------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------

    csv_path = OUTPUT_DIR / "corrected_comparison_summary.csv"

    fields = [
        "tokenizer",
        "repository",
        "vocab_size",
        "language",
        "sentences",
        "total_tokens",
        "total_words",
        "total_graphemes",
        "total_bytes",
        "corpus_tok_per_sentence",
        "corpus_tok_per_word",
        "corpus_tok_per_grapheme",
        "corpus_tok_per_byte",
        "mean_sentence_tok_per_word",
        "median_sentence_tok_per_word",
        "p95_sentence_tok_per_word",
        "mean_sentence_tok_per_grapheme",
        "median_sentence_tok_per_grapheme",
        "mean_sentence_tok_per_byte",
        "median_sentence_tok_per_byte",
        "token_ratio_vs_eng",
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for candidate in all_results:
            for lang in LANGUAGES:
                result = candidate["languages"][lang]

                writer.writerow(
                    {
                        "tokenizer": candidate["tokenizer"],
                        "repository": candidate["repository"],
                        "vocab_size": candidate["vocab_size"],
                        "language": lang,
                        **result,
                    }
                )

    print("=" * 90)
    print("COMPARISON COMPLETE")
    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")


if __name__ == "__main__":
    main()