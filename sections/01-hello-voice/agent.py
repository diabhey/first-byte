"""
Section 1: Hello voice.

Your first voice agent on LiveKit Inference. No separate provider keys needed.
The Inference layer routes STT to Deepgram, the LLM to OpenAI, and TTS to
Cartesia, all billed via your LiveKit account.

Run:
    uv run python sections/01-hello-voice/agent.py dev

Then open https://agents-playground.livekit.io and connect.
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
    )

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
