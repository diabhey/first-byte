# Section 1: Hello voice

## Goal

Boot a voice agent in under 60 seconds and have your first conversation.

## Run

```bash
uv run python sections/01-hello-voice/agent.py dev
```

Open [agents-playground.livekit.io](https://agents-playground.livekit.io) in another tab. Connect to your local agent. Talk to it. Keep the terminal visible — after each turn it prints `[timing]` lines (end-of-utterance delay, LLM TTFT, TTS first audio byte).

## What's happening under the hood

```bash
You speak  →  Silero VAD detects start of speech
           →  Deepgram nova-3 streams transcript          (via LiveKit Inference)
           →  OpenAI gpt-4o-mini generates reply          (via LiveKit Inference)
           →  Cartesia sonic-3 streams audio back         (via LiveKit Inference)
           →  You hear the reply
```

The `vad=silero.VAD.load()` line is the only thing not routed through Inference. VAD runs locally in your worker process for latency reasons.

## A/B turn-taking script (run this first)

Run **only this agent**. Use headphones. In the Playground, connect, then work the script top to bottom. For each line: speak exactly as written, hold the pause silently (count in your head), then either finish the sentence or wait to see if the agent jumps in. Note whether the agent **replied during the pause** (too early) or **waited**.

| # | Say this | Pause | Then | What to watch (Section 1) |
|---|----------|-------|------|---------------------------|
| 1 | `What's two plus two?` | — | wait for reply | Control. Observe last word → first audio; this includes more than TTS TTFB, so do not compare it with the course's 800 ms TTS target. |
| 2 | `Hmm, the thing I want to ask is` | **2 seconds** (do not continue) | wait | Often jumps in mid-thought — silence looked like end of turn. |
| 3 | `So my real question is` | **2 seconds** | `how does voice activity detection work?` | May cut in during the pause before you finish. |
| 4 | `What's the weather` | **2 seconds** | `in Lisbon?` | May answer after "weather" before "Lisbon". |
| 5 | `I was wondering` | **2 seconds** | `whether you can hear me clearly.` | Same: premature reply during the gap. |
| 6 | Speak over the agent mid-reply on any answer | — | — | Agent should stop and listen (barge-in). That's expected. |
| 7 | Stay silent after a full reply | 30 seconds | — | Agent should not keep talking unprompted. |

Write down for #2–#5: **jumped in** / **waited**, plus the terminal's `[timing] end-of-utterance delay` value when a reply does fire. That number is how long after you stopped speaking before the turn was committed — on premature replies it often lands near your pause length.

Then stop this worker (`Ctrl+C`), run Section 2 with the **same script and same pause lengths**, and compare both the feel and those EOU delay lines.

Section 2 adds semantic turn detection so #2–#5 should wait more often. The gap can be subtle with short pauses — use the full **2 second** holds.

## Concepts introduced

- `AgentSession` orchestrates the STT → LLM → TTS pipeline
- `Agent` defines instructions and reasoning behavior
- `JobContext` is the per-room handle the worker gives your entrypoint
- `WorkerOptions` registers your entrypoint with the LiveKit dispatch
- LiveKit Inference: zero-config provider access via shorthand strings like `"deepgram/nova-3:en"`
