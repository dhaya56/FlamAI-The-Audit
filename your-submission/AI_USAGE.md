# AI Usage

I used ChatGPT as my main reasoning, coding, debugging, and writing assistant, and also used Claude and Gemini as independent second opinions, mainly for Part C.

I did **not** treat AI output as ground truth. A recurring workflow throughout the assignment was:

**AI suggestion → challenge it → check the actual evidence → revise → submit.**

## Where AI helped me

I primarily used ChatGPT as a reasoning and coding assistant.

It helped me break the assignment into smaller verifiable tasks, inspect the starter code and benchmark files, write analysis scripts, check arithmetic, structure the repository, and turn findings into reproducible markdown documentation.

For Part A, AI helped identify potential issues in the supplied fertility/tokenization implementation and helped design the corrected comparison across tokenizers and denominator choices. I still checked the proposed bugs against the actual code and corpus rather than accepting them from the model.

For Part B, AI was particularly useful for turning the model specification into explicit calculations. For example, the KV-cache calculation was derived from the supplied architecture parameters rather than from a model-generated guess:

```text
2(K,V) × 28 layers × 8 KV heads × 128 head dimension × 2 bytes
= 114,688 bytes/token
= 112 KiB/token
```

The predicted capacity was then checked against the actual benchmark rows, including the transition from zero preemptions at batch 24 to preemptions at batches 32 and 48.

AI was also useful for catching inconsistencies in `REPORT_v0.md`. The original report treated the `reported_tok_s` value as though it were a different kind of throughput measure. I independently reproduced the value from the benchmark columns and corrected the interpretation.

For Part C, AI helped me explore multiple possible strategies rather than immediately committing to one. This became an iterative discussion involving prompt engineering, a ≤1B rewriter, SFT, language-specific strategies, reviewer allocation, and staged/hybrid approaches.

## Where AI misled me

Several AI-generated answers were plausible but not sufficiently supported by the given evidence.

For example, AI sometimes supplied confident estimates for training time, throughput, latency, or reviewer speed when the assignment did not provide enough information to calculate them. I removed those claims or explicitly marked them as assumptions.

In Part B, I also had to challenge the interpretation of the throughput column in `REPORT_v0.md` and distinguish aggregate prompt+generation throughput from useful generated-token goodput.

In Part C, the reasoning initially leaned toward prompt engineering simply because it was cheaper and simpler. I pushed back on that assumption and considered quality, validation coverage, reviewer time, reversibility, and serving complexity instead. This led to the final staged **prompt-first + selective ≤1B rewriter** strategy, with SFT kept as a fallback.

## My role in the process

I repeatedly interrupted and redirected the AI reasoning when something did not seem defensible. I also introduced the idea of using Claude and Gemini as independent reviewers and brought their disagreements back into the analysis rather than accepting one model's recommendation.

I specifically pushed for:

* exact evidence instead of plausible claims;
* explicit assumptions where numbers could not be derived;
* verification of suspected bugs before including them;
* clear separation between observed results and proposed experiments;
* testing alternatives before settling on the final Part C strategy.

The final repository therefore reflects **AI-assisted work, but not unverified AI output**. The claims and calculations included in the submission were checked against the actual code, data, logs, and assignment constraints.
