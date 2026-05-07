"""
Section 2: Production voice UX.

Adds the two things that separate a voice demo from a voice product:

  1. Semantic turn detection (LiveKit's MultilingualModel) so the agent only
     speaks when the user is actually done, not after an arbitrary silence.
  2. Function tools the LLM can call mid-conversation, with proper error
     handling and interruption guards for state-mutating operations.

Run:
    uv run python sections/02-production-ux/agent.py dev
"""

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.llm import ToolError
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


# A small mock "order book" so the function tool has something to look up.
# Replace with a real DB call in production.
ORDERS = {
    "A100": {"status": "shipped", "carrier": "DHL", "eta_days": 2},
    "A101": {"status": "processing", "carrier": None, "eta_days": 4},
    "A102": {"status": "delivered", "carrier": "DHL", "eta_days": 0},
}


class SupportAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a customer support voice agent. Keep replies short, "
                "two or three sentences. When a user asks about an order, call "
                "the get_order_status tool with the order ID. Speak the result "
                "naturally; do not read field names aloud."
            ),
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Greet the user and ask what you can help with. Mention you "
                "can check order status if they have an order ID."
            ),
        )

    @function_tool()
    async def get_order_status(
        self,
        context: RunContext,
        order_id: str,
    ) -> dict:
        """Look up the current status of an order.

        Args:
            order_id: The order ID, e.g. A100.
        """
        order_id = order_id.upper().strip()
        if order_id not in ORDERS:
            # ToolError speaks a graceful failure rather than crashing.
            raise ToolError(
                f"I could not find order {order_id}. Could you repeat the ID?"
            )
        return ORDERS[order_id]

    @function_tool()
    async def place_order(
        self,
        context: RunContext,
        item: str,
        quantity: int,
    ) -> str:
        """Place a new order. Mutates state, do not interrupt mid-call.

        Args:
            item: The item to order.
            quantity: How many to order.
        """
        # State-mutating tool: block barge-in while the call is in flight so
        # the user does not double-submit.
        context.disallow_interruptions()
        # In production this is your API call. Mocked here.
        return f"Placed an order for {quantity} {item}. You will receive a confirmation shortly."


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(min_silence_duration=0.25),
        # The headline of this section. Semantic end-of-utterance detection
        # using STT context, not just acoustic silence.
        turn_detection=MultilingualModel(),
    )

    # Wire the false-interruption event so we can see backchannel detection
    # in real time.
    @session.on("agent_false_interruption")
    def _on_false_interruption(ev) -> None:
        print(f"[false interruption] backchannel detected, agent continues")

    await session.start(agent=SupportAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
