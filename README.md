# first-byte

Course repo for **Production Voice AI Agents with LiveKit** by [Abhimanyu Selvan](https://diabhey.com).

The name comes from TTS time-to-first-byte. The course measures the whole wait, from the moment you stop speaking to the first audio back, and shows which stage spent it.

[`SYLLABUS.md`](./SYLLABUS.md) covers what the course teaches. This README covers setup and the commands you run.

## Sections

Course Section 1 is the talk and demo. It has no code, so the folders are numbered one lower.

| Course section | Folder | What you build |
| --- | --- | --- |
| 2 | [`01-hello-voice`](./sections/01-hello-voice/README.md) | A first voice agent, and the measured wait |
| 3 | [`02-production-ux`](./sections/02-production-ux/README.md) | Semantic turn detection and tuned interruptions |
| 4 | [`03-grounding-moss`](./sections/03-grounding-moss/README.md) | Moss retrieval on every spoken turn |
| 5 | [`04-ship-it`](./sections/04-ship-it/README.md) | A LiveKit Cloud deploy, inspected in the dashboard |

Each folder has one standalone `agent.py`. The [`orb`](./orb/README.md) is the browser page you use to call the deployed agent at the end.

Exercises follow the course listing: 1–2 in Section 2, 3 in Section 3, 4–5 in Section 4, and 6 in Section 5.

## Pre-class setup

Do this before the live session. Budget 30 to 40 minutes.

### 1. Tools

- Python 3.13 (3.11–3.14 works)
- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/) 2.19.3 or newer (`lk --version`)
  - macOS: `brew install livekit-cli`, or `brew update && brew upgrade livekit-cli`
  - Linux: `curl -sSL https://get.livekit.io/cli | bash`
  - Windows: `winget install LiveKit.LiveKitCLI`
- Headphones with a microphone. Laptop speakers and a built-in mic feed back into each other.

Moss ships a native library. Use macOS 14+ on Apple Silicon, Linux (x86_64 or ARM64, glibc 2.28+), or Windows x64. On an Intel Mac, prepare a Linux environment before class.

### 2. Accounts

- **LiveKit Cloud**: the free Build plan at [cloud.livekit.io](https://cloud.livekit.io). LiveKit Inference covers STT, LLM, and TTS, so you need no provider keys. Run `lk cloud auth` once.
- **Moss**: the free tier at [moss.dev](https://moss.dev). Copy the project ID and key, and pick a lowercase index name such as `firstbyte-yourname`.

### 3. Repo

```bash
git clone https://github.com/diabhey/first-byte
cd first-byte
cp .env.example .env
# paste your LIVEKIT_* and MOSS_* values into .env
uv python install 3.13
uv sync --locked --python 3.13
```

### 4. Model files

```bash
uv run -m livekit.agents download-files
```

Run this again after a dependency update.

### 5. Pre-flight check

```bash
uv run python preflight.py
```

[`preflight.py`](./preflight.py) checks Python, the CLI, your credentials, the installed packages, and live access to LiveKit and Moss. Every check must pass. `--offline` skips the network checks.

Build your Moss index before class. The steps are in [Grounding with Moss](./sections/03-grounding-moss/README.md#build-the-index).

## Running an agent

```bash
lk agent console sections/01-hello-voice/agent.py
lk agent console sections/02-production-ux/agent.py
lk agent console sections/03-grounding-moss/agent.py
lk agent console sections/04-ship-it/agent.py
```

The console runs the agent on your machine with your microphone and speakers. Talk in the terminal. Press `m` to mute, `ctrl+t` to type, `?` for shortcuts, and `q` to quit. Quit one section before you start the next.

Sections 2 to 4 read the repo-root `.env`. Once Ship It has a `livekit.toml`, its console reads `sections/04-ship-it/.env.local` instead. [Ship It](./sections/04-ship-it/README.md#local-fallback) has the step.

## Deploying

Course Section 5 deploys the final agent to LiveKit Cloud. The commands are in [Ship It](./sections/04-ship-it/README.md#2-deploy). Then call it from the [orb](./orb/README.md) and [inspect the call](./sections/04-ship-it/README.md#4-inspect-the-call) in the dashboard.

## Dependency baseline

LiveKit Agents and Silero **1.8.11**, pinned in both lockfiles. Turn detection uses the SDK's local audio model, `inference.TurnDetector(version="v1-mini")`. After an upgrade, repeat the voice and deploy checks.

## Resources

- [O'Reilly live event](https://www.oreilly.com/live-events/production-voice-ai-agents-with-livekit/0642572366988/)
- [LiveKit Agents docs](https://docs.livekit.io/agents/)
- [LiveKit Inference models](https://docs.livekit.io/agents/models/inference/)
- [LiveKit Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/)
- [LiveKit Agents Python SDK](https://github.com/livekit/agents)
- [Deploying agents to LiveKit Cloud](https://docs.livekit.io/deploy/agents/)
- [LiveKit JS client SDK](https://docs.livekit.io/reference/client-sdk-js/)
- [`lk agent` commands](https://docs.livekit.io/reference/developer-tools/livekit-cli/agent/)
- [Moss docs](https://docs.moss.dev/docs)
- [ArchByte architecture visualization](https://diabhey.com/tools/archbyte)
- [`SYLLABUS.md`](./SYLLABUS.md): course outline and schedule
- [`AGENTS.md`](./AGENTS.md): notes for coding agents editing this repo
