from pathlib import Path
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[2]

CORPUS_DIR = (
    ROOT
    / "partA"
    / "A1_corpus"
    / "eval_corpus"
)

LANGUAGES = ["eng", "hin", "kan", "tam"]

TOKENIZERS = [
    ("GPT-2", "gpt2"),
    ("Sarvam-1", "sarvamai/sarvam-1"),
]


def read_lines(path):
    lines = []

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()

            if not raw:
                continue

            # Same normalization used by the starter fertility.py.
            # The starter script performs NFC before analysis.
            import unicodedata

            line = unicodedata.normalize("NFC", raw)
            lines.append(line)

    return lines


def analyze(lines, tokenizer):
    per_line_fertility = []
    per_line_tok_char = []

    for line in lines:
        # Preserve the starter methodology.
        line = line.lower()

        tokens = tokenizer.encode(
            line,
            add_special_tokens=False,
        )

        # Important: exact original denominator logic.
        words = line.split(" ")
        chars = len(line)

        per_line_fertility.append(
            len(tokens) / len(words)
        )

        per_line_tok_char.append(
            len(tokens) / chars
        )

    n = len(per_line_fertility)

    mean_fertility = (
        sum(per_line_fertility) / n
    )

    mean_tok_char = (
        sum(per_line_tok_char) / n
    )

    return mean_fertility, mean_tok_char


def main():
    print("A3-0 Legacy Method Reproduction")
    print()
    print("Corpus:", CORPUS_DIR)
    print("Languages:", ", ".join(LANGUAGES))
    print("Method: original fertility.py logic")
    print("Preprocessing: NFC, lowercasing")
    print('Word denominator: line.split(" ")')
    print("Aggregation: arithmetic mean of per-line ratios")
    print("Special tokens: disabled")
    print()

    corpus = {}

    for lang in LANGUAGES:
        path = CORPUS_DIR / f"{lang}.txt"

        if not path.exists():
            raise FileNotFoundError(
                f"Missing corpus file: {path}"
            )

        lines = read_lines(path)

        if len(lines) != 997:
            raise ValueError(
                f"{lang}: expected 997 lines, "
                f"found {len(lines)}"
            )

        corpus[lang] = lines

    for tokenizer_name, repo in TOKENIZERS:
        print("=" * 80)
        print(f"Tokenizer: {tokenizer_name}")
        print(f"Repository: {repo}")

        tokenizer = AutoTokenizer.from_pretrained(
            repo,
            use_fast=False,
        )

        results = {}

        for lang in LANGUAGES:
            fertility, tok_char = analyze(
                corpus[lang],
                tokenizer,
            )

            results[lang] = {
                "fertility": fertility,
                "tok_char": tok_char,
            }

            print(
                f"{lang}: "
                f"fertility={fertility:.6f} | "
                f"tok/char={tok_char:.6f}"
            )

        base = results["eng"]["fertility"]

        print()
        print("Relative fertility vs English:")

        for lang in LANGUAGES:
            if lang == "eng":
                continue

            ratio = (
                results[lang]["fertility"]
                / base
            )

            print(
                f"{lang}: {ratio:.6f}x"
            )

        print()


if __name__ == "__main__":
    main()