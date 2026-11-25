# Production Voice AI Agents with LiveKit

Build, test, and observe a production-oriented voice-agent prototype in two hours. Cloud deployment is walked through in class and completed as a gated follow-up; an optional prepared private demo can be shown only after rehearsal.

This syllabus describes the learning path and timing. Use the [README](./README.md) for setup, the [learner worksheet](./LEARNER_WORKSHEET.md) for evidence, and each section README for commands.

## Course description

Voice AI can use either a direct speech-to-speech model or a chained STT, LLM, and TTS pipeline. A direct model can minimize handoffs, while a chained pipeline makes individual stages replaceable and observable. The chained approach also exposes work that product teams must engineer: end-of-turn decisions, interruption behavior, retrieval, latency measurement, and deployment operations.

This course develops that chained path with LiveKit Agents. Learners start with a deliberately awkward agent, add LiveKit's local audio end-of-turn model and adaptive interruption handling, ground replies with a preloaded Moss index, and inspect per-turn timing and model usage. The final code is packaged for LiveKit Cloud, but the live class uses one local worker at a time to protect laptop memory and teaching time.

“Local” describes where the worker process runs. It does **not** mean fully offline: STT, LLM, and TTS still use LiveKit Inference, and Moss index setup/authentication uses Moss services. Only explicitly offline tests, model smoke checks, and `preflight.py --offline` avoid those service calls.

The course produces a **production-oriented prototype with a gated deployment path**. It does not claim production readiness. A real release still requires evaluation against product data, privacy and security review, token-service design, abuse controls, failure handling, load tests, capacity and cost planning, and an on-call/rollback process.

## Learning outcomes

By the end, learners can:

- Run a LiveKit agent locally through terminal Agent Console, with text mode as an audio-free fallback.
- Measure speech-end to first server audio across repeated turns and report a median instead of a single best run.
- Compare VAD-only endpointing with semantic end-of-turn detection and distinguish that decision from interruption handling.
- Explain when ambient every-turn retrieval fits and when a model-selected retrieval tool is more appropriate.
- Inspect Moss result scores, select a `min_score`, and verify both relevant and no-result paths before injecting context.
- Read final-transcript delay, retrieval time, LLM TTFT, TTS TTFB, end-of-turn/interruption model usage, and cumulative session usage without adding overlapping durations.
- Explain first-time `create` versus later `deploy`, and distinguish worker cold-start delay from per-turn response latency.
- Name the validation work that remains before a public production launch.

## Audience and prerequisites

The course is for backend/full-stack developers, solutions architects, and technical product builders who know Python and are comfortable with `async`/`await`.

Before class, learners need:

- Python 3.13 recommended (project range 3.11–3.14), `uv`, and LiveKit CLI 2.19.4+.
- A LiveKit Cloud project and a Moss project/index name.
- A supported Moss platform: Apple Silicon macOS 14+, Linux x86_64/ARM64 with glibc 2.28+, or Windows x64.
- Headphones and a microphone for voice mode. Text mode is available when audio is unavailable.
- The locked environment and model assets installed, plus a passing normal preflight.

Follow the [setup steps](./README.md#setup) when you're ready to run the exercises.

## Two-hour schedule

The first 105 minutes contain the scheduled instruction, exercises, and five-minute break. The final 15 minutes are protected recovery, worksheet completion, and questions. Optional topics do not consume that buffer.

### Section 1: Voice agents and the measured conversation (10 min)

- **Orientation (6 min):** chained and speech-to-speech paths, the course architecture, and the distinction between speech-end latency and individual component metrics.
- **Local demonstration (4 min):** run the completed agent through terminal Agent Console. Ask a known question and a follow-up, then show retrieval and timing evidence. A prerecorded browser-orb call is optional; a public or previously deployed agent is not assumed.

### Section 2: A deliberately imperfect voice agent (25 min)

Code: `sections/01-hello-voice/`

- **Framework map (7 min):** `Agent`, `AgentSession`, `JobContext`, `AgentServer`, LiveKit Inference, and the configurable `LLM_MODEL`.
- **Exercise 1 (8 min):** start one local worker with `lk agent console`, speak or type a question, and locate the transcript/reply.
- **Exercise 2 (7 min):** collect several complete-turn latency observations, pause mid-thought, and try to interrupt the non-interruptible baseline.
- **Checkpoint (3 min):** record the median and the reproducible baseline behavior in the worksheet.

### Section 3: Semantic turns and interruption handling (15 min)

Code: `sections/02-production-ux/`

- **Concept (5 min):** silence versus conversational completion, local `v1-mini` end-of-turn detection, and adaptive interruption handling.
- **Exercise 3 (8 min):** stop the first worker, run the second, repeat the same phrases, and compare end-of-turn behavior and interruption outcomes.
- **Checkpoint (2 min):** record which behavior changed and one remaining failure case.

### Break (5 min)

Stop the worker before the break. Keep the repository and worksheet open.

### Section 4: Grounding with retrieval rejection (30 min)

Code: `sections/03-grounding-moss/`

- **Design boundary (6 min):** ambient retrieval when most turns require the same data, versus a model-selected tool when retrieval is sparse. Moss reports low in-process query latency after an index is loaded; learners measure their own index rather than treating a vendor benchmark as a guarantee.
- **Exercise 4 (9 min):** inspect the prepared index or build a unique one before screen sharing; query known and irrelevant prompts, compare ranking settings, and select a `min_score`.
- **Exercise 5 (11 min):** run the agent with retrieval enabled and inspect the search, injected context, and reply for a known question and a follow-up. The retrieval off/on comparison is an optional exercise.
- **Transfer task (4 min):** add or replace one knowledge-base document, rebuild a course-owned scratch index, and predict which query should retrieve it. Learners may finish the rebuild after class if service latency would consume the session.

The grounded sections disable preemptive generation because their hook modifies the turn context on every reply. Otherwise LiveKit discards the speculative ungrounded output and generates again, wasting inference. This is a course-specific trade-off, not a rule that preemptive generation is always wrong.

### Section 5: Observe locally, understand deployment (20 min)

Code: `sections/04-ship-it/`

- **Exercise 6 (12 min):** run the completed local worker, inspect several per-turn records and cumulative usage, then disconnect and read the final summary. End-of-turn and interruption inference usage are part of the cost picture.
- **Deployment walkthrough (5 min):** explain the first-time `lk agent create` flow, secret names, health, logs, and later `lk agent deploy`. Do not start a Cloud build during class.
- **Production boundary (3 min):** separate Build-plan worker join/cold-start delay from per-turn `server_e2e`, and identify privacy, security, reliability, and public-token work that remains.

### Protected recovery, worksheet, and final questions (15 min)

Use this time for failed setup or service calls first. If the exercises finish on time, learners complete the worksheet: median latency, before/after behavior, retrieval rejection, dominant bottleneck, and their next validation step. Discuss optional browser/deployment work only after every core checkpoint is closed.

## Optional post-class lab: first Cloud deployment

After the local gates pass, learners can create a private Cloud deployment from `sections/04-ship-it`. First builds can outlast a classroom slot, and a Build-plan worker that scaled to zero can take 10–20 seconds to join its first session. Validate the deployment and browser orb separately.

## Instructor

**Abhimanyu Selvan** is an AI Systems Engineer. He runs [diabhey.com](https://diabhey.com), where he ships AI systems for engineering teams. His background includes safety-critical simulation, automated guided vehicles, medical IoT, cloud platforms, and developer advocacy.

He is also building HeartByte, an upcoming private voice diary for iPhone. The course uses a separate voice agent built with LiveKit and Moss. [HeartByte launch waitlist](https://heartbyte.io/)

Company affiliation: diabhey.
