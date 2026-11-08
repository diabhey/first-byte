"""
Section 2: Turn detection that doesn't cut people off.

Two upgrades over Section 1, one per side of the conversation: LiveKit's
local audio end-of-turn model replaces VAD-only silence timeouts, and barge-in
is switched on and tuned so backchannels do not cut the agent off. Same
pipeline otherwise. Preemptive generation starts inference before the final
turn boundary so the first audible reply can arrive sooner.

Run:
    lk agent dev sections/02-production-ux/agent.py
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
    inference,
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
    """Use message timing; overlapping pipeline stages must not be added."""
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
            total = item.metrics.get("e2e_latency")
            if total is None:
                return  # initial greeting has no preceding user turn
            llm_ttft = item.metrics.get("llm_node_ttft")
            tts_ttfb = item.metrics.get("tts_node_ttfb")
            llm_value = f"{llm_ttft * 1000:.0f}ms" if llm_ttft is not None else "n/a"
            tts_value = f"{tts_ttfb * 1000:.0f}ms" if tts_ttfb is not None else "n/a"
            status = "CANCELLED" if item.interrupted else "COMPLETE"
            print(f"[latency] server_e2e={total * 1000:.0f}ms "
                  f"response={status} preemptive=on | "
                  f"llm_ttft={llm_value} tts_ttfb={tts_value}")


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        # The headline of this section. Semantic end-of-turn detection that
        # uses speech meaning and acoustic cues to predict whether the user
        # is done, instead of just timing out on acoustic silence.
        # The current local audio model decides when the USER has finished.
        # Interruption handling separately decides when to stop the AGENT.
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(version="v1-mini"),
            interruption={
                "enabled": True,
                "mode": "vad",
                "discard_audio_if_uninterruptible": False,
                "min_duration": 0.7,
                "min_words": 2,
                "false_interruption_timeout": 2.0,
                "resume_false_interruption": True,
            },
            # Context changes in on_user_turn_completed invalidate speculative
            # output, so grounded turns regenerate with the retrieved context.
            preemptive_generation={"enabled": True},
        ),
    )
    print("[config] preemptive_generation=on")
    _attach_timing_logs(session)

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
