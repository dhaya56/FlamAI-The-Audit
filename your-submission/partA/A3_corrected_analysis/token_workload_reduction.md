# A3-2 — Direct GPT-2 vs Sarvam-1 Token Workload

## Objective

Quantify the direct model-token reduction obtained by replacing GPT-2 tokenization with Sarvam-1 tokenization for the same aligned FLORES+ content.

## Corpus

* 997 aligned sentences per language
* Hindi, Kannada, Tamil
* 2,991 Indic sentences in aggregate

## Command

```text
python your-submission\partA\A3_corrected_analysis\compare_token_reduction.py
```

## Results

| Language | GPT-2 tokens | Sarvam-1 tokens | Tokens reduced | Reduction |
| -------- | -----------: | --------------: | -------------: | --------: |
| Hindi    |      191,828 |          34,206 |        157,622 |    82.17% |
| Kannada  |      349,772 |          37,225 |        312,547 |    89.36% |
| Tamil    |      397,163 |          34,539 |        362,624 |    91.30% |

These reductions are also reproduced by the aligned sentence-level workload comparison:

| Language | GPT-2 tok/sentence | Sarvam-1 tok/sentence | Reduction |
| -------- | -----------------: | --------------------: | --------: |
| Hindi    |         192.405216 |             34.308927 |    82.17% |
| Kannada  |         350.824473 |             37.337011 |    89.36% |
| Tamil    |         398.358074 |             34.642929 |    91.30% |

## Aggregate Indic Workload

Across Hindi + Kannada + Tamil:

* GPT-2: 938,763 tokens
* Sarvam-1: 105,970 tokens
* Reduction: 832,793 tokens
* Aggregate reduction: 88.71%
* Sarvam-1 token workload: 0.1129x of GPT-2

## English Trade-off

Sarvam-1 is not universally more token-efficient.

For the same 997 English sentences:

* GPT-2: 25,741 tokens
* Sarvam-1: 29,915 tokens
* Sarvam-1 uses 16.22% more tokens

Therefore, the evidence supports an Indic-language routing advantage rather than a universal token-efficiency claim.

## Routing / Cost Metric

The single number that should drive routing and token-cost estimation is:

**direct model tokens for equivalent aligned content**

Operationally, this can be represented as total tokens or tokens per aligned sentence for the same workload.

This is preferred over `tokens/word` because serving systems consume model tokens, while whitespace-separated words are not a language-neutral unit.

The denominator metrics remain useful diagnostics for explaining why token counts differ across languages, but they should not be treated as direct cost multipliers.

## Caveat

The measured token-count reduction is not itself a measured percentage reduction in latency or monetary serving cost. Actual serving performance also depends on model architecture, batching, hardware, KV-cache behavior, and other serving overheads.

## Conclusion

For the evaluated aligned FLORES+ corpus, Sarvam-1 substantially reduces the number of model tokens required for Hindi, Kannada, and Tamil relative to GPT-2. The strongest operational evidence is the direct aligned token-count reduction, not the fertility number alone.
