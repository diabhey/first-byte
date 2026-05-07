"""
Section 4: Ship it.

The Section 3 agent, plus production observability and ready for `lk agent
create`. Two upgrades:

  1. metrics_collected event handler logs per-turn STT, LLM, and TTS latency.
  2. UsageCollector accumulates token and audio usage; we log the summary on
     shutdown via add_shutdown_callback.

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
    JobContext,
    MetricsCollectedEvent,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from moss import MossClient, QueryOptions

load_dotenv()


class CompassAgent(Agent):
    def __init__(self, moss_client: MossClient, index_name: str) -> None:
        super().__init__(
            instructions=(
                "You are the voice assistant for Compass Coffee, a single-origin "
                "coffee subscription service. Answer questions using only the "
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
            instructions="Greet the caller as Compass Coffee and ask how you can help.",
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
    #   1. metrics_collected fires on every measurable event in the pipeline:
    #      STT first byte, LLM time-to-first-token, TTS first audio chunk.
    #   2. UsageCollector accumulates token and audio usage across the session.
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def _log_session_summary() -> None:
        summary = usage_collector.get_summary()
        print(f"[usage] session summary: {summary}")

    ctx.add_shutdown_callback(_log_session_summary)

    await session.start(agent=CompassAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
