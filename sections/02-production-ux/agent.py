"""
Section 2: Turn detection that doesn't cut people off.

One upgrade over Section 1: swap LiveKit's open-weights end-of-turn model in
for VAD-only silence timeouts. Same pipeline otherwise. The difference is
audible on the first phrase with a natural pause.

Run:
    uv run python sections/02-production-ux/agent.py dev
"""

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
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

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
