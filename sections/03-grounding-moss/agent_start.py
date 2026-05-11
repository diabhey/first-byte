"""
Section 3 — Exercise 6 STARTING POINT.

Open this file during the live exercise. Your job: override
`on_user_turn_completed` so Moss runs on every user turn and the retrieved
docs land in `turn_ctx` as a system message before the LLM is called.

Everything else (Moss client setup, index pre-load, turn detection, the
agent's instructions) is already wired. You write the hook.

The finished reference is next door at `agent.py`. Try to write the hook
yourself before peeking.

Run:
    uv run python sections/03-grounding-moss/agent_start.py dev
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

    # ── EXERCISE 6 ─────────────────────────────────────────────────────────
    # Override `on_user_turn_completed` below.
    #
    #   1. Read the user's transcript from `new_message.text_content`.
    #   2. Skip if empty.
    #   3. Call `self._moss.query(self._index_name, query,
    #      QueryOptions(top_k=5, alpha=0.8))`.
    #   4. If `results.docs` is non-empty, build a context string from each
    #      `d.text` and call `turn_ctx.add_message(role="system", content=...)`
    #      so the LLM sees it before its reply.
    #   5. Always end with `return await super().on_user_turn_completed(...)`
    #      so the framework continues with the LLM call.
    #
    # The finished body lives at `agent.py:56`.
    # ───────────────────────────────────────────────────────────────────────

    # async def on_user_turn_completed(
    #     self,
    #     turn_ctx: ChatContext,
    #     new_message: ChatMessage,
    # ) -> None:
    #     # TODO: implement
    #     return await super().on_user_turn_completed(turn_ctx, new_message)


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

    await session.start(agent=HeartByteAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
