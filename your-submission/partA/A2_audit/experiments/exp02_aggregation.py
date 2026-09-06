from __future__ import annotations

import unicodedata
from pathlib import Path

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def load_lines(path: str) -> list[str]:
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            lines.append(unicodedata.normalize("NFC", line).lower())

    return lines


def analyze(path: str) -> dict:
    lines = load_lines(path)

    per_line_fertility = []
    total_tokens = 0
    total_words = 0

    for line in lines:
        tokens = len(ENCODER.encode(line))
        words = len(line.split(" "))

        per_line_fertility.append(tokens / words)

        total_tokens += tokens
        total_words += words

    macro_average = sum(per_line_fertility) / len(per_line_fertility)
    corpus_ratio = total_tokens / total_words

    return {
        "lines": len(lines),
        "total_tokens": total_tokens,
        "total_words": total_words,
        "macro_average": macro_average,
        "corpus_ratio": corpus_ratio,
    }


def main() -> None:
    corpora = {
        "eng": "starter_kit/corpus_sample/eng_sample.txt",
        "hin": "starter_kit/corpus_sample/hin_sample.txt",
    }

    results = {}

    for lang, path in corpora.items():
        result = analyze(path)
        results[lang] = result

        delta = result["corpus_ratio"] - result["macro_average"]
        pct = delta / result["macro_average"] * 100

        print(lang)
        print(f"  lines={result['lines']}")
        print(f"  total_tokens={result['total_tokens']}")
        print(f"  total_words={result['total_words']}")
        print(f"  per_line_average={result['macro_average']:.6f}")
        print(f"  corpus_level_ratio={result['corpus_ratio']:.6f}")
        print(f"  absolute_delta={delta:.6f}")
        print(f"  relative_delta_pct={pct:.2f}%")
        print()

    macro_ratio = results["hin"]["macro_average"] / results["eng"]["macro_average"]
    corpus_ratio = results["hin"]["corpus_ratio"] / results["eng"]["corpus_ratio"]

    print("cross_language_ratio")
    print(f"  per_line_average_method={macro_ratio:.6f}")
    print(f"  corpus_level_ratio_method={corpus_ratio:.6f}")
    print(f"  absolute_delta={corpus_ratio - macro_ratio:.6f}")
    print(
        f"  relative_delta_pct="
        f"{(corpus_ratio - macro_ratio) / macro_ratio * 100:.2f}%"
    )


if __name__ == "__main__":
    main()