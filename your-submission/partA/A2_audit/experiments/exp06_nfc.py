from __future__ import annotations

import unicodedata

import tiktoken


ENCODER = tiktoken.get_encoding("gpt2")


def analyze(path: str, normalize_nfc: bool) -> dict:
    per_line_fertility = []
    per_line_tpc = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            if not line:
                continue

            if normalize_nfc:
                line = unicodedata.normalize("NFC", line)

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
        nfc = analyze(path, normalize_nfc=True)
        raw = analyze(path, normalize_nfc=False)

        fert_delta = raw["fertility"] - nfc["fertility"]
        fert_pct = fert_delta / nfc["fertility"] * 100

        tpc_delta = raw["tok_per_char"] - nfc["tok_per_char"]
        tpc_pct = tpc_delta / nfc["tok_per_char"] * 100

        results[lang] = {
            "nfc": nfc,
            "raw": raw,
        }

        print(lang)
        print(
            f"  nfc: fertility={nfc['fertility']:.6f}, "
            f"tok_per_char={nfc['tok_per_char']:.6f}"
        )
        print(
            f"  raw: fertility={raw['fertility']:.6f}, "
            f"tok_per_char={raw['tok_per_char']:.6f}"
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

    nfc_ratio = (
        results["hin"]["nfc"]["fertility"]
        / results["eng"]["nfc"]["fertility"]
    )

    raw_ratio = (
        results["hin"]["raw"]["fertility"]
        / results["eng"]["raw"]["fertility"]
    )

    ratio_delta = raw_ratio - nfc_ratio
    ratio_pct = ratio_delta / nfc_ratio * 100

    print("cross_language_ratio")
    print(f"  nfc={nfc_ratio:.6f}")
    print(f"  raw={raw_ratio:.6f}")
    print(f"  delta={ratio_delta:.6f} ({ratio_pct:.2f}%)")


if __name__ == "__main__":
    main()