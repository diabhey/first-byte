"""
Section 1: Hello voice.

Your first voice agent on LiveKit Inference. No separate provider keys needed.
The Inference layer routes STT to Deepgram, the LLM to OpenAI, and TTS to
Cartesia, all billed via your LiveKit account.

Run:
    lk agent dev sections/01-hello-voice/agent.py

Then open your LiveKit Cloud project's Agent Console, select the dev deployment
printed by the CLI, and connect.
Watch the terminal for [timing] lines after each turn.
"""

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    ChatMessage,
    ConversationItemAddedEvent,
    JobContext,
    TurnHandlingOptions,
    cli,
)
from livekit.plugins import silero

load_dotenv()
server = AgentServer()


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
    """Read component timing and server-side first-audio latency per turn."""
    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if not isinstance(item, ChatMessage):
            return
        if item.role == "user":
            for key, label in (
                ("end_of_turn_delay", "end-of-turn delay"),
                ("transcription_delay", "transcription delay"),
            ):
                value = item.metrics.get(key)
                if value is not None:
                    print(f"[timing] {label}: {value:.2f}s")
        elif item.role == "assistant":
            for key, label in (
                ("llm_node_ttft", "LLM TTFT (first token)"),
                ("tts_node_ttfb", "TTS TTFB (first byte)"),
            ):
                value = item.metrics.get(key)
                if value is not None:
                    print(f"[timing] {label}: {value:.2f}s")
            total = item.metrics.get("e2e_latency")
            if total is not None:
                print(f"[timing] TOTAL end-to-end: {total * 1000:.0f}ms "
                      "(speech end → first server audio; excludes network/playback)")


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        # Deliberately broken baseline: VAD-only, no barge-in, and no
        # speculative generation. Compare it with the next section.
        turn_handling=TurnHandlingOptions(
            turn_detection="vad",
            interruption={"enabled": False, "discard_audio_if_uninterruptible": True},
            preemptive_generation={"enabled": False},
        ),
    )
    _attach_timing_logs(session)

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
