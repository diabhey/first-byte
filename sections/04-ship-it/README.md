# Section 4: Ship it

## Goal

Wire production observability, then deploy the agent to LiveKit Cloud Agents with a single command. By the end of this section your agent runs on the public internet against LiveKit's global network and infrastructure.

## Step 1: Run with production metrics (Exercise 7)

The tested §3 grounded agent and its observability handlers are already active
in [`agent.py`](./agent.py). Stop any earlier section worker, then run:

```bash
uv run python sections/04-ship-it/agent.py dev
```

Connect through the [Agents Playground](https://agents-playground.livekit.io),
ask two or three HeartByte questions, and read the terminal:

- `[latency]` **prints one latency line per turn.** `perceived` measures from the user's last detected speech to the agent's first server-side audio using LiveKit's `ChatMessage.metrics["e2e_latency"]`. The 800 ms `PASS` / `OVER`
target applies only to TTS time-to-first-byte (`tts_ttfb`), not to perceived
end-to-end latency. The line also shows EOU, STT finalization,
retrieval-hook time, and LLM TTFT.
- **Readable per-turn metrics** print from the `metrics_collected` event: STT,
end-of-utterance delay, LLM TTFT (`ttft`), and TTS TTFB (`ttfb`).
LiveKit's `metrics.log_metrics()` emits structured fields (often rendered as
JSON), which is useful for production ingestion; `_print_metric()` renders
the same key values as concise classroom lines.
- `[usage] session summary: ...` logs once on shutdown via
`add_shutdown_callback`, from a `metrics.UsageCollector` that accumulated
each event. It reports aggregate LLM token totals, STT/TTS audio durations,
and TTS character usage for the session.

```python
usage_collector = metrics.UsageCollector()

@session.on("metrics_collected")
def _on_metrics(ev: MetricsCollectedEvent) -> None:
    _print_metric(ev.metrics)
    usage_collector.collect(ev.metrics)

async def _log_session_summary() -> None:
    summary = usage_collector.get_summary()
    print(
        "[usage] session summary: "
        f"llm_prompt={summary.llm_prompt_tokens} "
        f"llm_completion={summary.llm_completion_tokens} "
        f"stt_audio={summary.stt_audio_duration:.2f}s "
        f"tts_audio={summary.tts_audio_duration:.2f}s "
        f"tts_chars={summary.tts_characters_count}"
    )

ctx.add_shutdown_callback(_log_session_summary)
```

Example:

```text
[metrics] STT  audio=2.41s streamed=true
[metrics] EOU  delay=0.62s transcription=0.21s
[metrics] LLM  ttft=0.44s prompt=580 completion=42 tokens/s=51.3
[metrics] TTS  ttfb=0.27s audio=4.31s chars=126
[latency] perceived=1390ms response=COMPLETE preemptive=on | eou=620ms stt_final=210ms retrieval=10ms llm_ttft=440ms tts_ttfb=270ms tts_target=800ms PASS
[usage] session summary: llm_prompt=580 llm_completion=42 stt_audio=2.41s tts_audio=4.31s tts_chars=126
```

The component values are diagnostics, not numbers to add together.
`stt_final` overlaps the EOU window, and streamed LLM/TTS work can overlap or
buffer. `perceived` is the SDK's separately measured speech-end → first-audio
value. It excludes the final network hop and browser playback. The course's
“under 800 ms” claim refers specifically to `tts_ttfb`.

The `[latency]` line appears when the assistant message is finalized (usually
after the spoken reply), even though `perceived` records when first audio began.

If the user interrupts after first audio, the end-to-end line is labelled
`CANCELLED`; interrupted LLM/TTS stage lines use `cancelled=true`. A response
cancelled before any audio has no first-audio total to report.

This agent carries forward Section 2's semantic turn detection, preemptive
generation, and tuned interruption settings (`min_interruption_words=2` and
friends), so `CANCELLED` means a real two-word interruption rather than a
cough. These values ship with the worker, so treat them as production
configuration and re-tune them against real visitor audio. A noisy phone caller
and a headset user do not want the same thresholds.

Because every production turn is grounded, LiveKit Agents 1.3.12 invalidates
speculative output whenever the Moss hook adds context, then regenerates the
answer from that context. This preserves grounding correctness, although the
discarded speculative request can consume inference.

Disconnect from the Playground or stop the worker to trigger the shutdown
callback and print `[usage] session summary: ...`.

Walk through the code after observing the output: the event handler explains
the per-turn logs; `UsageCollector` and the shutdown callback explain the final
session rollup. No uncomment/restart cycle is needed in this section.

> Note: pinned livekit-agents 1.3.12 provides `metrics_collected`,
> `ChatMessage.metrics`, `conversation_item_added`, and
> `metrics.UsageCollector`; this section uses all four. The newer
> `session_usage_updated` event is not present in 1.3.12. If you upgrade the
> SDK later, re-validate the observability flow end to end.

## Step 2: Prepare and deploy

Stop the local worker first. Confirm you are authenticated to the LiveKit Cloud
project used by this course:

```bash
lk cloud auth
```

```bash
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
```

This builds the worker and securely injects the `MOSS_*` values from `.env`.
LiveKit ignores the project credentials it provides automatically.

After deploy:

1. Run `lk agent secrets` to verify the secret names. Values cannot be read
   back from the CLI or dashboard.
2. Open [cloud.livekit.io](https://cloud.livekit.io), find the agent, and
   confirm it becomes healthy.
3. Note the agent ID. `lk agent create` writes it to a new `livekit.toml` in
   this directory. That file is gitignored; copy `livekit.toml.example` as a
   reference for the shape.

For redeploys, `lk agent deploy` reads `livekit.toml` and rolls a new container
without changing the stored Cloud secrets.

That's it. No Kubernetes manifest, no SSL cert wrangling.

### What's pre-staged

This directory ships as a self-contained deployable Python project so `lk agent create` works without surprises:

- `agent.py` — the single grounded worker with observability enabled.
- `pyproject.toml` + `uv.lock` — pinned deps. Section-local, intentionally separate from the repo-root `pyproject.toml` (which is for the course's dev environment).
- `Dockerfile` — uses `python:3.13-slim-trixie` (glibc 2.38) with `uv` from astral's image. The default `lk agent create` Dockerfile uses Bookworm (glibc 2.36), which silently fails to install `inferedge-moss-core` because the wheel is `manylinux_2_38_x86_64`. Pre-staging Trixie avoids that 5-minute live debug.
- `.dockerignore` — keeps `.env`, `.git`, editor files, and coding-agent dotfiles out of the build context.
- `livekit.toml.example` — template for the auto-generated `livekit.toml`.

## Step 3: Talk to your deployed agent from a local orb page

The Agents Playground is fine for poking the worker, but the course ships a small visitor-facing front end you can run locally to feel what production looks like. It's at the repo root in [`orb/`](../../orb/).

```bash
cd ../../orb
cp config.template.js config.js
```

Edit `config.js` and fill in two values:

- `URL`: your LiveKit Cloud `wss://...livekit.cloud` (same one in your `.env`)
- `TOKEN`: a one-hour LiveKit access token for room `heartbyte-orb`:

  ```bash
  lk token create --join --room heartbyte-orb --identity orb-visitor --valid-for 1h
  ```

Then serve the page:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [http://localhost:8000](http://localhost:8000) → tap the orb → grant the mic → ask "What is HeartByte?" Your browser connects over WebRTC to your LiveKit Cloud project; LiveKit dispatches your deployed worker to the room; the agent does STT → Moss retrieval → LLM → TTS and the reply streams back. The orb's color and state indicator track listening → thinking → speaking. Tap the orb during a live session to disconnect.

That's the full architecture: static webpage, LiveKit Cloud, and your deployed
agent meet in the room encoded in the token.

When you ship this for real visitors, you replace the hard-coded token in `config.js` with a server-side token endpoint that mints per-visitor tokens — see Going further below.

## Going further

- **Public frontend**: mint short-lived tokens server-side; never ship API
  secrets or a long-lived token to the browser.
- **Isolation**: use a unique room per visitor and rate-limit the token endpoint.
- **Telephony**: `lk sip` to wire a phone number. Buy a DID via LiveKit Phone Numbers in the Cloud dashboard, set up a dispatch rule, your agent picks up real calls. See [docs.livekit.io/sip](https://docs.livekit.io/sip/).
- **Vision**: Gemini Live and OpenAI's realtime models support video input. Pass a video track and ask the agent what it sees.
- **Avatars**: Tavus and Anam render a photorealistic talking head. Plug in via the avatar plugins.
- **Self-host**: if compliance requires it, run LiveKit Server yourself with the [self-hosting guide](https://docs.livekit.io/home/self-hosting/).

## Concepts introduced

- `metrics_collected` event + readable per-turn latency formatting
- speech-end → first-audio observation plus an 800 ms TTS TTFB target
- `metrics.UsageCollector` for cumulative model-usage rollup
- `ctx.add_shutdown_callback` for end-of-session reporting
- `lk agent create` for one-command deploy to LiveKit Cloud Agents
- The pattern: observability before deploy, not after
