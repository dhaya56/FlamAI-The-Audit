# A4 — Tokenizer Routing Recommendation

## Decision

Use **language-aware tokenizer routing**: route Hindi, Kannada, and Tamil traffic to **Sarvam-1**, while retaining **GPT-2 for English**, subject to a quality-equivalence check before production rollout.

## Corrected Evidence

On the same 997 aligned FLORES+ sentences per language, the corrected analysis measured:

| Language | GPT-2 tokens | Sarvam-1 tokens | Token reduction |
| -------- | -----------: | --------------: | --------------: |
| Hindi    |      191,828 |          34,206 |      **82.17%** |
| Kannada  |      349,772 |          37,225 |      **89.36%** |
| Tamil    |      397,163 |          34,539 |      **91.30%** |

Across the combined Hindi + Kannada + Tamil workload, GPT-2 produced **938,763 tokens** versus **105,970** for Sarvam-1: an **88.71% reduction** in model-token workload.

The trade-off is English: Sarvam-1 produced **29,915 tokens** versus **25,741** for GPT-2, or **16.22% more tokens**.

The same conclusion is visible using aligned sentence workload: Sarvam-1 reduced tokens per sentence by 82.17% for Hindi, 89.36% for Kannada, and 91.30% for Tamil.

## Why This Routing Decision

The routing decision should be driven by **actual model-token workload for equivalent content**, because model serving consumes tokens rather than whitespace-defined linguistic words.

`Tokens/word` remains useful as a diagnostic normalization, but it is not treated as a direct serving-cost multiplier.

## Biggest Caveat

This experiment measures **tokenization efficiency, not end-to-end system cost, latency, or model quality**. Sarvam-1's lower token count does not by itself prove lower production cost, and the analysis does not establish that Sarvam-1 provides equivalent output quality for the production task.

Therefore, the routing policy should be deployed only after a task-quality check confirms that the quality trade-off is acceptable.

## Production Metric

Monitor **p95 input tokens per request by language and tokenizer route**.

This catches the analysis being wrong in production if real user traffic produces materially higher token workloads than predicted by the FLORES+ evaluation, or if the expected Indic-tokenization advantage does not persist on live traffic. The reason for this is because the most direct production check of whether that prediction is holding is therefore the actual token workload. Latency and cost can change for many reasons unrelated to tokenization.

## Recommendation

Proceed with a **language-aware Indic routing policy** that sends Hindi, Kannada, and Tamil traffic to Sarvam-1, while retaining GPT-2 for English until quality and end-to-end serving measurements justify broader replacement.
