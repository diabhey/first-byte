"""
Section 4: Ship it.

The Section 3 agent, plus production observability and ready for `lk agent
create`. Two upgrades:

  1. conversation_item_added subscription reads per-turn latency from
     ChatMessage.metrics on every committed turn (STT first byte, LLM
     time-to-first-token, TTS first audio chunk, end-to-end).
  2. session_usage_updated accumulates model usage across the call; we log
     the cumulative tally on shutdown via add_shutdown_callback.

Note: the session-level `metrics_collected` event used in earlier versions of
livekit-agents is deprecated. We use `conversation_item_added` for per-turn
latency and `session_usage_updated` for usage rollup instead.

Run locally:
    uv run python sections/04-ship-it/agent.py dev

Deploy to LiveKit Cloud Agents:
    cd sections/04-ship-it
    lk agent create
"""

import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    ChatMessage,
    ConversationItemAddedEvent,
    JobContext,
    SessionUsageUpdatedEvent,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from moss import MossClient, QueryOptions

load_dotenv()


class HeartByteAgent(Agent):
    def __init__(self, moss_client: MossClient, index_name: str) -> None:
        super().__init__(
            instructions=(
                "You are the voice mind of HeartByte, the working studio of "
                "Abhimanyu Selvan (Abhi). Answer questions using only the "
                "context provided in system messages. If the context does not "
                "contain the answer, say so plainly. Keep replies short, two or "
                "three sentences. Speak conversationally; do not read URLs, "
                "emails, or punctuation aloud."
            ),
        )
        self._moss = moss_client
        self._index_name = index_name

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Greet the visitor briefly as the HeartByte orb. One sentence. "
                "Invite them to ask about HeartByte, Abhi's work, or how to "
                "get in touch."
            ),
        )

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        query = new_message.text_content
        if not query or not query.strip():
            return await super().on_user_turn_completed(turn_ctx, new_message)

        try:
            results = await self._moss.query(
                self._index_name,
                query,
                QueryOptions(top_k=5, alpha=0.8),
            )
        except Exception as exc:
            print(f"[moss] query failed: {exc}")
            return await super().on_user_turn_completed(turn_ctx, new_message)

        if results.docs:
            context_str = "\n".join(f"- {d.text}" for d in results.docs)
            turn_ctx.add_message(
                role="system",
                content=(
                    f"Relevant context for the user's question:\n{context_str}\n\n"
                    "Use this to answer. If the answer is not present, say so."
                ),
            )

        return await super().on_user_turn_completed(turn_ctx, new_message)


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    project_id = os.environ["MOSS_PROJECT_ID"]
    project_key = os.environ["MOSS_PROJECT_KEY"]
    index_name = os.environ.get("MOSS_INDEX_NAME", "firstbyte")

    moss = MossClient(project_id=project_id, project_key=project_key)
    try:
        await moss.load_index(index_name)
        print(f"[moss] index '{index_name}' loaded")
    except Exception:
        print(f"[moss] could not pre-load '{index_name}'; will use cloud lookup")

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(min_silence_duration=0.25),
        turn_detection=MultilingualModel(),
    )

    # Production observability. Two pieces:
    #   1. conversation_item_added fires when a turn commits. ChatMessage.metrics
    #      carries per-turn latency: STT first byte, LLM time-to-first-token,
    #      TTS first audio chunk, end-to-end.
    #   2. session_usage_updated tracks cumulative model usage (tokens, audio
    #      durations). We log the final tally on shutdown via add_shutdown_callback.

    @session.on("conversation_item_added")
    def _on_item(ev: ConversationItemAddedEvent) -> None:
        if not isinstance(ev.item, ChatMessage):
            return
        m = ev.item.metrics
        if not m:
            return
        e2e = m.get("e2e_latency")
        if ev.item.role == "assistant" and e2e is not None:
            print(f"[metrics] turn e2e_latency={e2e:.3f}s metrics={m}")

    @session.on("session_usage_updated")
    def _on_usage(ev: SessionUsageUpdatedEvent) -> None:
        for usage in ev.usage.model_usage:
            print(f"[usage] {usage.provider}/{usage.model}: {usage}")

    async def _log_session_summary() -> None:
        for usage in session.usage.model_usage:
            print(f"[usage] session final: {usage.provider}/{usage.model}: {usage}")

    ctx.add_shutdown_callback(_log_session_summary)

    await session.start(agent=HeartByteAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
