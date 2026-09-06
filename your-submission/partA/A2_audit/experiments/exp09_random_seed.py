from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ORIGINAL_SCRIPT = Path("starter_kit/fertility.py")

COMMAND_ARGS = [
    "--corpus",
    "eng=starter_kit/corpus_sample/eng_sample.txt",
    "--corpus",
    "hin=starter_kit/corpus_sample/hin_sample.txt",
    "--tokenizer",
    "gpt2",
]


def run_script(script_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(script_path), *COMMAND_ARGS],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def main() -> None:
    original_output = run_script(ORIGINAL_SCRIPT)

    source = ORIGINAL_SCRIPT.read_text(encoding="utf-8")

    seed_line = "random.seed(1337)  # reproducibility"

    if seed_line not in source:
        raise RuntimeError("Expected random.seed(1337) line was not found.")

    without_seed = source.replace(seed_line, "# seed removed for controlled experiment")

    with TemporaryDirectory() as tmp_dir:
        temp_script = Path(tmp_dir) / "fertility_no_seed.py"
        temp_script.write_text(without_seed, encoding="utf-8")

        no_seed_output = run_script(temp_script)

    print("original_with_seed")
    print(original_output)

    print("temporary_copy_without_seed")
    print(no_seed_output)

    print("outputs_identical:", original_output == no_seed_output)

    if original_output != no_seed_output:
        raise AssertionError(
            "Removing the unused seed changed the benchmark output."
        )


if __name__ == "__main__":
    main()