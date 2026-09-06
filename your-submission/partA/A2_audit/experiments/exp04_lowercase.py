from __future__ import annotations

import unicodedata

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def analyze(path: str, lowercase: bool) -> dict:
    per_line_fertility = []
    per_line_tpc = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            line = unicodedata.normalize("NFC", line)

            if lowercase:
                line = line.lower()

            tokens = len(ENCODER.encode(line))
            words = len(line.split(" "))
            chars = len(line)

            per_line_fertility.append(tokens / words)
            per_line_tpc.append(tokens / chars)

    return {
        "fertility": sum(per_line_fertility) / len(per_line_fertility),
        "tok_per_char": sum(per_line_tpc) / len(per_line_tpc),
    }


def main() -> None:
    corpora = {
        "eng": "starter_kit/corpus_sample/eng_sample.txt",
        "hin": "starter_kit/corpus_sample/hin_sample.txt",
    }

    results = {}

    for lang, path in corpora.items():
        original = analyze(path, lowercase=True)
        no_lower = analyze(path, lowercase=False)

        fert_delta = no_lower["fertility"] - original["fertility"]
        fert_pct = fert_delta / original["fertility"] * 100

        tpc_delta = no_lower["tok_per_char"] - original["tok_per_char"]
        tpc_pct = tpc_delta / original["tok_per_char"] * 100

        results[lang] = {
            "lower": original,
            "no_lower": no_lower,
        }

        print(lang)
        print(
            f"  lower:    fertility={original['fertility']:.6f}, "
            f"tok_per_char={original['tok_per_char']:.6f}"
        )
        print(
            f"  no_lower: fertility={no_lower['fertility']:.6f}, "
            f"tok_per_char={no_lower['tok_per_char']:.6f}"
        )
        print(
            f"  fertility_delta={fert_delta:.6f} "
            f"({fert_pct:.2f}%)"
        )
        print(
            f"  tok_per_char_delta={tpc_delta:.6f} "
            f"({tpc_pct:.2f}%)"
        )
        print()

    lower_ratio = (
        results["hin"]["lower"]["fertility"]
        / results["eng"]["lower"]["fertility"]
    )

    no_lower_ratio = (
        results["hin"]["no_lower"]["fertility"]
        / results["eng"]["no_lower"]["fertility"]
    )

    ratio_delta = no_lower_ratio - lower_ratio
    ratio_pct = ratio_delta / lower_ratio * 100

    print("cross_language_ratio")
    print(f"  lower={lower_ratio:.6f}")
    print(f"  no_lower={no_lower_ratio:.6f}")
    print(f"  delta={ratio_delta:.6f} ({ratio_pct:.2f}%)")


if __name__ == "__main__":
    main()