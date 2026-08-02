# Production Voice AI Agents with LiveKit

Build and deploy a real-time voice agent in two hours.

This is the course outline: what it covers, what you'll learn, and how the two
hours are structured. For setup and the commands you run in class, see the
[README](./README.md). Each directory under `sections/` has its own README for
the exercise it holds.

## Course description

There are now two practical architectures for voice AI.

Speech-to-speech models handle audio in and out directly: the lowest-latency
path between user audio and agent audio, but opaque on what happens between,
hard to debug, and locked to one provider's model and pricing.

A chained STT, LLM, TTS pipeline is the path many production deployments still
take, because each stage is independently swappable, debuggable, and
instrumentable. The trade-off is that you have to engineer the things
speech-to-speech hides: turn detection that doesn't cut people off mid-sentence,
retrieval that grounds answers without burning 300 to 900 ms on a network hop to
a hosted vector database, observability that lets you defend your latency budget
under load, and a deploy story that doesn't end at `python agent.py` on your
laptop.

This hands-on course is the operational playbook for the chained-pipeline path
on LiveKit Agents. You'll build a production-ready voice agent starting from
your first spoken interaction on a laptop and ending with a deployed agent on
LiveKit Cloud. The agent you build is the same one running live at
[heartbyte.io](https://heartbyte.io), the instructor's own voice agent. You'll
work through LiveKit's semantic end-of-turn model, in-process retrieval via Moss
(under 10 ms p99, zero network round-trips) on every turn, per-turn
observability across the STT, LLM, and TTS pipeline, and a single-command
deploy. The organizing constraint throughout is an 800 ms first-byte budget you
can defend under production load, not a demo number.

Every exercise runs against real LiveKit infrastructure. The final deploy
command ships your agent to a global edge network in one step. By the end,
you'll have a working voice agent and the operational playbook to ship it.

## What you'll learn

- Build a real-time voice agent on LiveKit Agents using LiveKit Inference, a
  unified API for STT, LLM, and TTS with no per-provider keys
- Upgrade from VAD-only silence timeouts to LiveKit's semantic end-of-turn model
  so the agent stops cutting people off mid-thought
- Ground every turn in your own data without breaking the conversational feel.
  Moss runs semantic search in-process (sub-10 ms), so retrieval fits inside the
  natural turn-taking pause instead of adding the 300 to 900 ms of dead air a
  cloud vector database would
- Instrument the STT → LLM → TTS pipeline with per-turn metrics, then deploy to
  LiveKit Cloud Agents with a single command

## Who this course is for

- Backend and full-stack developers building voice-powered products who want to
  go beyond a basic speech-to-text demo to a production system
- Solutions architects evaluating voice AI infrastructure who need to understand
  the real latency, scaling, and reliability trade-offs
- Technical founders and CTOs who want to ship a voice AI product that handles
  real customers without a dedicated infrastructure team

## What you need

Knowledge: working Python, including comfort with `async def` and `await`.

Accounts, both free:

- **LiveKit Cloud** on the Build plan. No credit card required. It covers STT,
  LLM, and TTS through LiveKit Inference, so you need no separate provider keys.
- **Moss**. The free tier is enough.

Local environment:

- Python 3.11 or newer, [uv](https://docs.astral.sh/uv/) for dependency
  management, and the [LiveKit CLI](https://docs.livekit.io/home/cli/)
- Headphones with a microphone. Laptop speakers plus a built-in mic cause audio
  feedback that makes voice testing unusable
- A recent browser for the LiveKit Agents Playground, a code editor, and stable
  broadband — a wired connection is recommended for the live session

Install steps, credentials, and the pre-flight check are in the
[README](./README.md#pre-class-setup). Budget 30 to 40 minutes and finish it
before the live session; if anything fails, post in the course Discord at least
24 hours before class.

## Schedule

Five sections over two hours. Section 1 is presentation and demo only, so the
four coding sections map to directories that are numbered one lower — course
Section 2 is the first directory.

### Section 1: Voice agents and the first-byte problem (15 min)

- **Presentation (10 min).** What a voice agent is and what this course covers:
  the STT, LLM, TTS pipeline and what plugs in at each stage (voice activity
  detection, semantic turn detection, function tools, retrieval, audio
  synthesis), where each component runs, and the course map — Hello Voice,
  Production UX, Grounding with Moss, Ship It.
- **Demo (5 min).** The finished system: a live voice call to the HeartByte orb
  at [heartbyte.io](https://heartbyte.io), the same agent you'll build,
  retrieving from Moss in-process and holding the 800 ms first-byte target.

### Section 2: Your first voice agent (30 min)

Code: `sections/01-hello-voice/`

- **Presentation (10 min).** LiveKit Agents fundamentals: `Agent`,
  `AgentSession`, `JobContext`, `WorkerOptions`, the entrypoint pattern, and how
  LiveKit Inference unifies STT, LLM, and TTS behind shorthand model strings.
- **Exercise 1 (10 min).** Boot the dev stack and have your first voice
  conversation. Connect through the Agents Playground, speak to the agent, and
  inspect the trace: Silero VAD, Deepgram nova-3, GPT-4o-mini, Cartesia sonic-3.
- **Exercise 2 (5 min).** Measure your first-byte latency. Time the gap from
  your last word to first audio out, speak over the agent mid-reply, and stay
  silent for a beat.
- **Q&A (5 min).**

### Section 3: Turn detection that doesn't cut people off (15 min)

Code: `sections/02-production-ux/`

- **Presentation (5 min).** Why VAD-only silence timeouts are wrong for voice:
  the difference between "they stopped making sound" and "they finished their
  thought," LiveKit's semantic end-of-turn model, and why this single change is
  the difference between an agent that feels rude and one that feels human.
- **Exercise 3 (8 min).** Upgrade to semantic turn detection. Test phrases with
  natural pauses, compare side by side against VAD-only behaviour, and watch the
  agent wait instead of barging in.
- **Q&A (2 min),** then a five-minute break.

### Section 4: Grounding agents in real data with Moss (30 min)

Code: `sections/03-grounding-moss/`

- **Presentation (5 min).** Why voice agents need retrieval: why
  retrieve-as-tool patterns add an extra LLM round-trip you can't afford in
  voice, how hosted vector databases add 300 to 900 ms of dead air per turn
  against Moss's claimed sub-10 ms p99 in-process with zero network hops, and
  the principle of retrieving always and letting the LLM decide what to use.
- **Exercise 5 (10 min).** Build a Moss index for the HeartByte orb. Install the
  Moss SDK, build the index from the shipped knowledge base, query it directly,
  and inspect scores while tuning alpha and top-k.
- **Exercise 6 (12 min).** Wire `on_user_turn_completed` for unconditional
  retrieval. Override the hook, query Moss on every user turn, inject the
  results as a system message, then ask about HeartByte and watch grounded
  answers arrive in real time.
- **Q&A (3 min).**

### Section 5: Observability and deployment (20 min)

Code: `sections/04-ship-it/`

- **Presentation (5 min).** Observability for voice agents: the per-turn latency
  breakdown across STT first byte, LLM time-to-first-token, and TTS first audio
  chunk; session-level usage rollups; and the principle of observability
  *before* deploy, not after.
- **Exercise 7 (7 min).** Wire production metrics. Read per-turn latency from
  `ChatMessage.metrics`, collect cumulative model usage, and register a shutdown
  callback for an end-of-session summary.
- **Live walkthrough (5 min).** Deploy with one command. It builds, ships, and
  registers your agent on LiveKit Cloud's global infrastructure; the section
  directory is pre-staged as a self-contained deployable project so the build
  hits the LiveKit Cloud cache and stays inside the demo window. Then serve the
  included orb page locally, paste in a LiveKit token, and tap the orb to talk
  to your cloud-deployed agent end to end — the same three pieces you need in
  production: a static page, LiveKit Cloud, and an agent worker.
- **Going further (3 min).** Wiring the visitor-facing half on Cloudflare Pages
  with per-visitor tokens minted server-side; the three security layers a public
  voice page needs (origin checks on the token endpoint, per-visitor room names,
  and edge rate limiting); the audio-reactive UI state machine driven from
  analyser taps on both microphone and agent audio; multi-agent handoffs;
  telephony over SIP; vision-enabled realtime models; photoreal avatars; and
  self-hosting LiveKit Server.
- **Final Q&A (5 min).**

## Instructor

**Abhimanyu Selvan** is an AI Systems Engineer. He runs
[diabhey.com](https://diabhey.com), where he ships production AI systems for
engineering teams: agent orchestration, event-driven pipelines, and distributed
systems. Previously he spent over a decade in safety-critical engineering before
moving into AI, including Boeing 787 flight simulators at Lockheed Martin,
automated guided vehicles at Oceaneering, medical IoT at Onera Health, and Otomi
(now the Akamai App Platform) at RedKubes. He later led developer advocacy
globally at DigitalOcean. In his spare time he's building a spiritual version of
himself at [heartbyte.io](https://heartbyte.io).

Company affiliation: diabhey.
