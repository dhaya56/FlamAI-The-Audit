from __future__ import annotations

import unicodedata

import regex
import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def analyze(path: str) -> dict:
    per_line_codepoint = []
    per_line_grapheme = []
    per_line_byte = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            line = unicodedata.normalize("NFC", line).lower()

            tokens = len(ENCODER.encode(line))

            codepoints = len(line)
            graphemes = len(regex.findall(r"\X", line))
            utf8_bytes = len(line.encode("utf-8"))

            per_line_codepoint.append(tokens / codepoints)
            per_line_grapheme.append(tokens / graphemes)
            per_line_byte.append(tokens / utf8_bytes)

    return {
        "tok_per_codepoint": (
            sum(per_line_codepoint) / len(per_line_codepoint)
        ),
        "tok_per_grapheme": (
            sum(per_line_grapheme) / len(per_line_grapheme)
        ),
        "tok_per_byte": (
            sum(per_line_byte) / len(per_line_byte)
        ),
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

        print(lang)
        print(
            f"  tok_per_codepoint="
            f"{result['tok_per_codepoint']:.6f}"
        )
        print(
            f"  tok_per_grapheme="
            f"{result['tok_per_grapheme']:.6f}"
        )
        print(
            f"  tok_per_byte="
            f"{result['tok_per_byte']:.6f}"
        )
        print()

    ratios = {
        "codepoint": (
            results["hin"]["tok_per_codepoint"]
            / results["eng"]["tok_per_codepoint"]
        ),
        "grapheme": (
            results["hin"]["tok_per_grapheme"]
            / results["eng"]["tok_per_grapheme"]
        ),
        "byte": (
            results["hin"]["tok_per_byte"]
            / results["eng"]["tok_per_byte"]
        ),
    }

    print("cross_language_ratio")
    for metric, ratio in ratios.items():
        print(f"  {metric}={ratio:.6f}")

    baseline = ratios["codepoint"]

    print()
    print("relative_change_vs_codepoint")
    for metric, ratio in ratios.items():
        if metric == "codepoint":
            continue

        delta = ratio - baseline
        pct = delta / baseline * 100

        print(
            f"  {metric}: delta={delta:.6f} "
            f"({pct:.2f}%)"
        )


if __name__ == "__main__":
    main()