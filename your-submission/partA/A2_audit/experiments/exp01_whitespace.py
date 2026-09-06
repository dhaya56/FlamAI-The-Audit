from pathlib import Path
import unicodedata

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def analyze(path: str, use_python_whitespace_split: bool) -> dict:
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            line = unicodedata.normalize("NFC", line).lower()
            lines.append(line)

    per_line_fertility = []

    for line in lines:
        tokens = len(ENCODER.encode(line))

        if use_python_whitespace_split:
            words = len(line.split())
        else:
            words = len(line.split(" "))

        per_line_fertility.append(tokens / words)

    fertility = sum(per_line_fertility) / len(per_line_fertility)

    return {
        "lines": len(lines),
        "fertility": fertility,
    }


def main() -> None:
    corpora = {
        "eng": "starter_kit/corpus_sample/eng_sample.txt",
        "hin": "starter_kit/corpus_sample/hin_sample.txt",
    }

    for lang, path in corpora.items():
        original = analyze(path, use_python_whitespace_split=False)
        corrected = analyze(path, use_python_whitespace_split=True)

        delta = corrected["fertility"] - original["fertility"]
        pct = delta / original["fertility"] * 100

        print(lang)
        print(f"  lines={original['lines']}")
        print(f"  original_split_fertility={original['fertility']:.6f}")
        print(f"  whitespace_split_fertility={corrected['fertility']:.6f}")
        print(f"  absolute_delta={delta:.6f}")
        print(f"  relative_delta_pct={pct:.2f}%")
        print()


if __name__ == "__main__":
    main()