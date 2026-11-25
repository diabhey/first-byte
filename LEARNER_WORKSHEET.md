# Learner worksheet

Use this worksheet to record evidence from the course. Leave a field blank when a mode cannot measure it; do not copy example values from slides or another learner.

## Environment

| Field | Your value |
| --- | --- |
| Date and course commit | |
| OS / architecture | |
| Python / LiveKit CLI | |
| `LLM_MODEL` | |
| `MOSS_INDEX_NAME` (no key) | |
| Test mode: local voice / local text fallback | |
| Headset or audio device | |

Remember: terminal Agent Console runs the worker locally, but LiveKit Inference still provides STT, LLM, and TTS. Text mode disables STT/TTS. Neither mode is a fully offline end-to-end test.

## Course Section 2: baseline timing and behavior

Use the same short prompt for at least three complete voice turns.

| Turn | End-of-turn delay | Final transcript delay | LLM TTFT | TTS TTFB | `server_e2e` | Complete/cancelled |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| Optional 4 | | | | | | |
| Optional 5 | | | | | | |

Baseline median `server_e2e`: __________

Section 2 budget: each `TOTAL pipeline` line says whether that turn was under 1370 ms. Record the printed milliseconds, not a sum of the stage times.

Do not add component durations; stages can overlap. If you used text mode, write “not measurable” for voice timing.

| Baseline prompt | Observed behavior |
| --- | --- |
| Pause after “the thing I want to ask is…” | |
| Pause between “What’s the weather” and “in Lisbon?” | |
| Speak a complete sentence over the reply | |
| Say only “mm-hm” during the reply | |

## Course Section 3: semantic turns and adaptive interruption

Repeat the same prompts and short question.

| Turn | `server_e2e` | Complete/cancelled | Notes |
| --- | ---: | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |

Semantic/adaptive median `server_e2e`: __________

| Comparison | VAD-only baseline | Semantic/adaptive worker | What changed? |
| --- | --- | --- | --- |
| Unfinished pause | | | |
| Paused location question | | | |
| Full spoken interruption | | | |
| Short backchannel | | | |

One failure or ambiguous case to add to a product evaluation set:

______________________________________________________________________

## Course Section 4: retrieval relevance and rejection

Record the actual settings used: `top_k` ______  `alpha` ______  `min_score` ______

| Query | Expected | Result count | Top score/source | Query time | Accept, reject, or investigate? |
| --- | --- | ---: | --- | ---: | --- |
| Known course question | relevant | | | | |
| Paraphrase | relevant | | | | |
| Irrelevant/unknown question | no result | | | | |

Why is your selected `min_score` defensible, and what evidence would change it?

______________________________________________________________________

### Hook evidence

| Test | Retrieval/injection evidence | Answer evidence | Result |
| --- | --- | --- | --- |
| Known question, hook enabled | | | |
| “Tell me more about his work” | | | |
| Known question, hook disabled (optional comparison) | | | |

Record the search and injection messages and the matching source data. Use the standalone unrelated query above to measure no match. In a spoken follow-up, the previous turn can bring in documents even if they cannot answer the new question.

### Transfer task

| Field | Your plan/result |
| --- | --- |
| Document added or replaced | |
| Expected source label | |
| Query that should retrieve it | |
| Paraphrase | |
| Query that should be rejected | |
| Rebuild/query result | |

## Course Section 5: observability

| Observation | Evidence |
| --- | --- |
| Dominant per-turn stage | |
| Why it appears dominant | |
| `eot_requests` at shutdown | |
| `interruption_requests` at shutdown | |
| LLM token usage | |
| STT/TTS usage | |
| Cancelled or unusual turn | |

Next experiment to test the bottleneck:

______________________________________________________________________

Do the data support the 800 ms investigation target on your setup? Explain without generalizing from one turn.

______________________________________________________________________

## Deployment and production boundary

Leave deployment fields open if you did not complete the optional post-class lab.

| Gate | Evidence/status |
| --- | --- |
| Local voice flow | |
| First private `create` | |
| Healthy worker and startup logs | |
| Worker join/cold-start time | |
| Per-turn `server_e2e` after join | |
| Private real call | |
| Optional orb connect/reconnect | |

One security or privacy gap before a public launch:

______________________________________________________________________

One reliability, capacity, or cost gap:

______________________________________________________________________

My next validation step, owner, and target date:

______________________________________________________________________
