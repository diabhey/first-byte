# Teaching guide: Production Voice AI Agents with LiveKit

Use this as presentation notes alongside the [syllabus](./SYLLABUS.md), section READMEs, and code. It supplies the delivery cues; installation and runnable commands stay in the linked READMEs. Complete the [readiness checklist](./COURSE_READINESS.md) before delivering the course. Course section numbers are used throughout.

## Run of show

| Elapsed time | Segment | Evidence learners should see |
| --- | --- | --- |
| 00:00–00:15 | 1. Voice agents and the first-byte problem | Finished grounded call; pipeline and latency budget |
| 00:15–00:45 | 2. Your first voice agent | Hello Voice call, measured wait, failed interruption |
| 00:45–01:00 | 3. Production UX | Semantic turn detection and tuned interruption comparison |
| 01:00–01:05 | Break | Stop the worker; preserve the code state |
| 01:05–01:35 | 4. Grounding with Moss | Documents, retrieval results, then grounded voice answers |
| 01:35–01:55 | 5. Observability and deployment | Timing, cumulative usage, Cloud agent, local orb call |
| 01:55–02:00 | Wrap-up and questions | Each learner's next validation step |

## Section 1: Explain the system before the code

**Presentation, 10 minutes.** Draw the path: microphone → LiveKit room → agent worker → STT → retrieval → LLM → TTS → room → speaker. Put Silero VAD and semantic turn detection next to incoming audio. Explain which work runs locally and which model requests use LiveKit Inference. Contrast the chained pipeline with speech-to-speech: independent stages give us a way to inspect and replace components.

Define the user-facing measurement as speech-end to first agent audio. Distinguish LLM time-to-first-token from TTS time-to-first-byte. Use 800 ms as a target to investigate; show several measurements and avoid promising it for every model, network, and turn. Retrieval and preemptive generation can overlap other work, so component times do not always add.

**Demo, 5 minutes.** Use the rehearsed course orb and complete grounded agent. Ask “What is HeartByte?” and “What is Abhi's three-phase method?” Show one result in the knowledge base and one timing observation. Use the public HeartByte site only if it passed the rehearsal. If audio is unavailable, play the prepared recording and trace the same request through code/logs.

## Section 2: A deliberately imperfect first agent

Open [Hello Voice](./sections/01-hello-voice/README.md). Explain `Agent` as behavior, `AgentSession` as the pipeline, `JobContext` as the room/job handle, and `AgentServer` as the process that accepts sessions. Point to the three Inference model strings and local Silero VAD. One set of LiveKit credentials covers the remote model requests; that does not remove credits or quota limits.

Run Exercises 1–2 using `lk agent dev` with LiveKit CLI 2.19.3+ as shown in the section README. Show the generated `dev-...` deployment in the terminal and select that exact target in Agent Console; the default production target can reach a different worker. Have learners say “What's two plus two?”, record the measured wait, pause inside an unfinished question, and speak over the reply. The baseline intentionally ignores interruptions. Ask learners to name the two independent decisions: when the user finished a thought and when the agent should stop speaking.

**Checkpoint:** a transcript and audible reply, timing output, and a reproducible interruption failure. If no reply arrives, check project selection, the selected `dev-...` deployment, the active section’s worker, model downloads, microphone permission, and project credits before changing the prompt.

## Section 3: Compare behavior with the same audio

Open [Production UX](./sections/02-production-ux/README.md). Explain audio-based semantic end-of-turn detection with the local `v1-mini` model, interruption duration/word thresholds, and resuming a false interruption. Show that the settings now live in `TurnHandlingOptions`. Describe preemptive generation as speculative inference from an interim transcript that can be cancelled when the turn changes.

Select the new worker’s printed dev deployment, then repeat the exact script from Hello Voice: unfinished thought, paused location question, full interruption, short backchannel. Invite learners to compare several complete turns rather than a single best latency. Natural speech is variable; explain deviations from the expected behavior rather than guaranteeing them.

**Checkpoint:** learners can identify the turn detector, the interruption settings, and the server-latency field. Stop this worker before the break.

## Section 4: Inspect retrieval before connecting it to voice

Open [Grounding with Moss](./sections/03-grounding-moss/README.md) and the supplied `data/kb.json`. Explain the always-retrieve pattern: retrieval runs before the reply, avoiding an extra LLM decision about whether to call a search tool. Treat latency claims as hypotheses to measure on the actual index and hardware.

For Exercise 4, build a unique course index, inspect the “What is HeartByte?” results, then compare alpha zero and one. Explain top-k and source metadata. Never overwrite an index merely to keep the demo moving; use a fresh course name when ownership is uncertain.

For Exercise 5, run the agent with the shipped commented hook and ask “Who's Abhi?” Then stop it, uncomment the complete hook, restart, and ask again. Trace the query, result formatting, temporary system context, and grounded reply. Retrieved text is reference data; it does not get to issue instructions. Explain why changing the context invalidates speculative ungrounded output.

**Checkpoint:** inspect retrieval output and see the hook's injection log before claiming grounding. If Moss access fails, show the supplied KB and trace the hook using prepared retrieval output; leave live grounding marked unverified.

## Section 5: Observe, then ship the same worker

Open [Ship It](./sections/04-ship-it/README.md). Exercise 6 uses the complete agent, with observability active. Trace `conversation_item_added` to turn metrics, `session_usage_updated` to cumulative usage, and the shutdown callback to the final summary. A greeting has no preceding user turn; interrupted or empty replies need separate interpretation. Ask learners which stage appears to dominate the measured wait.

Show the self-contained deployment directory and its separate lockfile. Explain that `create` registers a new Cloud identity and `deploy` updates an existing one. A deleted ID must be recreated; a sleeping deployment still exists. Use the [recovery runbook](./COURSE_READINESS.md#rebuild-a-deleted-cloud-agent) when needed.

Start the rehearsed deploy walkthrough, check status and secret names, then call from the local orb with a fresh token from the same project. If the build exceeds the five-minute demonstration slot, inspect its progress and call the pre-rehearsed deployment; complete the new build after class. Keep live deployment success separate from showing an existing agent.

Explain the public-site extension briefly: mint per-visitor tokens on a server, use isolated rooms, and rate-limit the token endpoint. Handoffs, telephony, avatars, vision, and self-hosting are follow-up topics. They are not exercises implemented in this repo.

## Wrap-up

Ask each learner to name one bottleneck they measured and the next validation they will run. Point to the README and section exercises for continuation, the readiness checklist for delivery/deployment gates, and official LiveKit/Moss documentation for further work.
