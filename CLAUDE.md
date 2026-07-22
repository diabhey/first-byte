# first-byte — course repo notes for Claude

Course repo for the O'Reilly live course **Production Voice AI Agents with LiveKit**.
Students clone this, run `preflight.py` before class, then work through
`sections/` in order. Everything here is student-facing teaching material —
optimize for readability in class, not cleverness.

## Numbering: course sections vs directories

The proposal has 5 course sections; Section 1 is presentation-only. Directories
are off by one:

| Directory                   | Course section |
|-----------------------------|----------------|
| `sections/01-hello-voice`   | Section 2      |
| `sections/02-production-ux` | Section 3      |
| `sections/03-grounding-moss`| Section 4      |
| `sections/04-ship-it`       | Section 5      |

When editing docs, always say which numbering you're using.

## Commands

```bash
uv sync                                              # deps (repo root)
uv run python preflight.py                           # must be all green
uv run python sections/<dir>/agent.py dev            # run a section agent
uv run python sections/03-grounding-moss/build_index.py   # (re)build Moss index
uv run python sections/03-grounding-moss/query_index.py "question" [--alpha X --top-k N]
cd sections/04-ship-it && lk agent create            # first deploy
cd sections/04-ship-it && lk agent deploy            # redeploys
```

## Pins and API choices (do not "fix" these)

- **livekit-agents is pinned to 1.3.x** (`>=1.3.0,<1.4.0`). The observability
  pattern taught in Section 5 — `metrics_collected` event + `metrics.log_metrics`
  + `metrics.UsageCollector` + `ctx.add_shutdown_callback` — is the validated
  1.3.x API, deployed in production. Newer docs mention `session_usage_updated`
  / `ChatMessage.metrics`; those are NOT in the installed SDK. Don't migrate
  without re-validating end to end.
- **onnxruntime<1.26**: 1.26 dropped macOS arm64 wheels; Silero VAD and the
  turn-detector plugin need it transitively. Affects students on M-series Macs.
- The legacy `cli.run_app(WorkerOptions(entrypoint_fnc=...))` entrypoint is a
  deliberate teaching choice on 1.3.x (newer `AgentServer` pattern exists in
  later SDK docs).
- `sections/04-ship-it/` is a deliberately self-contained project (own
  `pyproject.toml`, `uv.lock`, `Dockerfile` on **Trixie** — Bookworm's glibc
  2.36 breaks the `inferedge-moss-core` manylinux_2_38 wheel).

## Moss safety

`build_index.py` **deletes and recreates** the index named by `MOSS_INDEX_NAME`.
Never point it at the production index `heartbyte-io`. Course/test runs use a
scratch name (e.g. `firstbyte-<handle>`). `create_index` requires
`model_id="moss-minilm"` — omitting it is a runtime error, not a typo.

## Secrets

`.env` is a placeholder template; never commit or edit it without asking. For
local test runs, credentials live in `~/.livekit/cli-config.yaml` (LiveKit,
per-project) and `~/code/heartbyte/hb-agent/.env` (Moss). Prefer exporting env
vars per command over writing `.env`.

## Doc sync (two copies of the proposal)

1. `Abhimanyu Selvan - ... Live Course Proposal .md` (repo root) — export of the
   O'Reilly Google Doc; newest wording/timings.
2. The Google Doc itself — only Abhi can edit; flag needed changes to him.

(The old `proposal/` working copy + citation audit were retired in July 2026
after the audit closed. `prep/` — gitignored, instructor-only; this repo is
public and student-facing — absorbed the verified facts and sources into
`master-guide.md`.)

Any change to exercises, APIs, or the deploy story must be reflected in: the
section README, the section `agent.py`/`agent_start.py`, and the proposal
export (then flag the Google Doc change to Abhi). README.md yields to the
proposal when they disagree; code reality wins over both (then update the docs).

## Related repos

`~/code/heartbyte/hb-agent` is the production proving ground (live at
heartbyte.io). Non-HeartByte-specific fixes (dep pins, API drift, deprecations)
flow both ways between it and this repo.

## Testing without a microphone

Agents in `dev`/`start` mode auto-dispatch to new rooms in the LiveKit project.
Smoke-test loop: run the agent, create a room (`lk room create` or join it),
publish synthetic speech (`say -o q.wav ... && ffmpeg ... q.ogg`, then
`lk room join --publish q.ogg <room>`), watch the agent log for transcripts and
reply speech. Caveat on Abhi's machine: personal LiveKit projects already have
deployed cloud agents that contend for auto-dispatch with local dev workers —
students' fresh projects won't have this.
