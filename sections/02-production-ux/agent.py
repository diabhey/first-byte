"""
Section 2: Turn detection that doesn't cut people off.

Two upgrades over Section 1, one per side of the conversation: LiveKit's
open-weights end-of-turn model replaces VAD-only silence timeouts, and barge-in
is switched on and tuned so backchannels do not cut the agent off. Same
pipeline otherwise. Preemptive generation starts inference before the final
turn boundary so the first audible reply can arrive sooner.

Run:
    uv run python sections/02-production-ux/agent.py dev
"""

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    ChatMessage,
    ConversationItemAddedEvent,
    JobContext,
    MetricsCollectedEvent,
    WorkerOptions,
    cli,
)
from livekit.agents.metrics import EOUMetrics, LLMMetrics, TTSMetrics
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


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
    """Print component timing and exact perceived latency."""
    # Once generation is preemptive, EOU, LLM, and TTS work may overlap. Their
    # individual metrics remain useful diagnostics, but adding them would
    # overstate what the user waited. ChatMessage.metrics["e2e_latency"] is the
    # SDK's direct speech-end → first-server-audio measurement.

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        m = ev.metrics
        if isinstance(m, EOUMetrics):
            # With MultilingualModel, unfinished transcripts should keep this
            # from firing too early during a mid-thought pause.
            print(
                f"[timing] end-of-utterance delay: {m.end_of_utterance_delay:.2f}s "
                f"(silence → turn committed)"
            )
            print(
                f"[timing] transcription delay:    {m.transcription_delay:.2f}s "
                f"(speech end → final transcript)"
            )
        elif isinstance(m, LLMMetrics) and not m.cancelled:
            print(f"[timing] LLM TTFT (first token): {m.ttft:.2f}s")
        elif isinstance(m, TTSMetrics) and not m.cancelled:
            print(f"[timing] TTS TTFB (first byte):  {m.ttfb:.2f}s")

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if not isinstance(item, ChatMessage) or item.role != "assistant":
            return

        e2e_latency = item.metrics.get("e2e_latency")
        if e2e_latency is None:
            return  # initial greeting has no preceding user turn

        llm_ttft = item.metrics.get("llm_node_ttft")
        tts_ttfb = item.metrics.get("tts_node_ttfb")
        llm_value = f"{llm_ttft * 1000:.0f}ms" if llm_ttft is not None else "n/a"
        tts_value = f"{tts_ttfb * 1000:.0f}ms" if tts_ttfb is not None else "n/a"
        response_status = "CANCELLED" if item.interrupted else "COMPLETE"
        print(
            f"[latency] perceived={e2e_latency * 1000:.0f}ms "
            f"response={response_status} preemptive=on | "
            f"llm_ttft={llm_value} tts_ttfb={tts_value}"
        )


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        # The headline of this section. Semantic end-of-turn detection that
        # uses the STT transcript to predict whether the user is actually
        # done, instead of just timing out on acoustic silence.
        turn_detection=MultilingualModel(),
        # Barge-in, off in Section 1, switched on here. Interruption is a
        # separate system from turn detection: it decides when to stop the
        # AGENT, while turn_detection decides when the USER is finished.
        allow_interruptions=True,
        # Keep hearing the user even mid-reply, so an interrupted question is
        # not lost and does not have to be repeated.
        discard_audio_if_uninterruptible=False,
        # Raised from the 0.5s default so a cough or a chair creak cannot stop
        # the agent on acoustic energy alone.
        min_interruption_duration=0.7,
        # The important one. With the default of 0, any half second of sound
        # barges in, including "mm-hm", "yeah", and "right" while the agent is
        # still making its point. Requiring two real transcribed words lets
        # those backchannels through without cutting the reply short.
        min_interruption_words=2,
        # Safety net for interruptions that turn out to be noise: if no
        # transcript arrives within the timeout, resume the paused reply
        # instead of leaving the agent stuck mid-sentence.
        false_interruption_timeout=2.0,
        resume_false_interruption=True,
        # Start LLM and TTS work when a stable transcript arrives rather than
        # waiting for the final end-of-turn decision. The SDK cancels stale
        # speculative work if the transcript changes before the turn commits.
        preemptive_generation=True,
    )
    print("[config] preemptive_generation=on")
    _attach_timing_logs(session)

    await session.start(agent=HelloAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
