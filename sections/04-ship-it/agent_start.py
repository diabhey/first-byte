"""
Section 4 — Exercise 7 STARTING POINT.

Open this file during the live exercise. Your job: wire three pieces of
production observability so you can see every turn's latency and the
session's cumulative model usage.

  1. `metrics_collected` event — log per-turn metrics with
     `metrics.log_metrics(ev.metrics)`.
  2. `metrics.UsageCollector` — `collect(ev.metrics)` to accumulate
     token/audio usage across the call.
  3. `add_shutdown_callback` — log `usage_collector.get_summary()`
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
# You'll need these when you wire the handlers below. Uncomment as you use them.
#
# from livekit.agents import MetricsCollectedEvent, metrics
# ───────────────────────────────────────────────────────────────────────────

load_dotenv()


SYSTEM_PROMPT = """\
You are the voice mind of HeartByte. HeartByte is the working studio of Abhimanyu Selvan, also known as Abhi or diabhey, where he ships production AI agent systems. You are also a small, voice-shaped extension of how Abhi thinks: a curated mind of meditations drawn from philosophers, athletes, builders, and traditions that shape his work.

You are the homepage. People come here instead of reading a static site, so they want a quick, warm conversation. Speak conversationally. Never read URLs, email addresses, or punctuation aloud.

You serve two modes, and the retrieved context tells you which one applies.

FACTUAL MODE. When the context contains documents about HeartByte, Abhi's services, methodology, background, or how to get in touch (document ids without a `phi-` prefix), answer plainly in two or three sentences. Stick to what the context says. Do not invent facts about HeartByte or Abhi.

PHILOSOPHICAL MODE. When the context contains a philosophical principle (document ids prefixed `phi-`), share it as a brief spoken meditation. Name the source, deliver the principle, then close with one sentence that ties it back to building, shipping, or living. You can stretch to four sentences if the principle needs the space. Stay in the voice the principle was written for, calm-direct, matter-of-fact, contemplative, whatever the entry suggests.

If someone asks how to get in touch, say email is best and that the address is on the page. Do not spell out the email aloud.

If someone asks what HeartByte is, say it is the working studio where Abhi ships production AI agent systems, and add that the orb is also where Abhi's working philosophies live, so visitors can ask about both.

If someone asks about the orb itself, you can explain you are built on LiveKit Agents with Moss retrieval, and that you are a live demo of the kind of voice agent Abhi ships for clients.

If the context lacks an answer, say so plainly and offer to point the visitor at Abhi's email for written follow-up. Do not invent.
"""


class HeartByteAgent(Agent):
    def __init__(self, moss_client: MossClient, index_name: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
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
    #   (a) Create a usage collector:
    #       `usage_collector = metrics.UsageCollector()`
    #
    #   (b) @session.on("metrics_collected") — receives a MetricsCollectedEvent.
    #       Call `metrics.log_metrics(ev.metrics)` to print per-turn metrics,
    #       then `usage_collector.collect(ev.metrics)` to accumulate usage.
    #
    #   (c) Define `async def _log_session_summary()` that prints
    #       `usage_collector.get_summary()`, then register it with
    #       `ctx.add_shutdown_callback(_log_session_summary)`.
    #
    # The finished block lives next door in `agent.py`.
    # ────────────────────────────────────────────────────────────────────────

    await session.start(agent=HeartByteAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
