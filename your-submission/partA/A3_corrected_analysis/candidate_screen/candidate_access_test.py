from transformers import AutoTokenizer

CANDIDATES = [
    ("GPT-2", "gpt2"),
    ("IndicBERTv2", "ai4bharat/IndicBERTv2-SS"),
    ("IndicTrans2", "ai4bharat/indictrans2-en-indic-1B"),
    ("Sarvam-1", "sarvamai/sarvam-1"),
    ("Qwen2.5-7B", "Qwen/Qwen2.5-7B"),
    ("Gemma-2-9B", "google/gemma-2-9b"),
    ("XLM-R", "FacebookAI/xlm-roberta-base"),
]

SAMPLES = {
    "eng": "The children are reading a book in the library.",
    "hin": "बच्चे पुस्तकालय में एक किताब पढ़ रहे हैं।",
    "kan": "ಮಕ್ಕಳು ಗ್ರಂಥಾಲಯದಲ್ಲಿ ಒಂದು ಪುಸ್ತಕವನ್ನು ಓದುತ್ತಿದ್ದಾರೆ.",
    "tam": "குழந்தைகள் நூலகத்தில் ஒரு புத்தகத்தைப் படிக்கிறார்கள்.",
}


def main():
    for name, repo in CANDIDATES:
        print(f"\n{'=' * 70}")
        print(f"{name}: {repo}")

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                repo,
                use_fast=False,
                trust_remote_code=True,
            )

            print("LOAD: OK")
            print("Tokenizer class:", type(tokenizer).__name__)
            print("Vocab size:", len(tokenizer))

            for lang, text in SAMPLES.items():
                ids = tokenizer.encode(
                    text,
                    add_special_tokens=False,
                )
                print(f"{lang}: {len(ids)} tokens")

        except Exception as exc:
            print("LOAD: FAILED")
            print(f"ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()