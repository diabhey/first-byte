# Section 1: Hello voice

## Goal

Boot a voice agent in under 60 seconds and have your first conversation.

## Run

```bash
uv run python sections/01-hello-voice/agent.py dev
```

Open [agents-playground.livekit.io](https://agents-playground.livekit.io) in another tab. Connect to your local agent. Talk to it.

## What's happening under the hood

```
You speak  →  Silero VAD detects start of speech
           →  Deepgram nova-3 streams transcript          (via LiveKit Inference)
           →  OpenAI gpt-4o-mini generates reply          (via LiveKit Inference)
           →  Cartesia sonic-3 streams audio back         (via LiveKit Inference)
           →  You hear the reply
```

The `vad=silero.VAD.load()` line is the only thing not routed through Inference. VAD runs locally in your worker process for latency reasons.

## Things to try

- Ask a simple factual question, time the gap from your last word to first audio out. Aim for under 800 ms.
- Speak over the agent mid-reply. What happens? (Section 2 fixes the rough edges.)
- Stay silent for 30 seconds. What does the agent do?

## Concepts introduced

- `AgentSession` orchestrates the STT → LLM → TTS pipeline
- `Agent` defines instructions and reasoning behavior
- `JobContext` is the per-room handle the worker gives your entrypoint
- `WorkerOptions` registers your entrypoint with the LiveKit dispatch
- LiveKit Inference: zero-config provider access via shorthand strings like `"deepgram/nova-3:en"`
