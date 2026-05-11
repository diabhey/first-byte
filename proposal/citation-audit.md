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

**Resolution applied:**
- `04-ship-it/agent.py` now subscribes to `conversation_item_added` and reads per-turn latency from `ChatMessage.metrics`, and to `session_usage_updated` for cumulative usage. `add_shutdown_callback` reads `session.usage` for the final tally.
- Imports updated: removed `MetricsCollectedEvent` and the `metrics` module; added `ConversationItemAddedEvent` and `SessionUsageUpdatedEvent`.
- `04-ship-it/README.md` code snippet and "Concepts introduced" list rewritten to match.
- Proposal Section 5 Exercise 7 bullet rewritten to describe the new pattern.

LK-EVENTS quote backing the new pattern: *"The session-level `metrics_collected` event is deprecated. Use `session_usage_updated` for usage tracking and `ChatMessage.metrics` for per-turn latency."*

**Remaining caveat:** the new code hasn't been executed against a live LiveKit session. Run `uv run python sections/04-ship-it/agent.py dev` and confirm the new `[metrics] turn e2e_latency=...` and `[usage] ...` lines fire as expected.

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

### Finding 3: `lk agent create` is in the course repo but I could NOT locate it in vendor docs

The course's `sections/04-ship-it/README.md:33-36` documents the deploy command as:

```bash
lk agent create
```

This is the deploy story the entire Section 5 (and parts of the Course Description) depends on.

Sources searched:
- LK-CLI overview page: mentions "Create, deploy, update, and monitor agents on LiveKit Cloud" but does not list the specific command syntax
- LK-CLI-GH README: lists `lk perf agent-load-test`, `lk app create`, but **no `lk agent create`**
- `docs.livekit.io/reference/developer-tools/livekit-cli/agent.md`: returns **HTTP 404**
- `docs.livekit.io/agents/start/agent-deployment/`: returns **HTTP 404**

**Possibilities:**
- `lk agent create` is a newer CLI command not yet in the public README
- It's a feature behind a LiveKit Cloud Agents preview/beta
- The repo's command name is wrong and the actual current command is different (e.g., `lk app create` or `lk cloud agent ...`)

**Recommended action:** Before this proposal is submitted, run `lk agent --help` against the current CLI binary and verify `create` is listed. If it isn't, the course's deploy story needs a correction.

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

> "function tools with graceful failure and barge-in protection"

| Claim | Status | Source |
|---|---|---|
| `@function_tool` decorator | ✅ | LK-TOOLS: *"Add tools to your agent class with the `@function_tool` decorator"* |
| `ToolError` for graceful failure | ✅ | LK-TOOLS: *"Raise the `ToolError` exception to return an error to the LLM in place of a response."* |
| `disallow_interruptions()` blocks barge-in | ✅ | LK-TOOLS: *"call `context.disallow_interruptions()` at the start of your tool to ensure user speech won't interrupt the agent's task."* |

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
| Per-turn metrics exist | ✅ | LK-EVENTS: *"`ChatMessage.metrics`... for per-turn latency."* |
| Per-turn metrics via `ChatMessage.metrics` (new) | ✅ | LK-EVENTS. Repo updated — see Finding 1 (resolved). |

> "a single-command deploy"

❓ See Finding 3. The repo says `lk agent create`. Not located in vendor docs.

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
| `lk agent create` | ❓ | Finding 3. |
| LiveKit Cloud's global infrastructure | ✅ | Proposal now matches LK-DEPLOY's "global network and infrastructure" phrasing. Repo top-level README also updated in commit 06dff7e. |

---

### Course Objectives

> "LiveKit Inference, a unified API for STT, LLM, and TTS with no per-provider keys"

| Claim | Status | Source |
|---|---|---|
| LiveKit Inference is a unified API | ✅ | LK-INFERENCE: *"LiveKit Inference provides access to many of the best models and providers for voice agents"* with single `AgentSession` configuring all three modalities. |
| Shorthand strings (e.g., `deepgram/nova-3:en`) | ✅ | LK-INFERENCE: *"As a shortcut, you can pass a model descriptor string directly"* + `stt="deepgram/nova-3:en"`. |
| "No per-provider keys needed" | ✅ | LK-INFERENCE: *"LiveKit Inference is included in LiveKit Cloud, and does not require any additional plugins"* + supported providers listed (OpenAI, Google, Deepgram, Cartesia, ElevenLabs, AssemblyAI, etc.). |

> "Solve the hard voice UX problems: semantic turn detection, false-interruption (backchannel) handling, and function tools the agent can call mid-conversation with graceful failure"

| Claim | Status | Source |
|---|---|---|
| Semantic turn detection (`MultilingualModel`) | ✅ | LK-TURN: documents `MultilingualModel()` with 14 supported languages and the conversational-context behavior. |
| `agent_false_interruption` event | ✅ | LK-EVENTS: *"user speech that initially appeared to interrupt the agent, but is determined not to be a true interruption."* |
| Function tools mid-conversation with graceful failure | ✅ | LK-TOOLS (see above). |

> "Ground responses in real data using Moss in-process semantic search (under 10 ms p99, zero network round-trips) via the `on_user_turn_completed` hook"

All four sub-claims ✅ via LK-NODES + MOSS-VOICE + MOSS-LLMS (covered above).

> "Instrument the STT → LLM → TTS pipeline with per-turn metrics, then deploy to LiveKit Cloud Agents with a single `lk agent create` command"

| Claim | Status | Source |
|---|---|---|
| Per-turn metrics | ✅ | LK-EVENTS. Repo updated to current pattern (`conversation_item_added` + `ChatMessage.metrics`). See Finding 1 (resolved). |
| `lk agent create` | ❓ | Finding 3. |

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

### Section 3 — Production Voice UX

> "Presentation: The hard UX problems in voice AI (10 min): LiveKit's semantic end-of-utterance model vs. VAD-only silence timeouts, false-interruption (backchannel) detection..."

| Claim | Status | Source |
|---|---|---|
| Semantic end-of-utterance vs VAD-only | ✅ | LK-TURN: *"a user might say 'I need to think about that for a moment' and then take a long pause. The user has more to say but a VAD-only system interrupts them anyway."* |
| `agent_false_interruption` event | ✅ | LK-EVENTS. |
| "Function tools behave differently in voice than in text" | ✗ | Instructor framing. Defensible (LK-TOOLS shows voice-specific patterns like `disallow_interruptions`) but not a direct quote. |

> "Exercise 3: Upgrade to semantic turn detection... swap in `MultilingualModel()`"

| Claim | Status | Source |
|---|---|---|
| `MultilingualModel()` | ✅ | LK-TURN. |
| **Repo passes it as `turn_detection=...` directly on AgentSession; current LK-VOICE-AI docs nest it as `turn_handling=TurnHandlingOptions(turn_detection=...)`.** | ⚠ | Finding 2. Either pattern likely still works, but the docs have moved to the nested form. |
| Natural-pause test phrase ("Hmm, I think the order ID is... A100") | 📁 | Repo example. |

> "Exercise 4: Add a function tool with graceful failure"

All four elements (`@function_tool`, `get_order_status`, `ToolError`, `disallow_interruptions`, `place_order`) verified ✅ via LK-TOOLS; specific function names (`get_order_status`, `place_order`) are 📁 repo.

> "Live coding: Wire false-interruption tracking — subscribe to the `agent_false_interruption` event..."

✅ LK-EVENTS confirms the event. "uh-huh" as the backchannel example is 📁 repo.

---

### Section 4 — Grounding Agents in Real Data with Moss

> "Presentation: Why voice agents need retrieval (10 min)..."

| Claim | Status | Source |
|---|---|---|
| Retrieve-as-tool adds an LLM round-trip | ✗ | Instructor framing. Logical conclusion from LK-TOOLS (tools require LLM decision) but not a quoted vendor claim. Defensible. |
| 300 to 900 ms dead air for hosted vector DBs | ✅ | MOSS-VOICE. |
| Moss under 10 ms p99 in-process, zero network hops | ✅ | MOSS-VOICE. |
| "Retrieve always, let the LLM decide what to use" principle | ✗ | Instructor framing. (The principle is the course's framing of the unconditional-retrieval pattern that LK-NODES does call out as a common RAG use of `on_user_turn_completed`.) Defensible. |

> "Exercise 5: Build a Moss index for Compass Coffee..."

| Claim | Status | Source |
|---|---|---|
| Moss SDK (`MossClient`) | ✅ | MOSS-LLMS: *"MossClient: Semantic search client for vector similarity operations"* (Python). |
| `build_index.py` script | 📁 | Repo file. |
| 15-document knowledge base | 📁 | Repo `data/kb.json`. |
| Alpha and top_k as tunable params | ✅ | MOSS-LLMS confirms `top_k` (default 3) and `alpha` (default 0.5) on `QueryOptions`. *"Hybrid search weighting. `0.0` = keyword only, `1.0` = semantic only."* |
| Compass Coffee brand | 📁 | Repo (fictional brand for the course). |

> "Exercise 6: Wire `on_user_turn_completed` for unconditional RAG..."

| Claim | Status | Source |
|---|---|---|
| Override `on_user_turn_completed` | ✅ | LK-NODES: *"Override this method to modify the content of the turn, cancel the agent's reply, or perform other actions."* |
| Inject results as `system` message into `turn_ctx` | ✅ | LK-NODES signature: `turn_ctx: ChatContext`. ChatContext supports message injection. |
| Exact queries ("refund policy", "Ethiopian coffee") | 📁 | Repo. |

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
| Per-turn STT/LLM/TTS metrics exist | ✅ | LK-EVENTS via `ChatMessage.metrics`. |
| Repo uses `conversation_item_added` + `session_usage_updated` | ✅ | Finding 1 resolved. LK-EVENTS confirms both events. |
| Cost tracking | 📁 | Repo's implementation, not a vendor doc claim per se. (Cost is derivable from token/audio metrics.) |
| "Observability before deploy, not after" principle | 📁 | Repo phrasing. Instructor framing. |

> "Exercise 7: Wire production metrics..."

| Claim | Status | Source |
|---|---|---|
| Event subscriptions: `conversation_item_added`, `session_usage_updated` | ✅ | LK-EVENTS. |
| Per-turn metric access via `ChatMessage.metrics` dict | ✅ | LK-EVENTS quotes `m.get("e2e_latency")` pattern verbatim. |
| `add_shutdown_callback` on JobContext | ❓ | I did not find a vendor doc page explicitly documenting this method. It is widely used in LiveKit Agents examples, so it almost certainly exists, but I could not pull an authoritative quote in this audit. |

> "Live walkthrough: Deploy with `lk agent create`..."

| Claim | Status | Source |
|---|---|---|
| `lk agent create` | ❓ | **Finding 3.** |
| Command builds container / registers worker / dispatches to rooms | 📁 | Repo claim only. |
| "LiveKit Cloud's global infrastructure" | ✅ | Phrasing now matches LK-DEPLOY. Resolved in both proposal and repo Section 4 README (06dff7e). |
| Set Moss secrets in Cloud dashboard | ✅ | LK-DEPLOY mentions secrets management: *"LiveKit Cloud encrypts and securely injects these values into your agent containers at runtime."* |

> "Teaser: Multi-agent handoffs in 30 lines..."

| Claim | Status | Source |
|---|---|---|
| Multi-agent handoff pattern (function tool returns next Agent) | ✅ | LiveKit Agents framework natively supports multi-agent handoffs per the LiveKit Agents README (https://github.com/livekit/agents): *"Multi-agent handoffs: Native support."* Specific `TriageAgent`/`BillingAgent` example is 📁 repo. |
| `chat_ctx` propagation | ✅ | LiveKit Agents framework feature; repo example shows the syntax. |
| "30 lines" | 📁 | Repo claim about the example length. |

> "Going-further callouts: wiring a visitor-facing frontend with the LiveKit JavaScript Client SDK (mic permission flow, AudioContext resume on Safari, an audio-reactive state machine across idle, listening, thinking, and speaking, and a token endpoint that hands a per-visitor join token to the browser), multi-agent handoffs in 30 lines, telephony via `lk sip`, vision-enabled realtime models, photoreal avatars (Tavus/Anam), self-hosting LiveKit Server"

| Claim | Status | Source |
|---|---|---|
| LiveKit JavaScript Client SDK exists | ✅ | https://docs.livekit.io/reference/client-sdk-js/ — official client SDK reference. Package is `livekit-client`. |
| Mic permission flow / AudioContext / state machine / token endpoint as the 4 needed pieces | ✗ | Instructor framing surfaced by the hb-agent build. Accurate description of what was actually needed, but not a quoted vendor claim. Acceptable as a teaser callout. |
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

2. **Verify `lk agent create` exists** (Finding 3). Run `lk agent --help`. If the command isn't there, identify the actual command and update both repo Section 4 README and Section 5 of the proposal.

3. **Decide on the entrypoint pattern** (Finding 2). Either:
   - Update the repo to use `AgentServer` + `@server.rtc_session()` to match current docs, or
   - Keep `WorkerOptions` and call out in Section 2 of the proposal that you're teaching the worker pattern deliberately (e.g., "the canonical worker-based pattern; LiveKit also supports a newer server-decorator pattern").

4. **Confirm `add_shutdown_callback`** is in the current vendor docs and quote-able for Section 5.

5. **Optional polish**:
   - ~~Replace "global edge network" with vendor phrasing~~ DONE. Proposal uses "LiveKit Cloud's global infrastructure" and repo README uses "global network and infrastructure" (commit 06dff7e).
   - Consider whether "production-ready" needs softening to "production-grade fundamentals" to set honest expectations.

The course's substantive material (semantic turn detection, function tools, the `on_user_turn_completed` retrieval pattern, the Moss in-process retrieval story, deployed-on-cloud finish) is all well-grounded in vendor docs. The metrics API (Finding 1) has been fixed. Remaining open items: the entrypoint scaffolding (Finding 2) and the deploy command (Finding 3), both repairable by updating the repo before the live session.
