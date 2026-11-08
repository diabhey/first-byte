# AGENTS.md

Course repo for the O'Reilly live course **Production Voice AI Agents with LiveKit**. Students clone this, run `preflight.py` before class, then work through `sections/` in order. Everything here is student-facing teaching material — optimize for readability in class, not cleverness.

This file is the canonical agent guide for any coding agent. Prefer it over scattered notes when editing this repo.

## Project overview

- Build path: Hello Voice → Production UX (turn detection) → Grounding with Moss → Ship It
- Reference experience: [heartbyte.io](https://heartbyte.io); rehearse the opening demo against the course orb before delivery
- Delivery plan: `TEACHING_GUIDE.md`; operational checks and deleted-agent recovery: `COURSE_READINESS.md`

## Course numbering

The course has 5 sections; Section 1 is presentation-only. Directories are off by one:

| Directory                    | Course section |
|------------------------------|----------------|
| `sections/01-hello-voice`    | Section 2      |
| `sections/02-production-ux`  | Section 3      |
| `sections/03-grounding-moss` | Section 4      |
| `sections/04-ship-it`        | Section 5      |

When editing docs, always say which numbering you're using.

## Setup commands

```bash
uv sync --locked                                                # deps (repo root)
uv run python preflight.py                                      # local + authenticated checks
uv run -m livekit.agents download-files                         # cache models before class
lk agent dev sections/<dir>/agent.py                       # run a section agent
uv run python sections/03-grounding-moss/build_index.py         # create Moss index
uv run python sections/03-grounding-moss/build_index.py --replace  # explicit rebuild
uv run python sections/03-grounding-moss/query_index.py "q" [--alpha X --top-k N]
cd sections/04-ship-it && lk agent create --secrets-file=../../.env  # first deploy
cd sections/04-ship-it && lk agent deploy                       # redeploys
```

Copy `.env.example` → `.env` for local credentials. Do not invent or commit secrets.

## Validated SDK baseline

The user-requested refresh upgrades the course to **LiveKit Agents 1.8.11**, with matching Silero in the root and deployable project. Use the committed lockfiles for reproducible classroom installs.

- Keep matching LiveKit framework/plugin versions. Revalidate both projects after upgrades.
- Use `AgentServer` and `@server.rtc_session()` in source. Run local development with LiveKit CLI 2.19.3+ and `lk agent dev sections/<dir>/agent.py`; preserve the legacy `cli.run_app(server)` path only for compatibility. The CLI generates an isolated dev deployment; select it explicitly in Agent Console and do not override it with production.
- Use `TurnHandlingOptions` and the built-in `inference.TurnDetector(version="v1-mini")` for audio-based turn detection and interruption settings; keep the deliberate non-interruptible Hello Voice baseline.
- Current observability uses `conversation_item_added` and `ChatMessage.metrics` for turn timing, `session_usage_updated` for cumulative model usage, and `ctx.add_shutdown_callback` for the final summary. Do not reintroduce deprecated `metrics_collected` or `metrics.UsageCollector`.
- The old text-turn-detector plugin and the `transformers<5` and `onnxruntime<1.26` caps belonged to the 1.3.x baseline and have been removed. Current ONNX Runtime wheels support macOS 14+ on Apple Silicon. Moss's current native wheels require a supported platform; Intel Macs need a Linux x86_64 environment.
- Python 3.13 is the classroom recommendation; the project supports 3.11–3.14.
- `sections/04-ship-it/` remains self-contained with its own `pyproject.toml`, `uv.lock`, Dockerfile, and `.dockerignore`. Keep the Dockerfile on Debian Trixie for native-wheel compatibility. Build for `linux/amd64` when validating on Apple Silicon.

## Moss safety

- `build_index.py` creates the configured index and refuses to overwrite it by default.
- Any valid Moss index name is accepted (lowercase letters, digits, hyphens); only the unedited `.env.example` placeholder is rejected. `firstbyte-<handle>` is a suggested convention, not a requirement.
- Deletion requires an explicit `--replace` flag. If the index name does not start with `firstbyte-`, `--replace` also requires interactive confirmation (retyping the index name) before deleting.
- `create_index` requires `model_id="moss-minilm"` — omitting it is a runtime error.

## Secrets

- `.env` is local only; never commit it or paste real keys into tracked files.
- Prefer exporting env vars per command over writing secrets into the tree.
- Local LiveKit CLI auth typically lives in `~/.livekit/cli-config.yaml`.

## Code style for this course

- Prefer clear, teachable diffs over clever refactors.
- Keep each section's `agent.py` runnable standalone.
- `03-grounding-moss`: Exercise 5 is the commented `on_user_turn_completed` in `agent.py` — leave it commented in the shipped tree; students uncomment live.
- `04-ship-it`: observability is active by default. Students run the complete grounded agent, inspect per-turn metrics and the shutdown usage summary, then deploy the same worker.
- Match existing patterns: short instructions, Inference model strings (`deepgram/...`, `openai/...`, `cartesia/...`), Silero VAD, and local audio turn detection via `inference.TurnDetector(version="v1-mini")`. Do not restore the deprecated `MultilingualModel` plugin.

## Doc sync

Keep documentation responsibilities clear:

- `SYLLABUS.md` — what the course covers and what students will learn. Prose only; no commands, no code blocks. Tracks the O'Reilly learning objectives; known listing/API differences are recorded in `COURSE_READINESS.md`.
- `README.md` — how to set up, run, and deploy. Owns the setup commands.
- `sections/*/README.md` — what to do in one section, and what to watch happen.

Commands belong in the README and the section READMEs. The syllabus links to them instead of repeating them.

Any change to exercises, APIs, or the deploy story must be reflected in:

1. the section README
2. the section `agent.py`

When docs and code disagree, code reality wins; then update the docs.

## Testing

- Voice testing: headphones + mic; run `lk agent dev sections/<dir>/agent.py`, open [Agent Console](https://docs.livekit.io/testing/agent-console/), and select the exact `dev-...` deployment printed by the CLI. Do not use default production/legacy Playground automatic dispatch for this worker.
- For metrics and usage verification, use `sections/04-ship-it`; inspect turn timing, cumulative usage updates, and the session summary on shutdown.
- Mic-less smoke test (optional): publish synthetic speech into a fresh room with `lk room join --publish`, with these rules:
  - Pad clips with trailing silence so VAD sees end-of-speech.
  - The publisher must be the **first** participant in the room (RoomIO links to the first mic).
  - Verify replies via transcription streams, audio, or `04-ship-it` timing/usage output; worker registration alone does not prove a voice conversation.

## Out of scope

- Do not claim live readiness from offline checks alone. Complete the course rehearsal after SDK, model, or deployment changes.
- Don't turn teaching stubs into production frameworks.
- Don't run `build_index.py` against production Moss indexes.
