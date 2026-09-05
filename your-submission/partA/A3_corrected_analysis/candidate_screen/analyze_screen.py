from pathlib import Path
import csv
from collections import defaultdict

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "candidate_screen_summary.csv"

INDIC_LANGS = {"hin", "kan", "tam"}

rows = []

with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["language"] in INDIC_LANGS:
            rows.append(row)

grouped = defaultdict(list)

for row in rows:
    grouped[row["candidate"]].append(row)

print("A3 candidate screen comparison")
print("Indic languages: Hindi, Kannada, Tamil")
print("Aggregation: simple mean of the three language-level metrics")
print()

results = []

for candidate, candidate_rows in grouped.items():
    mean_tok_word = sum(
        float(r["tok_per_word"]) for r in candidate_rows
    ) / len(candidate_rows)

    mean_tok_byte = sum(
        float(r["tok_per_byte"]) for r in candidate_rows
    ) / len(candidate_rows)

    mean_ratio_vs_eng = sum(
        float(r["token_ratio_vs_eng"]) for r in candidate_rows
    ) / len(candidate_rows)

    results.append(
        (
            candidate,
            mean_tok_word,
            mean_tok_byte,
            mean_ratio_vs_eng,
        )
    )

results.sort(key=lambda x: (x[1], x[2]))

print(
    f"{'Candidate':25}"
    f"{'Mean tok/word':>16}"
    f"{'Mean tok/byte':>16}"
    f"{'Mean vs-Eng':>16}"
)

print("-" * 73)

for candidate, tok_word, tok_byte, ratio in results:
    print(
        f"{candidate:25}"
        f"{tok_word:16.4f}"
        f"{tok_byte:16.4f}"
        f"{ratio:16.4f}x"
    )

print()
print("Ranking criterion:")
print("Primary: lower mean tok/word")
print("Secondary: lower mean tok/byte")