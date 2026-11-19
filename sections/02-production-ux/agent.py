"""
Section 2: Turn detection that doesn't cut people off.

Two upgrades over Section 1, one per side of the conversation: LiveKit's
local audio end-of-turn model replaces VAD-only silence timeouts, and barge-in
is switched on and tuned so backchannels do not cut the agent off. Same
pipeline otherwise. Preemptive generation starts inference before the final
turn boundary so the first audible reply can arrive sooner.

Run:
    lk agent console sections/02-production-ux/agent.py
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


_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_BLUE = "\033[34m"
_GREEN = "\033[32m"
_PURPLE = "\033[35m"
_ORANGE = "\033[38;5;208m"
_GAP = "\033[90m"
_BOX_WIDTH = 62


def _paint(color: str, text: str) -> str:
    if os.environ.get("NO_COLOR"):
        return text
    return f"{color}{text}{_RESET}"


def _ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 1000:.0f} ms"


def _rule() -> str:
    dots = ("· " * _BOX_WIDTH)[:_BOX_WIDTH]
    return f"│ {_paint(_DIM, dots.ljust(_BOX_WIDTH))} │"


def _line(text: str) -> str:
    shown = text if len(text) <= _BOX_WIDTH else text[: _BOX_WIDTH - 1] + "…"
    return f"│ {shown.ljust(_BOX_WIDTH)} │"


_NEST_INDENT = 6


def _metric_line(label: str, value: str, color: str, indent: int = 0) -> str:
    shown = (" " * indent) + label
    padded = value.rjust(8)
    # Nested rows sit on the right edge. Stage rows sit just inward of them.
    right_pad = max(_NEST_INDENT - indent, 0)
    gap = _BOX_WIDTH - len(shown) - len(padded) - right_pad
    body = (
        f"{_paint(color, shown)}{' ' * max(gap, 2)}"
        f"{_paint(_BOLD + color, padded)}{' ' * right_pad}"
    )
    return f"│ {body} │"


def _round_ms(value: float | None) -> int | None:
    if value is None:
        return None
    return round(value * 1000)


def _sum_line(parts: list[tuple[int, str]]) -> str:
    """Colored addition of the rounded milliseconds. The last part is the total."""
    shown = " + ".join(str(ms) for ms, _color in parts[:-1])
    total = parts[-1][0]
    plain = f"{shown} = {total} ms"
    colored = " + ".join(_paint(color, str(ms)) for ms, color in parts[:-1])
    colored += " = " + _paint(_BOLD + _ORANGE, f"{total} ms")
    return f"│ {colored}{' ' * max(_BOX_WIDTH - len(plain), 0)} │"


def _print_pipeline_box(
    user_text: str,
    end_of_turn: float | None,
    transcript: float | None,
    llm_ttft: float | None,
    tts_ttfb: float | None,
    total: float,
    llm_ttfs: float | None = None,
    retrieval: float | None = None,
    interrupted: bool = False,
) -> None:
    """One box for a single speech-end to first-audio path.

    End-of-turn delay already includes the time until the final transcript.
    The three stage clocks do not cover the handoffs between them.
    The measured total is the pause from speech end to the first audio frame.
    """
    quote = user_text.replace("\n", " ").strip() or "(no transcript)"
    end_ms = _round_ms(end_of_turn)
    llm_ms = _round_ms(llm_ttft)
    tts_ms = _round_ms(tts_ttfb)
    total_ms = _round_ms(total) or 0
    sentence_ms = None
    ttfs_ms = _round_ms(llm_ttfs)
    if ttfs_ms is not None and llm_ms is not None:
        sentence_ms = max(ttfs_ms - llm_ms, 0)

    other_ms = None
    if None not in (end_ms, llm_ms, tts_ms):
        other_ms = total_ms - end_ms - llm_ms - tts_ms - (sentence_ms or 0)

    if interrupted:
        verdict, verdict_color = "Reply cancelled", _ORANGE
    elif total_ms < 1000:
        verdict, verdict_color = "Under 1 second in this local test", _GREEN
    else:
        verdict, verdict_color = "This local test ran past 1 second", _ORANGE
    number = f"{total_ms} ms".rjust(8)
    gap = _BOX_WIDTH - len(number) - len(verdict)
    total_line = (
        f"{_paint(_BOLD + _ORANGE, number)}{' ' * max(gap, 2)}"
        f"{_paint(verdict_color, verdict)}"
    )

    end_label = "END OF TURN"
    if transcript is not None:
        end_label = f"END OF TURN (+ transcript {_ms(transcript)})"
    rows = [
        _metric_line(end_label, _ms(end_of_turn), _BLUE, indent=2),
        _metric_line("LLM FIRST TOKEN", _ms(llm_ttft), _PURPLE, indent=2),
    ]
    equation: list[tuple[int, str]] = []
    if end_ms is not None:
        equation.append((end_ms, _BLUE))
    if llm_ms is not None:
        equation.append((llm_ms, _PURPLE))
    if sentence_ms:
        rows.append(_metric_line("└ handoff to TTS", f"{sentence_ms} ms", _GAP, indent=6))
        equation.append((sentence_ms, _GAP))
    rows.append(_metric_line("TTS FIRST BYTE", _ms(tts_ttfb), _ORANGE, indent=2))
    if tts_ms is not None:
        equation.append((tts_ms, _ORANGE))
    if other_ms is not None and other_ms > 1:
        handoff_label = "└ handoffs between clocks"
        if retrieval is not None:
            handoff_label = f"└ handoffs between clocks (+ moss {_ms(retrieval)})"
        rows.append(_metric_line(handoff_label, f"{other_ms} ms", _GAP, indent=6))
        equation.append((other_ms, _GAP))
    elif retrieval is not None:
        rows.append(_line(f"Moss retrieval {_ms(retrieval)}, inside the handoffs."))
    equation.append((total_ms, _ORANGE))

    lines = [
        "┌" + "─" * (_BOX_WIDTH + 2) + "┐",
        _line(f'"{quote}"'),
        _rule(),
        *rows,
        _rule(),
    ]
    if other_ms is not None and other_ms < -1:
        lines.append(_line(f"These clocks overlap by {-other_ms} ms."))
    elif equation:
        lines.append(_sum_line(equation))
    lines.extend([
        f"│ {total_line} │",
        _line("Measured pause: speech end → first audio frame."),
        "└" + "─" * (_BOX_WIDTH + 2) + "┘",
    ])
    print("\n" + "\n".join(lines) + "\n", flush=True)


def _attach_timing_logs(session: AgentSession) -> None:
    """Hold the user half of a turn until the reply arrives, then print one box."""
    pending_user: dict | None = None

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        nonlocal pending_user
        item = ev.item
        if not isinstance(item, ChatMessage):
            return
        if item.role == "user":
            pending_user = {
                "text": item.text_content or "",
                "end_of_turn": item.metrics.get("end_of_turn_delay"),
                "transcript": item.metrics.get("transcription_delay"),
                "retrieval": item.metrics.get("on_user_turn_completed_delay"),
            }
            return
        if item.role != "assistant":
            return
        total = item.metrics.get("e2e_latency")
        # The greeting has no preceding user turn, so it has no end-to-end total.
        if total is None or pending_user is None:
            return
        _print_pipeline_box(
            pending_user["text"],
            pending_user["end_of_turn"],
            pending_user["transcript"],
            item.metrics.get("llm_node_ttft"),
            item.metrics.get("tts_node_ttfb"),
            total,
            item.metrics.get("llm_node_ttfs"),
            pending_user["retrieval"],
            interrupted=bool(item.interrupted),
        )
        pending_user = None

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
            # Start from a stable interim transcript. If the user continues,
            # that speculative reply is cancelled and generated again.
            preemptive_generation={"enabled": True},
        ),
    )
    print("[config] preemptive_generation=on")
    _attach_timing_logs(session)

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
