from pathlib import Path
import csv


HERE = Path(__file__).resolve().parent

LEGACY_VALUES = {
    "GPT-2": {
        "eng": 1.282531,
        "hin": 7.823186,
        "kan": 22.148288,
        "tam": 24.733182,
    },
    "Sarvam-1": {
        "eng": 1.460539,
        "hin": 1.400991,
        "kan": 2.348439,
        "tam": 2.150157,
    },
}

CORRECTED_CSV = HERE / "corrected_comparison_summary.csv"

LANGUAGES = ["eng", "hin", "kan", "tam"]


# Load corrected corpus-level tok/word values.
corrected = {}

with CORRECTED_CSV.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        tokenizer = row["tokenizer"]
        language = row["language"]

        corrected[(tokenizer, language)] = float(
            row["corpus_tok_per_word"]
        )


print("A3 Legacy -> Corrected Method Comparison")
print()
print("Metric: corpus-level tokens per whitespace-separated word")
print("Change = corrected - legacy")
print("Percent change = (corrected - legacy) / legacy")
print()

for tokenizer in ["GPT-2", "Sarvam-1"]:
    print("=" * 75)
    print(tokenizer)

    for lang in LANGUAGES:
        legacy = LEGACY_VALUES[tokenizer][lang]
        new = corrected[(tokenizer, lang)]

        delta = new - legacy
        pct = (delta / legacy) * 100

        print(
            f"{lang}: "
            f"legacy={legacy:.6f} | "
            f"corrected={new:.6f} | "
            f"delta={delta:+.6f} | "
            f"change={pct:+.2f}%"
        )

    print()


print("=" * 75)
print("English-relative workload change")

for tokenizer in ["GPT-2", "Sarvam-1"]:
    legacy_eng = LEGACY_VALUES[tokenizer]["eng"]
    corrected_eng = corrected[(tokenizer, "eng")]

    print()
    print(tokenizer)

    for lang in ["hin", "kan", "tam"]:
        legacy_ratio = (
            LEGACY_VALUES[tokenizer][lang]
            / legacy_eng
        )

        corrected_ratio = (
            corrected[(tokenizer, lang)]
            / corrected_eng
        )

        delta = corrected_ratio - legacy_ratio
        pct = (delta / legacy_ratio) * 100

        print(
            f"{lang}: "
            f"legacy={legacy_ratio:.6f}x | "
            f"corrected={corrected_ratio:.6f}x | "
            f"change={pct:+.2f}%"
        )