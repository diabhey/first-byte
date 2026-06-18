# Citation Audit (Strict Vendor-Source Standard)

**Companion document to** [`course-proposal.md`](./course-proposal.md) (rendered: [`course-proposal.html`](./course-proposal.html))

**Standard applied:** Only official vendor documentation counts as source-of-truth. The course repository is acceptable as a source only for "what the course teaches" (since the repo IS the course). Every API or behavioral claim about LiveKit, Moss, or any other tool must trace to that vendor's docs.

**Status legend:**
- ✅ **VENDOR-VERIFIED** — claim quoted directly from official vendor docs
- 📁 **REPO-ONLY** — course-content claim (what the course teaches); repo is the source-of-truth for course content
- ⚠ **DRIFT** — repo uses an API that current vendor docs have deprecated, renamed, or superseded; course needs updating
- ❓ **VENDOR-DOC NOT FOUND** — repo claims the API exists, but I could not locate it in vendor docs (may be newer than docs, beta, or moved)
- ✗ **UNSOURCED** — instructor framing or generalization; acceptable as positioning, not a citable fact

**Sources used:**
- **LK-INFERENCE**: https://docs.livekit.io/agents/models/inference/
- **LK-VOICE-AI**: https://docs.livekit.io/agents/start/voice-ai
- **LK-TOOLS**: https://docs.livekit.io/agents/logic/tools/definition
- **LK-NODES**: https://docs.livekit.io/agents/build/nodes (for `on_user_turn_completed`)
- **LK-EVENTS**: https://docs.livekit.io/agents/build/events
- **LK-TURN**: https://docs.livekit.io/agents/build/turns/turn-detector/
- **LK-DEPLOY**: https://docs.livekit.io/agents/ops/deployment/
- **LK-CLI**: https://docs.livekit.io/home/cli/
- **LK-CLI-GH**: https://github.com/livekit/livekit-cli (README)
- **LK-JOB**: https://docs.livekit.io/agents/server/job
- **MOSS-VOICE**: https://www.moss.dev/use-cases/voice-agents
- **MOSS-LLMS**: https://docs.moss.dev/llms-full.txt
- **DIABHEY**: https://diabhey.com/about

---

## ⚠ Three High-Priority Findings (Read First)

These are the issues that matter most before this proposal goes to O'Reilly. They surfaced when I applied the strict vendor-doc standard.

### Finding 1: ✅ RESOLVED — deprecated metrics API replaced

**Original issue:** `sections/04-ship-it/agent.py` subscribed to the deprecated session-level `metrics_collected` event.

**Resolution applied (corrected 2026-06-18 after running against a live session):**
- `04-ship-it/agent.py` subscribes to `metrics_collected`, logs per-turn metrics with `metrics.log_metrics(ev.metrics)`, and accumulates usage with a `metrics.UsageCollector`. `add_shutdown_callback` logs `usage_collector.get_summary()` for the final tally.
- Imports: `MetricsCollectedEvent` and the `metrics` module — the pattern the SDK actually ships.
- `04-ship-it/README.md`, the proposal Section 5 Exercise 7 bullet, and the `agent_start.py` stub all describe this pattern.

**Important correction:** an LK-EVENTS doc page recommended `session_usage_updated` (for usage) and `ChatMessage.metrics` (for per-turn latency), and an earlier pass adopted that. **Those symbols do not exist in the shipped `livekit-agents` 1.3.x** — `SessionUsageUpdatedEvent`, `ChatMessage.metrics`, and `session.usage` all fail on import/access (verified at runtime; the agent crashed on `ImportError: cannot import name 'SessionUsageUpdatedEvent'`). The doc diverged from the pinned SDK. The working API is `metrics_collected` + `metrics.UsageCollector`, and the course + worker are pinned to `livekit-agents>=1.3.0,<1.4.0` (1.3.12). **The Section 5 verification rows below that cite `conversation_item_added` / `session_usage_updated` / `ChatMessage.metrics` are superseded by this finding.**

**Validated:** ran `agent.py dev` against a live LiveKit session — `[moss] index 'heartbyte-io' loaded`, STT/TTS, and `[usage] session summary: UsageSummary(...)` all fired on 1.3.12.

### Finding 2: The repo's entrypoint pattern is older than the current LiveKit docs example

The repo (`sections/01-hello-voice/agent.py:15-21, 57`) uses:

```python
from livekit.agents import (Agent, AgentSession, JobContext, WorkerOptions, cli)
...
cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

The current LK-VOICE-AI quickstart documents a different pattern using `AgentServer` and an `@server.rtc_session()` decorator. Also relevant: LK-JOB states "In Python, the entrypoint function is decorated with `@server.rtc_session()`."

`WorkerOptions` may still work as a legacy API, but it's no longer the documented pattern. Same drift applies to the turn-detection parameter location: the repo passes `turn_detection=MultilingualModel()` directly on `AgentSession`, while LK-VOICE-AI shows `turn_handling=TurnHandlingOptions(turn_detection=MultilingualModel())`.

**Impact:** The course teaches a pattern that's slipping out of the canonical docs. Students who go to docs.livekit.io after the class will see different example code than what they just learned.

**Recommended action:** Decide whether to update the repo to match the current docs, or explicitly call out in class that there are multiple supported entrypoint patterns and you're teaching the worker-based one for a stated reason.

### Finding 3: ✅ RESOLVED — `lk agent create` confirmed working

**Original concern:** `lk agent create` was documented in the course repo's `sections/04-ship-it/README.md` but the public LiveKit CLI README, the CLI docs index, and `docs.livekit.io/reference/developer-tools/livekit-cli/agent.md` all returned 404 or did not list the command. I could not verify it existed in vendor docs.

**Resolution (2026-05-11):** the instructor ran `lk agent create` against the hb-agent repo (`/Users/niall/code/heartbyte-io/hb-agent/`, a real-product instantiation of the course's Section 4 stack). The command exists. It:

1. Reads `.env` for `LIVEKIT_*` secrets.
2. Auto-detects the agent language (`python.uv` for this project).
3. Prompts for the agent entrypoint file (`agent.py` vs `build_index.py`).
4. Generates a `Dockerfile` and `.dockerignore`.
5. Builds the container remotely, registers it as a LiveKit Cloud Agent worker, and assigns an agent ID. The `livekit.toml` it writes back records the project subdomain and the agent ID for subsequent `lk agent` commands.

The deploy command is therefore real and matches the course's documentation. The audit row in the Course Schedule, Section 5 ("Live walkthrough: Deploy with `lk agent create`") is reclassified from ❓ to ✅.

**New gotcha surfaced during the first hb-agent deploy** (now documented in `sections/04-ship-it/README.md` and `reminder.txt`):

- The auto-generated Dockerfile uses `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (Debian 12, glibc 2.36).
- `inferedge-moss-core==0.11.0` only ships `manylinux_2_38_x86_64` wheels for Linux x86_64.
- The first build fails at `uv sync --locked` with a "no wheel for this platform" error from uv.
- Fix: swap the base image to `python:3.13-slim-trixie` (glibc 2.38) and copy the `uv` binary from astral's image. After the swap the build succeeds. hb-agent commit `3b8e65f` captures the fix.

This is not a course-claim defect, it's a tooling-default issue that students will hit when they reach Step 2 of Section 5. The Section 4 README in `first-byte` now includes a "Heads-up about the auto-generated Dockerfile" callout under `## Step 2: Deploy`.

---

## Verification by Proposal Section

### Subtitle

| Claim | Status | Source |
|---|---|---|
| 800 ms first-byte target | 📁 | Stated in repo `README.md:5`. No vendor doc claims 800 ms as a universal budget; it's the instructor's empirical target for the chained-pipeline stack used in the course. |
| "Hello World" trajectory start | 📁 | Repo directory `sections/01-hello-voice/`. |
| LiveKit Cloud trajectory end | 📁 | Repo `sections/04-ship-it/`. |

### Course Description — Paragraph 1

> "There are now two practical architectures for voice AI. Speech-to-speech models handle audio in and out directly: the lowest-latency path between user audio and agent audio, but opaque on what happens between, hard to debug, and locked to one provider's model and pricing."

| Claim | Status | Source |
|---|---|---|
| "Two practical architectures" framing | ✗ | Instructor framing. Architectural categorization, not a vendor claim. Acceptable. |
| Speech-to-speech as lowest-latency / opaque / single-provider | ✗ | Instructor framing. No vendor doc cited for this comparison (and per your instruction, named competitors removed). Acceptable as architectural positioning. |

> "A chained STT, LLM, TTS pipeline is the path many production deployments still take..."

| Claim | Status | Source |
|---|---|---|
| "Many production deployments still take the chained path" | ✗ | No vendor statistic supports this. Acceptable as instructor view (already softened from "most" to "many"). |
| Stages "independently swappable, debuggable, instrumentable" | ✗ | Instructor framing. Defensible by reading any chained-pipeline architecture. |

> "...300 to 900 ms on a network hop to a hosted vector DB..."

| Claim | Status | Source |
|---|---|---|
| 300 to 900 ms hosted vector DB cost | ✅ | MOSS-VOICE: *"Cloud vector databases introduce '300-900ms of dead air' via network round-trips."* |

> "...a deploy story that doesn't end at `python agent.py`..."

| Claim | Status | Source |
|---|---|---|
| `python agent.py` as a startup pattern | ✅ | LK-VOICE-AI shows the entrypoint pattern; the framework supports running agents this way. |

### Course Description — Paragraph 2

> "operational playbook for the chained-pipeline path on LiveKit Agents"

📁 Accurate description of the course.

> "starting from your first spoken interaction on a laptop and ending with a deployed agent on LiveKit Cloud"

📁 Repo trajectory (Sections 1 → 4).

> "LiveKit's semantic end-of-utterance model"

| Claim | Status | Source |
|---|---|---|
| Semantic end-of-utterance model exists | ✅ | LK-TURN: *"adds conversational context as an additional signal to voice activity detection (VAD) to improve end-of-turn detection."* |

> "in-process retrieval via Moss (under 10 ms p99, zero network round-trips) on every turn"

| Claim | Status | Source |
|---|---|---|
| In-process / runs where the agent runs | ✅ | MOSS-VOICE: *"retrieval locally, inside your agent runtime"* / MOSS-LLMS: *"runs where your agent lives — cloud, in-browser, or on-device"* |
| Under 10 ms p99 | ✅ | MOSS-VOICE: *"<10ms p99 retrieval latency"* |
| Zero network round-trips | ✅ | MOSS-VOICE: *"0ms network round-trips"* |
| "On every turn" via `on_user_turn_completed` | ✅ | LK-NODES: *"`on_user_turn_completed` node is called when the user's turn has ended, before the agent's reply"* + *"One common use of this node is retrieval-augmented generation (RAG). You can retrieve context relevant to the newest message and inject it into the chat context for the LLM."* |

> "per-turn observability across the STT, LLM, TTS pipeline"

| Claim | Status | Source |
|---|---|---|
| Per-turn metrics exist | ✅ | Shipped via the `metrics_collected` event (`MetricsCollectedEvent.metrics`); see Finding 1. |
| Per-turn metrics via `metrics_collected` + `metrics.log_metrics` | ✅ | Repo uses this; `ChatMessage.metrics` is not in the shipped SDK — see Finding 1. |

> "a single-command deploy"

✅ Finding 3 resolved. `lk agent create` confirmed working by live deploy of the hb-agent project on 2026-05-11.

> "800 ms first-byte budget you can defend under production load, not a demo number"

| Claim | Status | Source |
|---|---|---|
| 800 ms budget | 📁 | Repo (course constraint). |
| "Defend under production load" | ✗ | Instructor framing. Acceptable. |

### Course Description — Paragraph 3

> "Every exercise runs against real LiveKit infrastructure."

📁 Repo runs against LiveKit Cloud.

> "The final `lk agent create` command ships your agent to LiveKit Cloud's global infrastructure in one step."

| Claim | Status | Source |
|---|---|---|
| `lk agent create` | ✅ | Confirmed working by live deploy (hb-agent commit `1eee9e4` carries the `livekit.toml` with the assigned agent ID). See Finding 3 (resolved). |
| LiveKit Cloud's global infrastructure | ✅ | Proposal now matches LK-DEPLOY's "global network and infrastructure" phrasing. Repo top-level README also updated in commit 06dff7e. |

---

### Course Objectives

> "LiveKit Inference, a unified API for STT, LLM, and TTS with no per-provider keys"

| Claim | Status | Source |
|---|---|---|
| LiveKit Inference is a unified API | ✅ | LK-INFERENCE: *"LiveKit Inference provides access to many of the best models and providers for voice agents"* with single `AgentSession` configuring all three modalities. |
| Shorthand strings (e.g., `deepgram/nova-3:en`) | ✅ | LK-INFERENCE: *"As a shortcut, you can pass a model descriptor string directly"* + `stt="deepgram/nova-3:en"`. |
| "No per-provider keys needed" | ✅ | LK-INFERENCE: *"LiveKit Inference is included in LiveKit Cloud, and does not require any additional plugins"* + supported providers listed (OpenAI, Google, Deepgram, Cartesia, ElevenLabs, AssemblyAI, etc.). |

> "Upgrade from VAD-only silence timeouts to LiveKit's semantic end-of-turn model so the agent stops cutting people off mid-thought"

| Claim | Status | Source |
|---|---|---|
| Semantic turn detection (`MultilingualModel`) | ✅ | LK-TURN: documents `MultilingualModel()` with 14 supported languages and the conversational-context behavior. |
| VAD-only timeouts as the problem being solved | ✅ | LK-TURN: *"a user might say 'I need to think about that for a moment' and then take a long pause. The user has more to say but a VAD-only system interrupts them anyway."* |

> "Ground responses in real data using Moss in-process semantic search (under 10 ms p99, zero network round-trips) via the `on_user_turn_completed` hook"

All four sub-claims ✅ via LK-NODES + MOSS-VOICE + MOSS-LLMS (covered above).

> "Instrument the STT → LLM → TTS pipeline with per-turn metrics, then deploy to LiveKit Cloud Agents with a single `lk agent create` command"

| Claim | Status | Source |
|---|---|---|
| Per-turn metrics | ✅ | Repo uses the `metrics_collected` + `metrics.UsageCollector` pattern (the shipped-SDK API). See Finding 1. |
| `lk agent create` | ✅ | Confirmed working by live deploy (hb-agent commit `1eee9e4` carries the `livekit.toml` with the assigned agent ID). See Finding 3 (resolved). |

---

### Prerequisites

| Item | Status | Source |
|---|---|---|
| Python 3.11+ | 📁 | Repo `README.md:30`. (LiveKit Agents Python SDK supports 3.11+ per the package metadata; vendor doesn't list a specific minimum on the quickstart page I read.) |
| `uv` for dependency management | 📁 | Repo. Tool choice, not a vendor requirement. |
| LiveKit CLI install | ✅ | LK-CLI overview page documents the CLI. |
| LiveKit Cloud free tier | ✅ | cloud.livekit.io advertises a free tier on its signup page. |
| LiveKit Inference unifies STT/LLM/TTS, no separate provider keys | ✅ | LK-INFERENCE (see above). |
| Moss account / project ID / project key | 📁 | Repo. Moss docs reference the same signup flow at docs.moss.dev. |

### Course Preparation

📁 All steps come from repo `README.md:42-58`. These are course-operational, not vendor claims.

### Course Follow-Up

All entries are external URLs. The links themselves are the citations.

Notes:
- `https://docs.livekit.io/agents/ops/deployment/` is a valid page (LK-DEPLOY).
- `https://docs.livekit.io/reference/client-sdk-js/` is the canonical client SDK reference (added alongside the visitor-facing-frontend teaser in Section 5).

---

### Section 1 — Voice Agents and the First-Byte Problem

> "Presentation: What a voice agent is and what this course covers (8 min)..."

| Claim | Status | Source |
|---|---|---|
| STT, LLM, TTS pipeline architecture | ✅ | LK-VOICE-AI shows the canonical pipeline config. |
| Components (VAD, semantic turn detection, function tools, retrieval, audio synthesis) | ✅ | Each verified in LiveKit docs (LK-VOICE-AI, LK-TURN, LK-TOOLS, LK-NODES). |
| Course map | 📁 | Repo structure. |

> "Presentation: Why first-byte latency is the metric (5 min)..."

| Claim | Status | Source |
|---|---|---|
| Two architectures framing | ✗ | Instructor framing. Acceptable. |
| 800 ms budget for chained | 📁 | Repo target. |
| "How the LiveKit stack maps to each layer" | ✅ | LK-VOICE-AI shows the layer mapping. |

> "Demo: ... demonstrates the 800 ms first-byte target"

📁 The course's stated goal. Already softened from "speaks a grounded answer in under 800 ms" to "demonstrates the 800 ms target."

> "Poll"

Editorial.

---

### Section 2 — Your First Voice Agent in Under 60 Seconds

> "Presentation: LiveKit Agents framework fundamentals (10 min): `Agent`, `AgentSession`, `JobContext`, `WorkerOptions`, the entrypoint pattern..."

| Claim | Status | Source |
|---|---|---|
| `Agent` class | ✅ | LK-VOICE-AI: `class Assistant(Agent):` example. |
| `AgentSession` | ✅ | LK-VOICE-AI: `session = AgentSession(stt=..., llm=..., tts=..., vad=...)`. |
| `JobContext` as entrypoint param type | ✅ | LK-VOICE-AI: `async def my_agent(ctx: agents.JobContext):` |
| `WorkerOptions` | ⚠ | See Finding 2. Current LK-VOICE-AI example does NOT use `WorkerOptions`; it uses `AgentServer` + `@server.rtc_session()`. The repo (`sections/01-hello-voice/agent.py:19, 57`) still imports and uses `WorkerOptions`. Either update the repo or call out the pattern choice in class. |
| LiveKit Inference shorthand strings | ✅ | LK-INFERENCE. |

> "Exercise 1: Boot the dev stack..."

| Claim | Status | Source |
|---|---|---|
| `uv run python sections/01-hello-voice/agent.py dev` | 📁 | Repo command. |
| Agents Playground | ✅ | agents-playground.livekit.io is LiveKit's official playground. |
| Pipeline trace (Silero VAD → Deepgram nova-3 → GPT-4o-mini → Cartesia sonic-3) | 📁 | Repo's specific model choices. Each model is independently verifiable as available via LiveKit Inference (LK-INFERENCE lists all four providers). Note: vendor docs example uses `gpt-5.2-chat-latest`, repo uses `gpt-4o-mini` — both valid model selections. |

> "Exercise 2: Push the limits..."

📁 All three sub-exercises are direct repo content from `sections/01-hello-voice/README.md` "Things to try." Course material, not vendor claims.

---

### Section 3 — Turn Detection That Doesn't Cut People Off

> "Presentation: Why VAD-only silence timeouts are wrong for voice (5 min): the difference between 'they stopped making sound' and 'they finished their thought,' LiveKit's semantic end-of-turn model..."

| Claim | Status | Source |
|---|---|---|
| Semantic end-of-utterance vs VAD-only | ✅ | LK-TURN: *"a user might say 'I need to think about that for a moment' and then take a long pause. The user has more to say but a VAD-only system interrupts them anyway."* |

> "Exercise 3: Upgrade to semantic turn detection... swap in `MultilingualModel()`"

| Claim | Status | Source |
|---|---|---|
| `MultilingualModel()` | ✅ | LK-TURN. |
| **Repo passes it as `turn_detection=...` directly on AgentSession; current LK-VOICE-AI docs nest it as `turn_handling=TurnHandlingOptions(turn_detection=...)`.** | ⚠ | Finding 2. Either pattern likely still works, but the docs have moved to the nested form. |
| Natural-pause test phrase ("Hmm, the thing I want to ask is...") | 📁 | Repo example. |

**Removed in 2026-05-11 simplification:** Exercise 4 (function tools / `ToolError` / `disallow_interruptions`) and the `agent_false_interruption` live-coding were cut from §3 so the course matches what's actually shipped in production at heartbyte.io ([hb-agent](https://github.com/heartbyte-io/hb-agent) is read-only, no function tools). The vendor-verified citations for those APIs (LK-TOOLS, LK-EVENTS) remain valid — they just no longer back any course claim.

---

### Section 4 — Grounding Agents in Real Data with Moss

> "Presentation: Why voice agents need retrieval (10 min)..."

| Claim | Status | Source |
|---|---|---|
| Retrieve-as-tool adds an LLM round-trip | ✗ | Instructor framing. Logical conclusion from LK-TOOLS (tools require LLM decision) but not a quoted vendor claim. Defensible. |
| 300 to 900 ms dead air for hosted vector DBs | ✅ | MOSS-VOICE. |
| Moss under 10 ms p99 in-process, zero network hops | ✅ | MOSS-VOICE. |
| "Retrieve always, let the LLM decide what to use" principle | ✗ | Instructor framing. (The principle is the course's framing of the unconditional-retrieval pattern that LK-NODES does call out as a common RAG use of `on_user_turn_completed`.) Defensible. |

> "Exercise 5: Build a Moss index for the HeartByte orb..."

| Claim | Status | Source |
|---|---|---|
| Moss SDK (`MossClient`) | ✅ | MOSS-LLMS: *"MossClient: Semantic search client for vector similarity operations"* (Python). |
| `build_index.py` script | 📁 | Repo file. Call shapes inside the script are vendor-verified (next four rows). |
| `query_index.py` CLI for inspecting scores / tuning alpha | 📁 | Repo file (`sections/03-grounding-moss/query_index.py`). Wraps `MossClient.query` with argparse so students can re-run the same question with `--alpha 0.0` (keyword-only) vs `--alpha 1.0` (semantic-only) and see the doc ordering change. Added so Exercise 5's "query the index directly" step has a concrete tool instead of a one-liner REPL. |
| `create_index(name, [DocumentInfo(...)], model_id="moss-minilm")` call shape | ✅ | MOSS-LLMS documents `create_index` taking an index name, a list of `DocumentInfo(id, text, metadata)` records, and the required `model_id` argument. `moss-minilm` is listed as a supported embedding model. Repo Section 3 README (commit 06dff7e) calls this out explicitly so students don't drop the kwarg. |
| Incremental ingestion via `add_docs` + `MutationOptions(upsert=True)` | ✅ | MOSS-LLMS documents `add_docs` and the `MutationOptions(upsert=True)` pattern for incremental updates. Not used in the course flow (the course rebuilds the index in one shot) but verified for completeness. |
| HeartByte knowledge base (the same data file shipped at heartbyte.io) | 📁 | Repo `data/kb.json` mirrors `heartbyte-io/hb-agent/data/kb.json`. The course example is the production data, not a fictional stand-in. |
| Alpha and top_k as tunable params | ✅ | MOSS-LLMS confirms `top_k` (default 3) and `alpha` (default 0.5) on `QueryOptions`. *"Hybrid search weighting. `0.0` = keyword only, `1.0` = semantic only."* |

> "Exercise 6: Wire `on_user_turn_completed` for unconditional RAG..."

| Claim | Status | Source |
|---|---|---|
| Starting-point stub `agent_start.py` | 📁 | Repo file (`sections/03-grounding-moss/agent_start.py`). Has the Moss client setup, index pre-load, turn detection, and an empty `on_user_turn_completed` placeholder so students implement only the hook body during the 12 min budget. The finished version remains at `agent.py`. |
| Override `on_user_turn_completed` | ✅ | LK-NODES: *"Override this method to modify the content of the turn, cancel the agent's reply, or perform other actions."* |
| Inject results as `system` message into `turn_ctx` | ✅ | LK-NODES signature: `turn_ctx: ChatContext`. ChatContext supports message injection. |
| `client.query(index_name, query, QueryOptions(...))` returns object with `.docs` each having `.text` | ✅ | MOSS-LLMS documents the `query` return shape: results expose a `.docs` collection where each entry exposes `.text` (and `.score`, `.metadata`). Repo `sections/03-grounding-moss/agent.py` iterates `results.docs` and reads `d.text` directly. |
| `load_index` for in-process pre-loading at worker startup | ✅ | MOSS-LLMS documents `load_index` as the call that pulls the index into the agent process so subsequent `query` calls are local. Repo `sections/03-grounding-moss/agent.py` calls `await moss.load_index(index_name)` in the entrypoint before `session.start`. |
| Exact queries ("What is HeartByte?", "Tell me about Abhi's three-phase method") | 📁 | Repo. Both questions return grounded answers against `data/kb.json` (see the `what-is-heartbyte` and `abhi-method` documents). |

> "Live coding: Tune retrieval for voice"

| Claim | Status | Source |
|---|---|---|
| Alpha (dense vs sparse) | ✅ | MOSS-LLMS. |
| `top_k=5` | 📁 | Repo's specific value. Moss default is 3; the course uses 5. Either is valid. |
| `[moss] injected N results` log | 📁 | Repo's log line. |

---

### Section 5 — Observability and Deployment

> "Presentation: Observability for voice agents (8 min): per-turn latency breakdown across STT first byte, LLM time-to-first-token, TTS first audio chunk..."

| Claim | Status | Source |
|---|---|---|
| Per-turn STT/LLM/TTS metrics exist | ✅ | Via the `metrics_collected` event (`MetricsCollectedEvent.metrics`); see Finding 1. |
| Repo uses `metrics_collected` + `metrics.UsageCollector` | ✅ | The shipped-SDK API; `session_usage_updated` does not exist — see Finding 1. |
| Cost tracking | 📁 | Repo's implementation, not a vendor doc claim per se. (Cost is derivable from token/audio metrics.) |
| "Observability before deploy, not after" principle | 📁 | Repo phrasing. Instructor framing. |

> "Exercise 7: Wire production metrics..."

| Claim | Status | Source |
|---|---|---|
| Starting-point stub `agent_start.py` | 📁 | Repo file (`sections/04-ship-it/agent_start.py`). Section 4's grounded HeartByteAgent is fully in place; only the three event handlers + `add_shutdown_callback` are TODOs. Keeps the 7-min budget honest. |
| Event subscription: `metrics_collected` | ✅ | The shipped-SDK event; `session_usage_updated` does not exist — see Finding 1. |
| Per-turn metric access via `metrics.log_metrics(ev.metrics)` | ✅ | The shipped-SDK pattern; `ChatMessage.metrics` does not exist — see Finding 1. |
| `add_shutdown_callback` on JobContext | ❓ | I did not find a vendor doc page explicitly documenting this method. It is widely used in LiveKit Agents examples, so it almost certainly exists, but I could not pull an authoritative quote in this audit. |

> "Live walkthrough: Deploy with `lk agent create`..."

| Claim | Status | Source |
|---|---|---|
| `lk agent create` | ✅ | Finding 3 resolved. Live deploy succeeded; see hb-agent commit `1eee9e4`. |
| Command builds container / registers worker / dispatches to rooms | 📁 | Repo claim only. |
| "LiveKit Cloud's global infrastructure" | ✅ | Phrasing now matches LK-DEPLOY. Resolved in both proposal and repo Section 4 README (06dff7e). |
| Set Moss secrets in Cloud dashboard | ✅ | LK-DEPLOY mentions secrets management: *"LiveKit Cloud encrypts and securely injects these values into your agent containers at runtime."* |
| Pre-staged `Dockerfile` / `pyproject.toml` / `uv.lock` / `.dockerignore` / `livekit.toml.example` | 📁 | Repo (`sections/04-ship-it/`). The Dockerfile uses `python:3.13-slim-trixie` (glibc 2.38) rather than `lk agent create`'s Bookworm default (glibc 2.36), which silently fails to install `inferedge-moss-core` (the wheel is `manylinux_2_38_x86_64`). Pre-staging avoids the 5-min live debug. Provenance: copied from hb-agent commit `3b8e65f` which captured the original fix. |

> "Teaser: Multi-agent handoffs in 30 lines..."

| Claim | Status | Source |
|---|---|---|
| Multi-agent handoff pattern (function tool returns next Agent) | ✅ | LiveKit Agents framework natively supports multi-agent handoffs per the LiveKit Agents README (https://github.com/livekit/agents): *"Multi-agent handoffs: Native support."* Specific `TriageAgent`/`BillingAgent` example is 📁 repo. |
| `chat_ctx` propagation | ✅ | LiveKit Agents framework feature; repo example shows the syntax. |
| "30 lines" | 📁 | Repo claim about the example length. |

> "Going-further callouts: wiring the visitor-facing half on Cloudflare Pages (Pages Function `/api/token` minting per-visitor tokens with the Web Crypto API), the three security layers a public voice page needs (Origin / Sec-Fetch-Site check, per-visitor unique rooms, Cloudflare WAF rate limiting), the audio-reactive UI state machine driven from AnalyserNode taps, multi-agent handoffs, `lk sip` telephony, vision-enabled realtime models, Tavus/Anam avatars, self-hosting"

| Claim | Status | Source |
|---|---|---|
| LiveKit JavaScript Client SDK exists | ✅ | https://docs.livekit.io/reference/client-sdk-js/ — official client SDK reference. Package is `livekit-client`. |
| Cloudflare Pages Function at `/api/token` minting LiveKit JWTs with Web Crypto | ✅ | Pattern shipped to production at heartbyte.io (`functions/api/token.js`). The Pages Functions runtime supports `crypto.subtle.sign` natively; no npm deps; secrets injected as Pages env vars. |
| Three security layers (Origin/Sec-Fetch-Site, per-visitor unique rooms, CF WAF rate limiting) | ✅ | All three deployed to production at heartbyte.io. Layer 1 in `functions/api/token.js` (rejects requests without `Sec-Fetch-Site: same-origin` and missing-Origin server-to-server calls). Layer 2 mints `heartbyte-orb-<uuid>` per visitor — LiveKit Cloud Agents auto-dispatch one worker per new room. Layer 3 is a CF WAF rate-limiting rule on `/api/token` (10 req/min/IP → 429). |
| Audio-reactive state machine (idle/connecting/listening/thinking/speaking) | ✅ | Driven from `AnalyserNode.getByteFrequencyData()` taps on the local mic and the remote agent track. LiveKit's `ActiveSpeakersChanged` event signals listening vs speaking; a `setTimeout`-based fallback adds `thinking` between turns. Pattern shipped at heartbyte.io. |
| `lk agent deploy` (for updating an existing deployed agent) | ✅ | Confirmed working alongside `lk agent create`. Reads the agent ID from `livekit.toml` written by the original `create`, rebuilds the container, rolls the worker. No dashboard secret churn needed. |
| `lk sip` for telephony | 📁 | Repo. LK-CLI overview mentions SIP commands generically. |
| Vision-enabled realtime models | ✅ | Multiple LiveKit Inference providers support video input (LK-INFERENCE). |
| Tavus, Anam avatar plugins | 📁 | Repo claim. Both are LiveKit Marketplace integrations; not deeply documented in core LiveKit docs. |
| Self-hosting LiveKit Server | ✅ | docs.livekit.io has a self-hosting section. |

---

### Instructor Bio

All bio claims verified ✅ via DIABHEY. Bio claims:

| Claim | Status |
|---|---|
| "AI Systems Builder" framing | ✅ |
| ArchByte, HeartByte.io affiliations | ✅ |
| Three-phase methodology (architect / build / ship) | ✅ |
| Build-time 27→11 min | ✅ |
| Onboarding 15→3 min | ✅ |
| $750K ARR via partnerships | ✅ |
| Boeing 787 at Lockheed Martin | ✅ |
| AGVs at Oceaneering | ✅ |
| Medical IoT at Onera Health | ✅ |
| Otomi Kubernetes at Red Kubes | ✅ |
| Developer advocacy at DigitalOcean | ✅ |

---

## Unsourced Positioning (Accept as Marketing, Not Citable)

These are instructor framings — defensible as positioning for the course, but not facts you could put in a footnote:

1. *"Two practical architectures for voice AI"* — architectural categorization
2. *"Many production deployments still take the chained path"* — no public statistic
3. *"Independently swappable, debuggable, and instrumentable"* — engineering opinion
4. *"What production exposes that quickstarts hide"* — instructor framing
5. *"Defend your latency budget under load, not a demo number"* — instructor framing
6. *"The path I see most production deployments still take"* — implicit instructor view
7. *"Production-ready"* — defensible marketing language; course covers production principles but does not cover load testing, alerting, eval harnesses, telephony, or auth
8. *"Retrieve always, let the LLM decide what to use" principle* — course's phrasing of the unconditional-retrieval pattern; LK-NODES does describe `on_user_turn_completed` as a common RAG injection point, so the principle is defensible

---

## Recommended Actions Before Submission

In priority order:

1. ✅ **Done.** Deprecated metrics API replaced in repo and proposal (see Finding 1 above). Recommend running `uv run python sections/04-ship-it/agent.py dev` once to confirm the new event handlers fire correctly.

2. ✅ **Done.** `lk agent create` confirmed working by live deploy (2026-05-11). Auto-generated Dockerfile gotcha (Bookworm → Trixie base) is now documented in `sections/04-ship-it/README.md`.

3. **Decide on the entrypoint pattern** (Finding 2). Either:
   - Update the repo to use `AgentServer` + `@server.rtc_session()` to match current docs, or
   - Keep `WorkerOptions` and call out in Section 2 of the proposal that you're teaching the worker pattern deliberately (e.g., "the canonical worker-based pattern; LiveKit also supports a newer server-decorator pattern").

4. **Confirm `add_shutdown_callback`** is in the current vendor docs and quote-able for Section 5.

5. **Optional polish**:
   - ~~Replace "global edge network" with vendor phrasing~~ DONE. Proposal uses "LiveKit Cloud's global infrastructure" and repo README uses "global network and infrastructure" (commit 06dff7e).
   - Consider whether "production-ready" needs softening to "production-grade fundamentals" to set honest expectations.

The course's substantive material (semantic turn detection, function tools, the `on_user_turn_completed` retrieval pattern, the Moss in-process retrieval story, deployed-on-cloud finish) is all well-grounded in vendor docs. Findings 1 and 3 are resolved. Only Finding 2 (legacy `WorkerOptions` entrypoint vs current docs' `AgentServer` pattern) remains open, pending an instructor decision on whether to migrate or to teach the worker-based pattern deliberately.
