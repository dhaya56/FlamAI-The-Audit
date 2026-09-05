from pathlib import Path
import csv


HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "corrected_comparison_summary.csv"

GPT2_NAME = "GPT-2"
SARVAM_NAME = "Sarvam-1"

LANGUAGES = ["eng", "hin", "kan", "tam"]


rows = []

with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["language"] in LANGUAGES:
            rows.append(row)


data = {}

for row in rows:
    candidate = row["tokenizer"]
    language = row["language"]

    data[(candidate, language)] = {
        "total_tokens": int(row["total_tokens"]),
        "tok_per_sentence": float(row["corpus_tok_per_sentence"]),
        "tok_per_word": float(row["corpus_tok_per_word"]),
        "tok_per_grapheme": float(row["corpus_tok_per_grapheme"]),
        "tok_per_byte": float(row["corpus_tok_per_byte"]),
    }


print("A3 Direct Token Workload Comparison")
print()
print("Comparison: GPT-2 vs Sarvam-1")
print("Corpus: 997 aligned sentences per language")
print()

print(
    f"{'Language':10}"
    f"{'GPT-2 tokens':>15}"
    f"{'Sarvam tokens':>17}"
    f"{'Reduction':>14}"
    f"{'Reduction %':>14}"
)

print("-" * 70)


for lang in LANGUAGES:
    gpt2_tokens = data[(GPT2_NAME, lang)]["total_tokens"]
    sarvam_tokens = data[(SARVAM_NAME, lang)]["total_tokens"]

    reduction = gpt2_tokens - sarvam_tokens
    reduction_pct = (
        reduction / gpt2_tokens
    ) * 100

    print(
        f"{lang:10}"
        f"{gpt2_tokens:15d}"
        f"{sarvam_tokens:17d}"
        f"{reduction:14d}"
        f"{reduction_pct:13.2f}%"
    )


print()
print("Sarvam token count as a fraction of GPT-2:")
print()

for lang in LANGUAGES:
    gpt2_tokens = data[(GPT2_NAME, lang)]["total_tokens"]
    sarvam_tokens = data[(SARVAM_NAME, lang)]["total_tokens"]

    fraction = sarvam_tokens / gpt2_tokens

    print(f"{lang}: {fraction:.6f}x")


print()
print("Sentence workload:")
print()

for lang in LANGUAGES:
    gpt2_tps = data[(GPT2_NAME, lang)]["tok_per_sentence"]
    sarvam_tps = data[(SARVAM_NAME, lang)]["tok_per_sentence"]

    reduction_pct = (
        (gpt2_tps - sarvam_tps)
        / gpt2_tps
    ) * 100

    print(
        f"{lang}: "
        f"GPT-2={gpt2_tps:.6f} tok/sentence, "
        f"Sarvam={sarvam_tps:.6f} tok/sentence, "
        f"reduction={reduction_pct:.2f}%"
    )