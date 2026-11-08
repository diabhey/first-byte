# Course readiness and Cloud-agent recovery

This is the delivery checklist for **Production Voice AI Agents with LiveKit**. The [README](./README.md) owns installation and run commands; the [teaching guide](./TEACHING_GUIDE.md) supplies the presentation and exercise cues. Course section numbers are used throughout; coding directory numbers are one lower.

## Refresh baseline: 8 November 2026

The refresh targets LiveKit Agents and Silero **1.8.11**, with independently locked root and deployable environments. The examples use the current agent-server, turn-handling, conversation-metrics, and session-usage APIs, with the built-in local audio turn detector pinned to `v1-mini`. The deprecated text turn-detector plugin is removed. Local development uses LiveKit CLI **2.19.3+** with an isolated, randomly named dev deployment selected explicitly in Agent Console. The browser orb uses the pinned LiveKit JS client **2.23.0**.

Automated tests can validate imports, configuration, exercise behavior, and model-loading compatibility. They cannot establish that a particular Cloud project has usable credits, that a deleted deployment has been restored, that a participant's microphone works, or that the final experience meets a latency target. Complete the live gates below before describing the course as rehearsed.

## Checks completed during the refresh

| Check | Observed result | Scope |
| --- | --- | --- |
| Dependency refresh | Root and deployable locks updated together; obsolete dependency PR versions superseded | Reproducible dependency baseline |
| Automated behavior tests | 21 Python tests and 5 Node tests passed locally | Configuration, retrieval/error paths, event handlers, browser lifecycle |
| Browser setup check | Actual browser displayed the missing-configuration guard; external JS/CDN imports loaded | Page startup and setup feedback |
| LiveKit Inference network smoke | `openai/gpt-4o-mini` returned a reply; `cartesia/sonic-3` generated audio; streaming `deepgram/nova-3:en` transcribed generated speech | Individual provider connectivity using the selected course project |
| Cloud inventory | Read-only project inventory and agent-status queries succeeded; existing sleeping deployments were found | Confirms account access and avoids blindly recreating an existing agent |
| Current development CLI | CLI 2.19.3 launched the Hello Voice file, registered its isolated dev worker, and stopped cleanly | Worker registration and new command syntax; not a completed call |
| Model asset preparation | SDK `download-files` completed; Silero loaded and the bundled audio turn model initialized | Installed model assets and native model loading |
| Linux deployment image | Full `linux/amd64` Docker build passed; non-root UID 10001 loaded both models with networking disabled | Linux install/build and runtime asset availability; not a Cloud deployment |
| Native audio model | Bundled local turn model initialized and processed a silence input on Apple Silicon | Native library/model compatibility; not conversational accuracy |

The provider smoke test did not start an agent job or prove a room/agent/browser call. Moss credentials, the intended deployed image, real microphone interaction, and the opening demo need their own live evidence. A sleeping Cloud agent is an existing deployment; its status alone does not validate the refreshed source.

## Required delivery assets

| Asset | Repository location | Check before delivery |
| --- | --- | --- |
| Student preparation and commands | [README](./README.md), [.env.example](./.env.example), [preflight.py](./preflight.py) | Run from a fresh clone with the committed locks |
| Learning objectives and two-hour schedule | [SYLLABUS](./SYLLABUS.md) | Match organizer's current agenda |
| Presentation and facilitation cues | [TEACHING_GUIDE](./TEACHING_GUIDE.md) | Open alongside the code; a separate slide deck is optional |
| VAD-only and semantic-turn comparison | [Hello Voice](./sections/01-hello-voice/README.md), [Production UX](./sections/02-production-ux/README.md) | Rehearse identical phrases on both agents |
| Retrieval exercise and course data | [Grounding with Moss](./sections/03-grounding-moss/README.md) | Query a dedicated course index; preserve the commented exercise hook |
| Complete grounded agent and deployment project | [Ship It](./sections/04-ship-it/README.md) | Build, deploy, and make a real call |
| Browser client | [Orb](./orb/README.md) | Fresh token, microphone permission, audible answer, clean reconnect |

## Rebuild a deleted Cloud agent

Deleting an agent removes its deployment identity. It does not necessarily remove the LiveKit project, a separate Moss index, local CLI credentials, or another agent in another project. Inspect the selected project before creating anything.

1. Finish the [setup and preflight](./README.md#pre-class-setup). Select the intended **course** project explicitly:

   ```bash
   lk project list
   lk project set-default "<your-course-project-name>"
   lk agent list
   ```

2. If the intended agent still appears, inspect it with `lk agent status --id "<existing-agent-id>"`. A sleeping agent still exists. Restore its local config with `lk agent config` when appropriate, then use `lk agent deploy` for a new version. Check project selection before interpreting a not-found error.
3. If the old agent ID is confirmed deleted, move its local `sections/04-ship-it/livekit.toml` outside the repository as a backup. Do not copy placeholder IDs from `livekit.toml.example`; `create` must generate a fresh ID.
4. Verify the dedicated course Moss index. If it still exists, query it using the [retrieval inspection commands](./sections/03-grounding-moss/README.md#2-inspect-retrieval-before-adding-it-to-voice). If absent, run `build_index.py` with a unique course index name. Use `--replace` only for an intentional rebuild of an index you own; it deletes first.
5. Create the replacement from the self-contained project:

   ```bash
   cd sections/04-ship-it
   lk agent create --secrets-file=../../.env
   lk agent secrets
   lk agent status
   lk agent logs
   ```

   The secrets file must contain your `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, and `MOSS_INDEX_NAME`. LiveKit supplies its own project credentials. Deleted deployment secrets cannot be read back: obtain Moss values from your own local secret store or dashboard. Confirm the three secret **names** are present; keep values private.
6. Test the new deployment with [Agent Console](https://docs.livekit.io/testing/agent-console/) and the [local orb](./orb/README.md). Stop local dev workers before testing automatic dispatch to Cloud. Mint the token from the same project and use a new room name for each rehearsal.
7. Keep the generated, gitignored `livekit.toml`. Future updates use `lk agent deploy`. If a separate public website selects an agent by dispatch name or ID, update its server-side configuration to the intended new deployment and test that website separately.

## Live rehearsal gates

Record these in your private delivery notes, including the tested commit, date, project, and any observed latency. Do not commit credentials, room tokens, or participant recordings.

| Gate | Evidence required | Current delivery status |
| --- | --- | --- |
| Fresh student setup | CLI 2.19.3+ and locked install on representative student platforms; all normal preflight checks pass | Must be confirmed on the delivery environment |
| Model cache | SDK `download-files` succeeds before the live session | Passed locally and in the Linux image; repeat on student machines |
| LiveKit Inference | Real STT transcript, generated reply, and TTS audio using the course model strings | Individual provider smoke passed; full room/browser call pending |
| Turn handling | Same pause and interruption script run on Hello Voice and Production UX | Requires microphone/audio rehearsal |
| Moss grounding | Known question returns course documents; enabled hook injects results; unknown facts handled honestly | Requires your course Moss credentials and index |
| Observability | Several turns show timing and cumulative usage; disconnect prints final summary | Requires a completed session |
| Cloud deployment | Successful image build, healthy agent, secrets configured, call reaches Cloud worker | Linux image and inventory/status checks passed; refreshed Cloud deployment/call pending |
| Orb lifecycle | Connect, microphone, audible reply, disconnect, reconnect with a fresh room/token | Setup guard/browser startup passed; real voice rehearsal pending |
| Opening demo | Course orb works; public HeartByte demo checked separately if used | Do not assume a previous public deployment still works |
| Class capacity and support | Account access, credits/quotas, support channel, and alternate network confirmed | Confirm with the organizer before class |

A green local or CI check is useful evidence for its own scope. It does not close the live-call and Cloud-deployment gates.

## Course-day preparation

- **One week before:** rehearse a fresh install and Cloud build; verify platform prerequisites, accounts, credits, and the organizer's agenda. Use a dedicated course project/index.
- **One day before:** complete all live gates, retain a working deployed example, and prepare a short local recording of the comparison and final grounded call if the course permits recordings. Keep screenshots/logs of retrieval and timing as an audio-free fallback.
- **Thirty minutes before:** run normal preflight, confirm the demo agent's health, open the code and teaching guide, connect headphones, test the microphone and screen sharing, mint fresh room tokens, and close competing dev workers.
- **After class:** revoke temporary sharing/tokens as needed, stop unused workers, and retain only the intended course deployment. Check the account's usage dashboard.

## Organizer listing changes to request

The [published O'Reilly listing](https://www.oreilly.com/live-events/production-voice-ai-agents-with-livekit/0642572366988/) was compared with the repository on 8 November 2026. Local exercises now use `lk agent dev` with CLI 2.19.3+ and explicit development-deployment selection in Agent Console instead of the older Playground flow. The repository now teaches `AgentServer` in place of the listed `WorkerOptions`, and the local audio `inference.TurnDetector(version="v1-mini")` in place of the deprecated transcript-based `MultilingualModel`. The observability exercise inspects the complete shipped agent; the listing's `agent_start.py` stub is not part of this repository. The local orb instructions use a one-hour test token rather than the listing's 24-hour token. Prerequisites should name the supported Python/platform range and include model downloads. The five-minute break is explicit in the repository's 120-minute schedule. The opening demo should be described as the self-contained course orb, with the public HeartByte site optional after rehearsal.

These changes are prepared in the repository. Updating O'Reilly's page requires the organizer's publishing process.

## Current reference sources

- [LiveKit agent deployment quickstart](https://docs.livekit.io/deploy/agents/quickstart/)
- [Deployment configuration and new versions](https://docs.livekit.io/deploy/agents/managing-deployments/)
- [Agent secrets](https://docs.livekit.io/deploy/agents/secrets/)
- [Agent Console](https://docs.livekit.io/testing/agent-console/)
- [Audio turn detection](https://docs.livekit.io/agents/logic/turns/turn-detector/)
- [LiveKit Agents Python releases](https://github.com/livekit/agents/releases)
