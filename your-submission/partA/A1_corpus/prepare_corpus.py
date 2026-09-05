from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

from datasets import load_dataset


DATASET_ID = "openlanguagedata/flores_plus"
DATASET_REVISION = "5fec6c13f9e5a4db2f745d4ec0d7c9721ddc4f06"
SPLIT = "dev"

LANGUAGES = {
    "eng_Latn": "eng",
    "hin_Deva": "hin",
    "kan_Knda": "kan",
    "tam_Taml": "tam",
}

EXPECTED_ROWS = 997


def normalize_text(text: str) -> str:
    """Apply NFC Unicode normalization without changing content otherwise."""
    return unicodedata.normalize("NFC", text)


def load_language(language_code: str):
    return load_dataset(
        DATASET_ID,
        language_code,
        split=SPLIT,
        revision=DATASET_REVISION,
    )


def validate_dataset(datasets: dict[str, object]) -> list[int]:
    """Validate row counts, IDs, and cross-language alignment."""
    id_lists = {}

    for language_code, ds in datasets.items():
        row_count = len(ds)
        if row_count != EXPECTED_ROWS:
            raise ValueError(
                f"{language_code}: expected {EXPECTED_ROWS} rows, got {row_count}"
            )

        ids = [int(row["id"]) for row in ds]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{language_code}: duplicate sentence IDs found")

        id_lists[language_code] = ids

    reference_language = next(iter(LANGUAGES))
    reference_ids = set(id_lists[reference_language])

    for language_code, ids in id_lists.items():
        if set(ids) != reference_ids:
            raise ValueError(
                f"{language_code}: sentence ID set does not match "
                f"{reference_language}"
            )

    return id_lists[reference_language]


def write_corpus(
    datasets: dict[str, object],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "dataset": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "split": SPLIT,
        "languages": list(LANGUAGES.keys()),
        "expected_sentences_per_language": EXPECTED_ROWS,
        "preprocessing": [
            "Unicode NFC normalization only",
            "Preserve original case, punctuation, and whitespace",
        ],
    }

    for language_code, short_code in LANGUAGES.items():
        rows = sorted(datasets[language_code], key=lambda row: int(row["id"]))

        texts = []
        domains = {}
        topics = {}

        for row in rows:
            text = normalize_text(row["text"])

            if not text.strip():
                raise ValueError(
                    f"{language_code}: empty sentence found at id={row['id']}"
                )

            texts.append(text)

            domain = row["domain"]
            topic = row["topic"]

            domains[domain] = domains.get(domain, 0) + 1
            topics[topic] = topics.get(topic, 0) + 1

        output_path = output_dir / f"{short_code}.txt"
        output_path.write_text("\n".join(texts) + "\n", encoding="utf-8")

        metadata[short_code] = {
            "language_code": language_code,
            "sentence_count": len(texts),
            "domains": dict(sorted(domains.items())),
            "topics": dict(sorted(topics.items())),
        }

    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare the FLORES+ multilingual evaluation corpus."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "eval_corpus",
        help="Directory for locally materialized evaluation files.",
    )
    args = parser.parse_args()

    datasets = {
        language_code: load_language(language_code)
        for language_code in LANGUAGES
    }

    reference_ids = validate_dataset(datasets)

    print(f"dataset: {DATASET_ID}")
    print(f"dataset revision: {DATASET_REVISION}")
    print(f"split: {SPLIT}")
    print(f"languages: {', '.join(LANGUAGES)}")
    print(f"sentences per language: {EXPECTED_ROWS}")
    print(f"total language-sentences: {EXPECTED_ROWS * len(LANGUAGES)}")
    print(f"shared aligned IDs: {len(reference_ids)}")

    write_corpus(datasets, args.output_dir)

    print(f"materialized corpus: {args.output_dir}")


if __name__ == "__main__":
    main()