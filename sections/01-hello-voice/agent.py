"""
Course Section 2 / Directory 01: Hello voice.

Your first voice agent on LiveKit Inference. No separate provider keys needed.
By default, the Inference layer routes STT to Deepgram, the LLM to Google, and
TTS to Cartesia, all billed via your LiveKit account.

Run locally without a browser or deployed agent:
    lk agent console sections/01-hello-voice/agent.py

Add `--text` after `console` for the lowest-memory check. Text mode skips STT
and TTS; use voice mode afterward to verify the complete pipeline. Watch the
terminal for [timing] lines after each turn.
"""

import os

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
DEFAULT_LLM_MODEL = "google/gemma-4-31b-it"
# Speech end to first server audio. Playback on the laptop is not included.
PIPELINE_BUDGET_MS = 1370


def _llm_model() -> str:
    """Return the configured Inference model, with a stable course default."""
    return os.environ.get("LLM_MODEL", "").strip() or DEFAULT_LLM_MODEL


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
            if total is None:
                print("[timing] greeting has no user turn, so there is no pipeline total yet")
                return
            total_ms = round(total * 1000)
            if total_ms < PIPELINE_BUDGET_MS:
                verdict = "under"
            elif total_ms == PIPELINE_BUDGET_MS:
                verdict = "at"
            else:
                verdict = "over"
            print(
                f"[timing] TOTAL pipeline: {total_ms}ms — {verdict} {PIPELINE_BUDGET_MS}ms "
                "(speech end → first server audio; excludes playback)"
            )


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm=_llm_model(),
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
