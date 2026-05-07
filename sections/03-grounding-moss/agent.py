"""
Section 3: Grounding with Moss.

Adds retrieval-augmented generation done at the right layer. We override
on_user_turn_completed so Moss runs on EVERY user turn, before the LLM, and
inject the top results into the chat context as a system message.

This is different from putting retrieval behind a function tool the LLM has
to choose to call. For voice latency, you cannot afford the round-trip of
"LLM decides to retrieve, retrieve, LLM decides to answer." Always retrieve,
let the LLM decide what to use.

Run (after build_index.py has populated your Moss index):
    uv run python sections/03-grounding-moss/agent.py dev
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
        """Run Moss on every user turn, inject results before the LLM call."""
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
            print(f"[moss] injected {len(results.docs)} results")
        else:
            print("[moss] no results for query")

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

    await session.start(agent=CompassAgent(moss, index_name), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
