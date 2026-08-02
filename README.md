# first-byte

Course repo for **Production Voice AI Agents with LiveKit** by Abhimanyu Selvan.

The name comes from a key voice-AI metric: TTS time-to-first-byte. Rather than chase a single headline number, the course measures the whole speech-end-to-first-audio path and breaks it down by stage — turn detection, transcription, retrieval, LLM time-to-first-token, and TTS TTFB — so you can see which one costs you the wait.

> **🎧 Hear the finished experience: [heartbyte.io](https://heartbyte.io).** The course builds a self-contained version with curated course data.

[`SYLLABUS.md`](./SYLLABUS.md) covers what the course teaches and how the two hours are structured. This README covers setup and the commands you run.

## Layout

```bash
first-byte/
├── pyproject.toml          # uv-managed deps for every section
├── SYLLABUS.md             # Course description, objectives, and schedule
├── AGENTS.md               # Instructions for coding agents working on this repo
├── .env.example            # Template for credentials
├── preflight.py            # Verifies your setup before class
├── sections/
│   ├── 01-hello-voice/     # First voice agent on LiveKit Inference
│   ├── 02-production-ux/   # Semantic turn detection
│   ├── 03-grounding-moss/  # RAG via on_user_turn_completed
│   └── 04-ship-it/         # Observability + lk agent create deploy
└── orb/                    # Visitor-facing webpage (Three.js orb, LiveKit JS SDK).
                            # Run locally to talk to your deployed agent.
```

The four directories map to course sections 2 through 5 (course Section 1 is the presentation and live demo, no code): `01-hello-voice` is course Section 2, `02-production-ux` is course Section 3, `03-grounding-moss` is course Section 4, and `04-ship-it` is course Section 5. Inside each directory, the local README labels itself by directory order (`Section 1` … `Section 4`) — when in doubt, use the path.

Each `sections/` directory has one self-contained `agent.py` you run with `uv run python sections/<dir>/agent.py dev`. They build on each other, but each is also runnable standalone. In `03-grounding-moss`, Exercise 5 is the commented `on_user_turn_completed` hook (uncomment to enable RAG). In `04-ship-it`, observability is already enabled: run it, inspect the per-turn metrics and shutdown usage summary, then deploy that same worker.

Exercise numbering follows the course listing: Exercises 1–2 (Section 2), Exercise 3 (Section 3), Exercises 4–5 (Section 4), and Exercise 6 (Section 5). This course builds a read-only agent.

The `orb/` directory is the browser client. After deployment, serve it locally with `python3 -m http.server 8000 --bind 127.0.0.1`. See `orb/README.md`.

## Pre-class setup

Complete this **before** the live session. Budget 30 to 40 minutes.

### 1. Tools

Install:

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- LiveKit CLI:
  - macOS: `brew install livekit-cli`
  - Linux: `curl -sSL https://get.livekit.io/cli | bash`
  - Windows: `winget install LiveKit.LiveKitCLI`

You'll also want **headphones with a microphone** for the live session. Laptop speakers plus the built-in mic cause audio feedback that makes voice testing unusable.

### 2. Accounts

- **LiveKit Cloud**: sign up for the Build plan (free, no credit card required) at [cloud.livekit.io](https://cloud.livekit.io). It covers STT, LLM, and TTS via LiveKit Inference, so no separate provider keys are needed. After signup, run `lk cloud auth` once to link the CLI.
- **Moss**: sign up at [moss.dev](https://moss.dev) (free tier is enough), create a project, copy the project ID and project key, and choose a unique lowercase index name. Any name works; `firstbyte-yourname` is a handy convention that also skips the extra confirmation prompt if you ever rebuild the index with `--replace`.

### 3. Repo

```bash
git clone https://github.com/diabhey/first-byte
cd first-byte
cp .env.example .env
# paste your LIVEKIT_* and MOSS_* values into .env
uv sync
```

### 4. Pre-flight check

```bash
uv run python preflight.py
```

This verifies Python, the LiveKit CLI, credentials, and required packages. Every check should be green before class.

## Running an agent

```bash
# Course Section 2
uv run python sections/01-hello-voice/agent.py dev

# Course Section 3
uv run python sections/02-production-ux/agent.py dev

# Course Section 4
uv run python sections/03-grounding-moss/agent.py dev

# Course Section 5
uv run python sections/04-ship-it/agent.py dev
```

Then open [Agents Playground](https://agents-playground.livekit.io), sign in to the same LiveKit project, and connect while the local worker is running. Stop earlier workers first so only one agent is available for dispatch.

## Deploying

In Section 5 (`sections/04-ship-it/`) you'll deploy the final agent to LiveKit Cloud Agents:

```bash
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
lk agent secrets
```

`lk agent create` builds, ships, and registers your agent worker on LiveKit's global network and securely injects the `MOSS_*` values from the repo-root `.env`. LiveKit ignores the project credentials it supplies automatically. Then follow `orb/README.md` to test the deployed agent. Subsequent updates use `lk agent deploy`.

## Resources

- [O'Reilly live event: Production Voice AI Agents with LiveKit](https://learning.oreilly.com/live-events/production-voice-ai-agents-with-livekit/0642572366988/)
- [LiveKit Agents docs](https://docs.livekit.io/agents/)
- [LiveKit Inference catalog](https://docs.livekit.io/agents/models/inference/)
- [LiveKit Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai-quickstart/)
- [LiveKit Agents Python SDK and examples](https://github.com/livekit/agents)
- [LiveKit Cloud Agents deployment](https://docs.livekit.io/agents/ops/deployment/)
- [LiveKit JS Client SDK](https://docs.livekit.io/reference/client-sdk-js/) (visitor-facing frontend)
- [Agents Playground](https://agents-playground.livekit.io/)
- [Moss docs](https://docs.moss.dev)
- [ArchByte architecture visualization](https://archbyte.heartbyte.io/)
- [`SYLLABUS.md`](./SYLLABUS.md) — course description, objectives, and schedule
- [`AGENTS.md`](./AGENTS.md) — guidance for coding agents editing this repo
