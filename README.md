# first-byte

Course repo for **Production Voice AI Agents with LiveKit** by Abhimanyu Selvan.

The name comes from a key voice-AI metric: TTS time-to-first-byte. Rather than chase a single headline number, the course measures the whole speech-end-to-first-audio path and breaks it down by stage — turn detection, transcription, retrieval, LLM time-to-first-token, and TTS TTFB — so you can see which one costs you the wait.

> The course builds a self-contained HeartByte voice agent with curated course data and a local browser orb. [heartbyte.io](https://heartbyte.io) is the reference experience; verify the live demo during the [course rehearsal](./COURSE_READINESS.md).

[`SYLLABUS.md`](./SYLLABUS.md) covers what the course teaches and how the two hours are structured. This README covers setup and the commands you run. [`COURSE_READINESS.md`](./COURSE_READINESS.md) covers the rehearsal and rebuilding a deleted Cloud agent.

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

The four directories map to course sections 2 through 5 (course Section 1 is the presentation and live demo, no code): `01-hello-voice` is course Section 2, `02-production-ux` is course Section 3, `03-grounding-moss` is course Section 4, and `04-ship-it` is course Section 5. Each section README states both its course section and directory order.

Each `sections/` directory has one self-contained `agent.py` you run with `lk agent dev sections/<dir>/agent.py`. They build on each other, but each is also runnable standalone. In `03-grounding-moss`, Exercise 5 is the commented `on_user_turn_completed` hook (uncomment to enable RAG). In `04-ship-it`, observability is already enabled: run it, inspect the per-turn metrics and shutdown usage summary, then deploy that same worker.

Exercise numbering follows the course listing: Exercises 1–2 (Section 2), Exercise 3 (Section 3), Exercises 4–5 (Section 4), and Exercise 6 (Section 5). This course builds a read-only agent.

The `orb/` directory is the browser client. After deployment, serve it locally with `python3 -m http.server 8000 --bind 127.0.0.1`. See `orb/README.md`.

## Pre-class setup

Complete this **before** the live session. Budget 30 to 40 minutes.

### 1. Tools

Install:

- Python 3.13 recommended (supported project range: 3.11–3.14)
- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- LiveKit CLI **2.19.3 or newer** (`lk --version`):
  - macOS: `brew install livekit-cli`; existing installations: `brew update` then `brew upgrade livekit-cli`
  - Linux: `curl -sSL https://get.livekit.io/cli | bash`
  - Windows: `winget install LiveKit.LiveKitCLI`

Moss includes a native library. Use macOS 14 or newer on Apple Silicon, Linux (x86_64 or ARM64, glibc 2.28+), or Windows x64; the Linux deployment image is Debian Trixie. Intel Mac users should prepare a Linux environment before class and confirm microphone/browser connectivity during rehearsal. Docker Desktop on an Intel Mac can run the deployment image; on Apple Silicon, use `--platform linux/amd64` when checking that image.

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
uv python install 3.13
uv sync --locked --python 3.13
```

### 4. Download model files before class

```bash
uv run -m livekit.agents download-files
```

This prepares SDK/plugin assets before the live session. The local `v1-mini` turn model is bundled in `livekit-local-inference`, while Silero provides its VAD model with the plugin. Allow time and disk space for installation and model initialization. Do this again after a dependency update.

### 5. Pre-flight check

```bash
uv run python preflight.py
```

This checks Python, the LiveKit CLI, credentials, required packages, and authenticated read requests to LiveKit and Moss. Keep secrets in `.env` or export the same variables in your shell. All checks must pass before class. `uv run python preflight.py --offline` checks local setup without contacting those services; it does not prove authentication, model availability, audio, or deployment.

Build your Moss index in course Section 4, following its [README](./sections/03-grounding-moss/README.md). Preflight verifies account access; a successful voice conversation and Cloud deployment still need the [rehearsal checklist](./COURSE_READINESS.md).

## Running an agent

```bash
# Course Section 2
lk agent dev sections/01-hello-voice/agent.py

# Course Section 3
lk agent dev sections/02-production-ux/agent.py

# Course Section 4
lk agent dev sections/03-grounding-moss/agent.py

# Course Section 5
lk agent dev sections/04-ship-it/agent.py
```

The CLI prints a development deployment such as `Using deployment [dev-<random>]` and an Agent Console link. Open that link, or launch [Agent Console](https://docs.livekit.io/testing/agent-console/) from the same project’s Agents dashboard, and select the **exact development deployment printed in your terminal** before starting a session. The default production deployment and older Playground automatic dispatch do not target this isolated dev worker. Stop the earlier section’s worker before switching sections, and select the newly printed dev deployment.

Use the generated development deployment for class. Overriding it with `--deployment production` can mix local testing with existing Cloud workers.

For an older CLI, `uv run python sections/<dir>/agent.py dev` remains a legacy compatibility path. Upgrade to the required CLI for the current course workflow.

## Deploying

In Section 5 (`sections/04-ship-it/`) you'll deploy the final agent to LiveKit Cloud Agents:

```bash
lk cloud auth
lk project list
lk project set-default "<your-course-project-name>"
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
lk agent secrets
lk agent status
```

`lk agent create` builds, ships, and registers your agent worker on LiveKit's global network and securely injects the `MOSS_*` values from the repo-root `.env`. LiveKit ignores the project credentials it supplies automatically. The CLI writes your new agent ID and project to the gitignored `livekit.toml`. Follow [`orb/README.md`](./orb/README.md) to test the deployed agent. Subsequent updates use `lk agent deploy`. If the agent was deleted, follow [the rebuild steps](./COURSE_READINESS.md#rebuild-a-deleted-cloud-agent); `deploy` cannot restore a deleted ID.

## Validated dependency baseline

The course uses LiveKit Agents and Silero **1.8.11**, with matching versions in both committed lockfiles. Semantic turn detection uses the SDK’s local audio model, `inference.TurnDetector(version="v1-mini")`; the deprecated text turn-detector plugin is no longer needed. The examples use `AgentServer`, `TurnHandlingOptions`, `conversation_item_added`, and `session_usage_updated`. Install from the locks for class; dependency upgrades require another rehearsal. The [readiness record](./COURSE_READINESS.md) distinguishes automated checks from live voice and deployment checks.

## Resources

- [O'Reilly live event: Production Voice AI Agents with LiveKit](https://learning.oreilly.com/live-events/production-voice-ai-agents-with-livekit/0642572366988/)
- [LiveKit Agents docs](https://docs.livekit.io/agents/)
- [LiveKit Inference catalog](https://docs.livekit.io/agents/models/inference/)
- [LiveKit Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai-quickstart/)
- [LiveKit Agents Python SDK and examples](https://github.com/livekit/agents)
- [LiveKit Cloud Agents deployment](https://docs.livekit.io/deploy/agents/)
- [LiveKit JS Client SDK](https://docs.livekit.io/reference/client-sdk-js/) (visitor-facing frontend)
- [Agent Console](https://docs.livekit.io/testing/agent-console/)
- [Moss docs](https://docs.moss.dev)
- [ArchByte architecture visualization](https://archbyte.heartbyte.io/)
- [`SYLLABUS.md`](./SYLLABUS.md) — course description, objectives, and schedule
- [`TEACHING_GUIDE.md`](./TEACHING_GUIDE.md) — presentation talking points, exercise checkpoints, and fallback demos
- [`AGENTS.md`](./AGENTS.md) — guidance for coding agents editing this repo
