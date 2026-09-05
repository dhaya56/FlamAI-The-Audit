from __future__ import annotations

import unicodedata

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def analyze(path: str) -> dict:
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            line = unicodedata.normalize("NFC", line).lower()
            lines.append(line)

    per_line_tokens_per_word = []
    per_line_tokens_per_sentence = []

    for line in lines:
        tokens = len(ENCODER.encode(line))
        words = len(line.split(" "))

        per_line_tokens_per_word.append(tokens / words)

        # Exactly one sentence is the denominator for this observation.
        per_line_tokens_per_sentence.append(tokens / 1)

    return {
        "sentences": len(lines),
        "tokens": sum(per_line_tokens_per_sentence),
        "tokens_per_word": (
            sum(per_line_tokens_per_word)
            / len(per_line_tokens_per_word)
        ),
        "tokens_per_sentence": (
            sum(per_line_tokens_per_sentence)
            / len(per_line_tokens_per_sentence)
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
        print(f"  sentences={result['sentences']}")
        print(f"  total_tokens={result['tokens']}")
        print(f"  tokens_per_word={result['tokens_per_word']:.6f}")
        print(
            f"  tokens_per_sentence="
            f"{result['tokens_per_sentence']:.6f}"
        )
        print()

    word_ratio = (
        results["hin"]["tokens_per_word"]
        / results["eng"]["tokens_per_word"]
    )

    sentence_ratio = (
        results["hin"]["tokens_per_sentence"]
        / results["eng"]["tokens_per_sentence"]
    )

    print("cross_language_ratio")
    print(f"  tokens_per_word={word_ratio:.6f}")
    print(f"  tokens_per_sentence={sentence_ratio:.6f}")
    print(f"  absolute_delta={sentence_ratio - word_ratio:.6f}")
    print(
        f"  relative_delta_pct="
        f"{(sentence_ratio - word_ratio) / word_ratio * 100:.2f}%"
    )


if __name__ == "__main__":
    main()