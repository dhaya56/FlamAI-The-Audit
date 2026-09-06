# Part C — Decision Memo: Conversational Register

## Recommendation

Adopt a **prompt-first, selective-rewriter strategy**. Use prompt engineering across all six languages, and add a locally hosted **≤1B inference-time rewriter only for languages that fail the quality gate**. Keep SFT as a fallback rather than the starting intervention.

This is not a claim that one path is universally best. It uses the least invasive intervention as the default and spends additional compute and serving complexity only where the measured need justifies it.

## Assumptions

* **GPU:** Assume the A100 is available continuously for the stated 2 weeks: 14 × 24 = **336 A100-hours**.
* **Reviewer:** 10 h/week × 3 weeks = **30 reviewer-hours**. Assume **2 min/response = 30 ratings/hour** for planning.
* **Model availability:** Assume a suitable multilingual open-weight **≤1B** rewriter can be run locally; no external API is available.
* **Quality:** A response is successful only if it is both **casual/conversational and faithful to the original meaning**.
* **Validation coverage:** Native-speaker review is available only for **Hindi and Kannada**. Tamil, Telugu, Bengali and Marathi therefore receive lower-confidence automated/structural checks rather than being treated as human-validated.

## Back-of-envelope arithmetic

### Reviewer throughput

30 reviewer-hours × 30 ratings/hour = **900 response evaluations** available.

Initial blind comparison:

* 30 prompts × 2 native-reviewed languages × 3 conditions = **180 evaluations**
* 180 × 2 min = **6 reviewer-hours**

Remaining capacity:

* 30 − 6 = **24 reviewer-hours**
* 24 × 30 = **720 further evaluations**

The remaining reviewer time can be used for held-out evaluation, regression checks, and validation of any rewriter/SFT candidate.

### Data volume

For an initial rewriter training budget, provision **500 usable formal→casual pairs/language**:

* 500 × 6 = **3,000 usable pairs**
* Assume 200 source+target tokens/pair
* 3,000 × 200 = **600,000 training tokens/epoch**
* At 3 epochs = **1.8M token presentations**

This is a planning budget, not a claim that exactly 500 pairs/language are required; the dataset can be expanded only if the pilot shows underfitting.

### Training and serving cost

Because Part C does not specify a particular training model, sequence length, batching strategy, or measured A100 throughput, an exact training-hour estimate would be false precision. I would therefore cap the initial rewriter/SFT training commitment at **25% of the assumed 336-hour GPU budget = 84 A100-hours**, and continue only if the pilot demonstrates a meaningful quality gain.

For rewriter serving, assume 300 input + 100 output tokens/request. Per 100,000 requests:

* 100,000 × 400 = **40M rewriter tokens**

At an explicitly assumed effective throughput of 50k tokens/s, that corresponds to about **800 seconds (13.3 GPU-minutes) of raw inference compute**, before framework and queueing overhead. A 1B FP16 model needs about **2 GB for weights**; actual serving VRAM will be higher because of runtime overhead and KV cache.

Prompt-only requires no training and no extra model; its main incremental cost is the additional prompt tokens.

## Why not start with SFT?

SFT is the most invasive and least reversible option because it changes the main model's weights. It also requires trustworthy casual targets and regression validation across all six languages, while native review covers only Hindi and Kannada. I am therefore **not rejecting SFT because GPU compute is unavailable**; I am delaying it because it creates the largest data-quality and validation burden before we know that a weight-level change is necessary. If lighter interventions fail, SFT becomes the justified escalation path.

## Success metric

**Primary metric: blind casual-and-faithful pass rate.**

A response is a PASS only when it is both conversational and meaning-preserving.

**Launch threshold: ≥75% pass rate** on the held-out Hindi/Kannada evaluation.

For the rewriter to justify its additional serving complexity, require **≥75% pass rate and at least +10 percentage points over prompt-only** on the same held-out set.

The 75% and +10-point values are decision thresholds chosen in advance, not facts supplied by the scenario.

## Kill criterion

By the **end of Week 2**, abandon the prompt-first + selective-rewriter strategy for a language if the best tested configuration remains below **75% casual-and-faithful pass rate**, or if the rewriter improves on prompt-only by **less than 10 percentage points** and therefore does not justify its added serving complexity. Fall back to the better-performing prompt-only configuration. Escalate to SFT only if an initial SFT pilot has already demonstrated a clear quality gain and there is enough time remaining for validation.

## Day-1 experiment

Run the same **30 prompts in all six languages** under three conditions:

1. current/default prompting,
2. improved casual-register prompting,
3. casual-register prompting followed by the candidate ≤1B rewriter.

Use blind native-speaker review for Hindi and Kannada, recording casualness and faithfulness separately and using their combined PASS rate as the primary metric. Use structural/semantic sanity checks for Tamil, Telugu, Bengali and Marathi, explicitly treating these four languages as lower-confidence. The Day-1 result determines whether prompt-only is sufficient and whether the rewriter earns further GPU budget; SFT is considered only if both lighter interventions fail.
