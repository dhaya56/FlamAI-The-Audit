from __future__ import annotations

import statistics
import unicodedata

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")

CORPORA = {
    "eng": "your-submission/partA/A1_corpus/eval_corpus/eng.txt",
    "hin": "your-submission/partA/A1_corpus/eval_corpus/hin.txt",
    "kan": "your-submission/partA/A1_corpus/eval_corpus/kan.txt",
    "tam": "your-submission/partA/A1_corpus/eval_corpus/tam.txt",
}


def load_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [
            unicodedata.normalize("NFC", raw.rstrip("\r\n"))
            for raw in f
        ]

    if len(lines) != 997:
        raise ValueError(f"{path}: expected 997 lines, got {len(lines)}")

    if any(not line.strip() for line in lines):
        raise ValueError(f"{path}: empty sentence found")

    return lines


def token_counts(lines: list[str]) -> list[int]:
    counts = []

    for line in lines:
        line = line.lower()
        counts.append(len(ENCODER.encode(line)))

    return counts


def main() -> None:
    texts = {
        lang: load_lines(path)
        for lang, path in CORPORA.items()
    }

    token_counts_by_lang = {
        lang: token_counts(lines)
        for lang, lines in texts.items()
    }

    print("paired_token_workload_vs_english")

    english = token_counts_by_lang["eng"]

    for lang in ["hin", "kan", "tam"]:
        target = token_counts_by_lang[lang]

        # Each index represents the same FLORES+ sentence ID.
        ratios = [
            target_tokens / english_tokens
            for target_tokens, english_tokens in zip(target, english)
            if english_tokens > 0
        ]

        mean_ratio = statistics.mean(ratios)
        median_ratio = statistics.median(ratios)

        print(lang)
        print(f"  aligned_pairs={len(ratios)}")
        print(f"  mean_target_to_english={mean_ratio:.6f}x")
        print(f"  median_target_to_english={median_ratio:.6f}x")
        print(f"  min_ratio={min(ratios):.6f}x")
        print(f"  max_ratio={max(ratios):.6f}x")
        print(f"  stdev_ratio={statistics.stdev(ratios):.6f}")
        print()

    print("alternative_corpus_level_ratio")

    total_eng = sum(english)

    for lang in ["hin", "kan", "tam"]:
        total_target = sum(token_counts_by_lang[lang])
        ratio = total_target / total_eng

        print(f"{lang}: {ratio:.6f}x")


if __name__ == "__main__":
    main()