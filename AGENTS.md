# AGENTS.md

Course repo for the O'Reilly live course **Production Voice AI Agents with LiveKit**.
Students clone this, run `preflight.py` before class, then work through `sections/`
in order. Everything here is student-facing teaching material — optimize for
readability in class, not cleverness.

This file is the canonical agent guide for any coding agent. Prefer it over
scattered notes when editing this repo.

## Project overview

- Build path: Hello Voice → Production UX (turn detection) → Grounding with Moss → Ship It
- Public demo of the finished experience: [heartbyte.io](https://heartbyte.io)

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
uv sync                                                         # deps (repo root)
uv run python preflight.py                                      # must be all green
uv run python sections/<dir>/agent.py dev                       # run a section agent
uv run python sections/03-grounding-moss/build_index.py         # create Moss index
uv run python sections/03-grounding-moss/build_index.py --replace  # explicit rebuild
uv run python sections/03-grounding-moss/query_index.py "q" [--alpha X --top-k N]
cd sections/04-ship-it && lk agent create --secrets-file=../../.env  # first deploy
cd sections/04-ship-it && lk agent deploy                       # redeploys
```

Copy `.env.example` → `.env` for local credentials. Do not invent or commit secrets.

## Do not change without re-validation

These are deliberate teaching / production choices. Do not "fix" or modernize them:

- **livekit-agents is pinned to 1.3.x** (`>=1.3.0,<1.4.0`). Locked install is
  `1.3.12`. Do **not** bump to 1.5+/1.6 to match newer LiveKit docs.
- **Section 5 observability** uses `metrics_collected` + a readable
  `_print_metric` formatter + `metrics.UsageCollector` +
  `ctx.add_shutdown_callback`, plus `conversation_item_added` and
  `ChatMessage.metrics["e2e_latency"]` for the exact first-audio total.
  `metrics.log_metrics` is deliberately not used in classroom output because
  its structured fields render noisily. `session_usage_updated` is the newer
  API that is **not** in installed 1.3.12.
- Keep matching pins: `livekit-plugins-silero` and
  `livekit-plugins-turn-detector` on `>=1.3.0,<1.4.0`.
- **`transformers<5`**: transformers 5.x causes uv to silently downgrade the
  turn-detector plugin off the validated 1.3.x line.
- **`onnxruntime<1.26`**: 1.26 dropped macOS arm64 wheels; Silero VAD and the
  turn-detector need it transitively (M-series Macs).
- Keep the legacy `cli.run_app(WorkerOptions(entrypoint_fnc=...))` entrypoint
  (newer `AgentServer` exists in later SDK docs; not what this course teaches).
- `sections/04-ship-it/` is a self-contained deployable project (own
  `pyproject.toml`, `uv.lock`, `Dockerfile` on **Trixie**). Do not switch the
  Dockerfile to Bookworm — glibc 2.36 breaks the `inferedge-moss-core`
  manylinux_2_38 wheel.

## Moss safety

- `build_index.py` creates the configured index and refuses to overwrite it by
  default.
- Any valid Moss index name is accepted (lowercase letters, digits, hyphens);
  only the unedited `.env.example` placeholder is rejected. `firstbyte-<handle>`
  is a suggested convention, not a requirement.
- Deletion requires an explicit `--replace` flag. If the index name does not
  start with `firstbyte-`, `--replace` also requires interactive confirmation
  (retyping the index name) before deleting.
- `create_index` requires `model_id="moss-minilm"` — omitting it is a runtime error.

## Secrets

- `.env` is local only; never commit it or paste real keys into tracked files.
- Prefer exporting env vars per command over writing secrets into the tree.
- Local LiveKit CLI auth typically lives in `~/.livekit/cli-config.yaml`.

## Code style for this course

- Prefer clear, teachable diffs over clever refactors.
- Keep each section's `agent.py` runnable standalone.
- `03-grounding-moss`: Exercise 6 is the commented `on_user_turn_completed` in
  `agent.py` — leave it commented in the shipped tree; students uncomment live.
- `04-ship-it`: observability is active by default. Students run the complete
  grounded agent, inspect per-turn metrics and the shutdown usage summary,
  then deploy the same worker.
- Match existing patterns: short instructions, Inference model strings
  (`deepgram/...`, `openai/...`, `cartesia/...`), Silero VAD, optional
  `MultilingualModel` turn detection.

## Doc sync

Any change to exercises, APIs, or the deploy story must be reflected in:

1. the section README
2. the section `agent.py`

When docs and code disagree, code reality wins; then update the docs.

## Testing

- Voice testing: headphones + mic; open
  [Agents Playground](https://agents-playground.livekit.io) against a local
  `... agent.py dev` worker.
- For metrics / usage verification, use `sections/04-ship-it` — its handlers
  print readable `[metrics] STT/EOU/LLM/TTS` lines;
  `[usage] session summary` prints once on shutdown.
- Mic-less smoke test (optional): publish synthetic speech into a fresh room
  with `lk room join --publish`, with these rules:
  - Pad clips with trailing silence so VAD sees end-of-speech.
  - The publisher must be the **first** participant in the room (RoomIO links
    to the first mic).
  - 1.3.x dev logs do not log successful replies clearly; verify via
    transcription streams, audio, or `04-ship-it` metric lines.

## Out of scope

- Don't upgrade LiveKit to "latest" to match upstream quickstarts.
- Don't turn teaching stubs into production frameworks.
- Don't run `build_index.py` against production Moss indexes.
