"""
Section 4 — Exercise 7 STARTING POINT.

Open this file during the live exercise. Your job: wire three pieces of
production observability so you can see every turn's latency and the
session's cumulative model usage.

  1. `conversation_item_added` event — read per-turn latency from
     `ChatMessage.metrics`.
  2. `session_usage_updated` event — log model usage as it accrues.
  3. `add_shutdown_callback` — log the cumulative `session.usage` tally
     on disconnect.

Everything else (Moss client, RAG hook, AgentSession) is already wired
from Section 3. You add the handlers inside `entrypoint()` below.

The finished reference is next door at `agent.py`. Try to write the
handlers yourself before peeking.

Run locally:
    uv run python sections/04-ship-it/agent_start.py dev
"""

import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from moss import MossClient, QueryOptions

# ── EXERCISE 7 imports ─────────────────────────────────────────────────────
# You'll need these two event types when you wire the handlers below.
# Uncomment as you use them.
#
# from livekit.agents import ConversationItemAddedEvent, SessionUsageUpdatedEvent
# ───────────────────────────────────────────────────────────────────────────

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

    # ── EXERCISE 7 ──────────────────────────────────────────────────────────
    # Add three things here:
    #
    #   (a) @session.on("conversation_item_added") — receives a
    #       ConversationItemAddedEvent. When `ev.item` is a ChatMessage with
    #       `role == "assistant"` and `metrics` is set, print
    #       `e2e_latency` from `ev.item.metrics`.
    #
    #   (b) @session.on("session_usage_updated") — receives a
    #       SessionUsageUpdatedEvent. Iterate `ev.usage.model_usage` and log
    #       each provider/model usage line.
    #
    #   (c) Define `async def _log_session_summary()` that iterates
    #       `session.usage.model_usage` and prints the final tally, then
    #       register it with `ctx.add_shutdown_callback(_log_session_summary)`.
    #
    # The finished block lives at `agent.py:127`.
    # ────────────────────────────────────────────────────────────────────────

    await session.start(agent=HeartByteAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
