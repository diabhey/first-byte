"""
Section 2: Turn detection that doesn't cut people off.

One upgrade over Section 1: swap LiveKit's open-weights end-of-turn model in
for VAD-only silence timeouts. Same pipeline otherwise. Compare [timing]
end-of-utterance delay lines against Section 1 on the A/B script.

Run:
    uv run python sections/02-production-ux/agent.py dev
"""

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    MetricsCollectedEvent,
    WorkerOptions,
    cli,
)
from livekit.agents.metrics import EOUMetrics, LLMMetrics, TTSMetrics
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class HelloAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly voice assistant. Keep replies short, two or "
                "three sentences. Speak conversationally; do not read URLs or "
                "punctuation aloud."
            ),
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Greet the user briefly and ask how you can help.",
        )


def _attach_timing_logs(session: AgentSession) -> None:
    """Print turn latency so you can A/B Section 1 vs Section 2 in the terminal."""
    # Stages of the current turn, held until first audio so we can total them.
    # Only these three are additive: end-of-utterance delay and transcription
    # delay are both measured from the moment you stop speaking, so the
    # transcription wait already sits inside the end-of-utterance delay.
    turn: dict[str, float] = {}

    def _print_total() -> None:
        if not {"eou", "llm", "tts"} <= turn.keys():
            return
        total_ms = (turn["eou"] + turn["llm"] + turn["tts"]) * 1000
        print(
            f"[timing] TOTAL end-to-end:       {total_ms:.0f}ms "
            f"(speech end → first audio byte)"
        )
        turn.clear()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        m = ev.metrics
        if isinstance(m, EOUMetrics):
            # With MultilingualModel, unfinished transcripts should keep this
            # from firing too early during a mid-thought pause.
            turn.clear()
            turn["eou"] = m.end_of_utterance_delay
            print(
                f"[timing] end-of-utterance delay: {m.end_of_utterance_delay:.2f}s "
                f"(silence → turn committed)"
            )
            print(
                f"[timing] transcription delay:    {m.transcription_delay:.2f}s "
                f"(speech end → final transcript)"
            )
        elif isinstance(m, LLMMetrics) and not m.cancelled:
            turn["llm"] = m.ttft
            print(f"[timing] LLM TTFT (first token): {m.ttft:.2f}s")
            _print_total()
        elif isinstance(m, TTSMetrics) and not m.cancelled:
            # A reply can arrive as several TTS segments; only the first one
            # contributes to first-audio latency.
            turn.setdefault("tts", m.ttfb)
            print(f"[timing] TTS TTFB (first byte):  {m.ttfb:.2f}s")
            _print_total()


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        # The headline of this section. Semantic end-of-turn detection that
        # uses the STT transcript to predict whether the user is actually
        # done, instead of just timing out on acoustic silence.
        turn_detection=MultilingualModel(),
    )
    _attach_timing_logs(session)

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
