from __future__ import annotations

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
        raise ValueError(
            f"{path}: expected 997 lines, got {len(lines)}"
        )

    if any(not line.strip() for line in lines):
        raise ValueError(f"{path}: empty sentence found")

    return lines


def analyze(path: str) -> dict[str, float]:
    lines = load_lines(path)

    per_line_tok_per_word = []
    per_line_tokens = []

    for line in lines:
        # Preserve the preprocessing used in the v0 benchmark.
        line = line.lower()

        tokens = len(ENCODER.encode(line))
        words = len(line.split(" "))

        per_line_tok_per_word.append(tokens / words)
        per_line_tokens.append(tokens)

    return {
        "tokens_total": sum(per_line_tokens),
        "tok_per_word": (
            sum(per_line_tok_per_word)
            / len(per_line_tok_per_word)
        ),
        "tok_per_sentence": (
            sum(per_line_tokens)
            / len(per_line_tokens)
        ),
    }


def main() -> None:
    results = {}

    for lang, path in CORPORA.items():
        results[lang] = analyze(path)

    print("absolute_metrics")

    for lang in CORPORA:
        result = results[lang]
        print(
            f"{lang}: "
            f"tokens={result['tokens_total']:.0f}, "
            f"tok/word={result['tok_per_word']:.6f}, "
            f"tok/sentence={result['tok_per_sentence']:.6f}"
        )

    print()
    print("language_ratio_vs_english")

    for lang in ["hin", "kan", "tam"]:
        word_ratio = (
            results[lang]["tok_per_word"]
            / results["eng"]["tok_per_word"]
        )

        sentence_ratio = (
            results[lang]["tok_per_sentence"]
            / results["eng"]["tok_per_sentence"]
        )

        print(lang)
        print(f"  tok_per_word={word_ratio:.6f}")
        print(f"  tok_per_sentence={sentence_ratio:.6f}")
        print()


if __name__ == "__main__":
    main()