# AGENTS.md

Course repo for the O'Reilly live course **Production Voice AI Agents with LiveKit**. Students clone this, run `preflight.py` before class, then work through `sections/` in order. Everything here is student-facing teaching material — optimize for readability in class, not cleverness.

This file is the canonical agent guide for any coding agent. Prefer it over scattered notes when editing this repo.

## Project overview

- Build path: Hello Voice → Production UX (turn detection) → Grounding with Moss → Ship It
- Rehearse the opening demo with the course agent. HeartByte is the instructor’s separate iPhone voice diary project. [HeartByte launch waitlist](https://heartbyte.io/)
- Instructor notes (delivery plan, operational checks, deleted-agent recovery) live in the gitignored `prep/` folder and must stay out of commits

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
uv sync --frozen                                                # deps (repo root)
uv run python preflight.py                                      # local + authenticated checks
uv run -m livekit.agents download-files                         # plugin download_files(); Silero is a no-op on 1.8.12
lk agent console sections/<dir>/agent.py                        # lowest-overhead local voice test
lk agent console --text sections/<dir>/agent.py                 # audio-free fallback
uv run python sections/03-grounding-moss/build_index.py         # create Moss index
uv run python sections/03-grounding-moss/build_index.py --replace  # explicit rebuild
uv run python sections/03-grounding-moss/query_index.py "q" [--alpha X --top-k N --min-score X]
cd sections/04-ship-it && lk agent create --secrets-file=../../.env  # first deploy
cd sections/04-ship-it && lk agent deploy                       # redeploys
```

Copy `.env.example` → `.env` for local credentials. Do not invent or commit secrets.

## Validated SDK baseline

The final November 2026 refresh upgrades the course to **LiveKit Agents 1.8.12**, matching Silero, and **Moss 1.24** in the root and deployable project. Use the committed lockfiles for reproducible classroom installs.

- Keep matching LiveKit framework/plugin versions. Revalidate both projects after upgrades.
- Use `AgentServer` and `@server.rtc_session()` in source. The validated instructor CLI is 2.19.4. Prefer `lk agent console sections/<dir>/agent.py` for local voice testing: it talks directly to the laptop microphone and speakers without a browser or LiveKit room. Use `--text` as the audio-free fallback. Reserve `lk agent dev` plus Agent Console for an explicit room/deployment test.
- Use `TurnHandlingOptions` and the built-in `inference.TurnDetector(version="v1-mini")` for audio-based turn detection. Keep the deliberate non-interruptible Hello Voice baseline, then teach adaptive interruption in later sections.
- Keep preemptive generation enabled for the Production UX comparison. Disable it in the grounded sections because `on_user_turn_completed` changes the chat context; otherwise speculative output is discarded and regenerated.
- Current observability uses `conversation_item_added` and `ChatMessage.metrics` for turn timing, `session_usage_updated` for cumulative model usage, and `ctx.add_shutdown_callback` for the final summary. The usage summary includes end-of-turn and interruption requests as well as LLM/STT/TTS use. Do not reintroduce deprecated `metrics_collected` or `metrics.UsageCollector`.
- The LLM is configured through `LLM_MODEL`; keep the same documented default across all standalone sections and the deployment project.
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
- `03-grounding-moss`: Demo 5 uses the instructor’s retrieval-enabled checkout. A fresh learner checkout can start with the `on_user_turn_completed` method commented out for the optional off/on exercise. Check the startup status and use a spoken turn to verify injection.
- `04-ship-it`: observability is active by default. Students run the complete grounded agent, inspect per-turn metrics and the shutdown usage summary, then deploy the same worker.
- Match existing patterns: short instructions, Inference model strings (`deepgram/...`, `google/...`, `cartesia/...`), Silero VAD, and local audio turn detection via `inference.TurnDetector(version="v1-mini")`. Do not restore the deprecated `MultilingualModel` plugin.

## Doc sync

Keep documentation responsibilities clear:

- `SYLLABUS.md` — what the course covers and what students will learn. Prose only; no commands, no code blocks. Tracks the O'Reilly learning objectives; known listing/API differences are recorded in `prep/COURSE_READINESS.md`.
- `README.md` — how to set up, run, and deploy. Owns the setup commands.
- `sections/*/README.md` — what to do in one section, and what to watch happen.

Commands belong in the README and the section READMEs. The syllabus links to them instead of repeating them.

Any change to exercises, APIs, or the deploy story must be reflected in:

1. the section README
2. the section `agent.py`

When docs and code disagree, code reality wins; then update the docs.

## Testing

- Low-memory voice testing: headphones + mic; run one `lk agent console sections/<dir>/agent.py` process at a time. This is local execution, not offline execution: LiveKit Inference and Moss still require credentials and network access. Do not run a browser orb, local Docker build, model download, or Cloud build concurrently while screen sharing.
- Room testing (optional): run `lk agent dev sections/<dir>/agent.py`, open [Agent Console](https://docs.livekit.io/testing/agent-console/), and select the exact `dev-...` deployment printed by the CLI. Do not use default production/legacy Playground automatic dispatch for this worker.
- For metrics and usage verification, use `sections/04-ship-it`; inspect turn timing, cumulative usage updates, and the session summary on shutdown.
- Mic-less smoke test (optional): publish synthetic speech into a fresh room with `lk room join --publish`, with these rules:
  - Pad clips with trailing silence so VAD sees end-of-speech.
  - The publisher must be the **first** participant in the room (RoomIO links to the first mic).
  - Verify replies via transcription streams, audio, or `04-ship-it` timing/usage output; worker registration alone does not prove a voice conversation.

## Out of scope

- Do not claim live readiness from offline checks alone. Complete the course rehearsal after SDK, model, or deployment changes.
- Do not create or build a Cloud deployment during the live class. After the complete local flow passes, rehearse the first private deployment off-camera and warm it shortly before any optional Cloud demonstration.
- Don't turn teaching stubs into production frameworks.
- Don't run `build_index.py` against production Moss indexes.
