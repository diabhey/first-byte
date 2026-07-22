# first-byte

Course repo for **Production Voice AI Agents with LiveKit** by Abhimanyu Selvan.

The name comes from the metric that decides whether voice AI feels real: TTS first-byte latency. Every choice in this course is in service of staying under 800 ms first audio out.

> **🎧 Hear the finished thing first: [heartbyte.io](https://heartbyte.io).** Tap the orb and talk to the production deployment of the exact agent this course builds. By the end of Section 5 you'll have deployed your own.

## Layout

```
first-byte/
├── pyproject.toml          # uv-managed deps for every section
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

The four directories map to course sections 2 through 5 (course Section 1 is the presentation and live demo, no code): `01-hello-voice` is Section 2, `02-production-ux` is Section 3, `03-grounding-moss` is Section 4, and `04-ship-it` is Section 5.

Each `sections/` directory is a self-contained `agent.py` you run with `uv run python sections/<section>/agent.py dev`. They build on each other, but each is also runnable standalone. Sections 4 and 5 also ship an `agent_start.py` stub for the in-class exercises — the parts you'll wire live are marked TODO, and the finished `agent.py` is the reference.

Exercise numbering follows the official course listing: Exercises 1–2 (Section 2), Exercise 3 (Section 3), Exercises 5–6 (Section 4), Exercise 7 (Section 5). There is deliberately no Exercise 4 — the function-tools exercise was cut when the course was scoped to match the production HeartByte orb, which is read-only (see the note at the end of `sections/02-production-ux/README.md`).

The `orb/` directory is the front-end half — a single HTML page using the LiveKit JS SDK and a Three.js sphere. After you've deployed your agent on LiveKit Cloud in Section 5, you'll serve this page locally (`python3 -m http.server`) and tap the orb to talk to your cloud agent. See `orb/README.md` for the three-step setup.

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
- **Moss**: sign up at [moss.dev](https://moss.dev) (free tier is enough), create a project, copy the project ID and project key. Pick an index name like `firstbyte-{your-handle}`.

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

This script verifies LiveKit Cloud auth, Moss credentials, dependency install, and Python version. Every check should be green before class. If anything fails, post in the course Discord at least 24 hours before the live session.

## Running an agent

```bash
# Section 1
uv run python sections/01-hello-voice/agent.py dev

# Section 2
uv run python sections/02-production-ux/agent.py dev

# (etc.)
```

Then open [agents-playground.livekit.io](https://agents-playground.livekit.io) in your browser and connect to your local agent. Talk to it.

## Deploying

In Section 5 (`sections/04-ship-it/`) you'll deploy the final agent to LiveKit Cloud Agents:

```bash
cd sections/04-ship-it
lk agent create
```

That single command builds, ships, and registers your agent worker on LiveKit's global network and infrastructure. Set your `MOSS_*` secrets in the LiveKit Cloud dashboard, then serve the orb page from `orb/` locally with a 24-hour token pasted into `config.js` and talk to your cloud agent end to end (see `orb/README.md`). For subsequent updates, `lk agent deploy` reads `livekit.toml` and rolls a new container without touching the dashboard secrets.

## Resources

- [LiveKit Agents docs](https://docs.livekit.io/agents/)
- [LiveKit Inference catalog](https://docs.livekit.io/agents/models/inference/)
- [LiveKit Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai-quickstart/)
- [LiveKit Agents Python SDK and examples](https://github.com/livekit/agents)
- [LiveKit Cloud Agents deployment](https://docs.livekit.io/agents/ops/deployment/)
- [LiveKit JS Client SDK](https://docs.livekit.io/reference/client-sdk-js/) (visitor-facing frontend)
- [Agents Playground](https://agents-playground.livekit.io/)
- [Moss docs](https://docs.moss.dev)
- [ArchByte architecture visualization](https://archbyte.heartbyte.io/)
