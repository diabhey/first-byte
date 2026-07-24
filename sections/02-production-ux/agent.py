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

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        m = ev.metrics
        if isinstance(m, EOUMetrics):
            # With MultilingualModel, unfinished transcripts should keep this
            # from firing too early during a mid-thought pause.
            print(
                f"[timing] end-of-utterance delay: {m.end_of_utterance_delay:.2f}s "
                f"(silence → turn committed)"
            )
            print(
                f"[timing] transcription delay:    {m.transcription_delay:.2f}s "
                f"(speech end → final transcript)"
            )
        elif isinstance(m, LLMMetrics) and not m.cancelled:
            print(f"[timing] LLM time-to-first-token: {m.ttft:.2f}s")
        elif isinstance(m, TTSMetrics) and not m.cancelled:
            print(f"[timing] TTS first audio byte:    {m.ttfb:.2f}s")


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
