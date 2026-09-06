from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

import regex
from transformers import AutoTokenizer


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

CORPUS_DIR = (
    ROOT
    / "partA"
    / "A1_corpus"
    / "eval_corpus"
)

OUTPUT_DIR = Path(__file__).resolve().parent

# Deterministic screening subset: first 100 aligned FLORES+ sentence IDs.
N_SENTENCES = 100

LANGUAGES = ["eng", "hin", "kan", "tam"]

CANDIDATES = [
    ("GPT-2", "gpt2"),
    ("IndicBERTv2-SS", "ai4bharat/IndicBERTv2-SS"),
    ("Sarvam-1", "sarvamai/sarvam-1"),
    ("Qwen2.5-7B", "Qwen/Qwen2.5-7B"),
    ("XLM-R", "FacebookAI/xlm-roberta-base"),
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    """Read non-empty corpus lines using the A1 NFC preprocessing."""
    lines = []

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            lines.append(line)

    return lines


def grapheme_count(text: str) -> int:
    """Count Unicode extended grapheme clusters."""
    return len(regex.findall(r"\X", text))


def word_count(text: str) -> int:
    """Whitespace-separated word count."""
    return len(text.split())


def load_corpus() -> dict[str, list[str]]:
    corpus = {}

    for lang in LANGUAGES:
        path = CORPUS_DIR / f"{lang}.txt"

        if not path.exists():
            raise FileNotFoundError(f"Missing corpus file: {path}")

        lines = read_lines(path)

        if len(lines) < N_SENTENCES:
            raise ValueError(
                f"{lang}: expected at least {N_SENTENCES} lines, "
                f"found {len(lines)}"
            )

        corpus[lang] = lines[:N_SENTENCES]

    # Alignment sanity check: same number of sentences.
    counts = {lang: len(corpus[lang]) for lang in LANGUAGES}

    if len(set(counts.values())) != 1:
        raise ValueError(f"Language sentence counts do not match: {counts}")

    return corpus


def encode_texts(tokenizer, texts: list[str]) -> list[int]:
    return [
        len(
            tokenizer.encode(
                text,
                add_special_tokens=False,
            )
        )
        for text in texts
    ]


# ---------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------

def main():
    corpus = load_corpus()

    print("A3 tokenizer screening benchmark")
    print(f"Corpus directory: {CORPUS_DIR}")
    print(f"Sentences per language: {N_SENTENCES}")
    print(f"Languages: {', '.join(LANGUAGES)}")
    print("Preprocessing: original text preserved; line endings removed only")
    print("Special tokens: disabled")
    print()

    all_results = []

    for candidate_name, repo in CANDIDATES:
        print("=" * 80)
        print(f"{candidate_name}: {repo}")

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                repo,
                use_fast=False,
            )
        except Exception as exc:
            print(f"LOAD FAILED: {type(exc).__name__}: {exc}")
            continue

        vocab_size = len(tokenizer)

        language_results = {}

        for lang in LANGUAGES:
            texts = corpus[lang]
            token_counts = encode_texts(tokenizer, texts)

            total_tokens = sum(token_counts)
            total_words = sum(word_count(text) for text in texts)
            total_graphemes = sum(grapheme_count(text) for text in texts)
            total_bytes = sum(
                len(text.encode("utf-8"))
                for text in texts
            )

            tok_per_sentence = total_tokens / len(texts)
            tok_per_word = total_tokens / total_words
            tok_per_grapheme = total_tokens / total_graphemes
            tok_per_byte = total_tokens / total_bytes

            language_results[lang] = {
                "sentences": len(texts),
                "tokens": total_tokens,
                "words": total_words,
                "graphemes": total_graphemes,
                "bytes": total_bytes,
                "tok_per_sentence": tok_per_sentence,
                "tok_per_word": tok_per_word,
                "tok_per_grapheme": tok_per_grapheme,
                "tok_per_byte": tok_per_byte,
            }

        eng_tokens = language_results["eng"]["tokens"]

        for lang in LANGUAGES:
            result = language_results[lang]
            result["token_ratio_vs_eng"] = (
                result["tokens"] / eng_tokens
            )

        # Print compact candidate summary.
        print(f"Vocab size: {vocab_size}")

        for lang in LANGUAGES:
            r = language_results[lang]
            print(
                f"{lang}: "
                f"tok/sent={r['tok_per_sentence']:.3f} | "
                f"tok/word={r['tok_per_word']:.3f} | "
                f"tok/grapheme={r['tok_per_grapheme']:.4f} | "
                f"tok/byte={r['tok_per_byte']:.4f} | "
                f"vs_eng={r['token_ratio_vs_eng']:.3f}x"
            )

        all_results.append(
            {
                "candidate": candidate_name,
                "repo": repo,
                "vocab_size": vocab_size,
                "results": language_results,
            }
        )

        print()

    # -----------------------------------------------------------------
    # Save machine-readable results
    # -----------------------------------------------------------------

    json_path = OUTPUT_DIR / "candidate_screen_results.json"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # -----------------------------------------------------------------
    # Save compact CSV summary
    # -----------------------------------------------------------------

    csv_path = OUTPUT_DIR / "candidate_screen_summary.csv"

    fields = [
        "candidate",
        "repo",
        "vocab_size",
        "language",
        "sentences",
        "tokens",
        "words",
        "graphemes",
        "bytes",
        "tok_per_sentence",
        "tok_per_word",
        "tok_per_grapheme",
        "tok_per_byte",
        "token_ratio_vs_eng",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for candidate in all_results:
            for lang in LANGUAGES:
                r = candidate["results"][lang]

                writer.writerow(
                    {
                        "candidate": candidate["candidate"],
                        "repo": candidate["repo"],
                        "vocab_size": candidate["vocab_size"],
                        "language": lang,
                        **r,
                    }
                )

    print("=" * 80)
    print("SCREEN COMPLETE")
    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")


if __name__ == "__main__":
    main()
