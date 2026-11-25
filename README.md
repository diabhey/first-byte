# first-byte

Course repository for **Production Voice AI Agents with LiveKit** by Abhimanyu Selvan. You'll run a voice agent, compare how it handles pauses and interruptions, ground its answers in a Moss index, and measure how long it takes to start replying.

**During the live session, you can just watch.** When you're ready to try the code, start with [setup](#setup) and work through the four coding sections below at your own pace. Section 1 is the presentation. The code starts in Section 2. [Course syllabus](./SYLLABUS.md)

## Setup

1. Install [Git](https://git-scm.com/install), [uv](https://docs.astral.sh/uv/getting-started/installation/), and [LiveKit CLI 2.19.4 or newer](https://docs.livekit.io/intro/basics/cli/#get-started). The commands below install Python 3.13 through uv.
2. Create a [LiveKit Cloud](https://cloud.livekit.io/) project. Copy its WebSocket URL, API key, and API secret. Run `lk cloud auth` to link the same project to the CLI. LiveKit Inference handles speech recognition, the language model, and speech synthesis.
3. Create a [Moss](https://moss.dev/) project and copy its project ID and key. Choose a unique index name such as `firstbyte-yourname`. You'll build the index in Section 4.
4. If you're starting from scratch, clone the repo and make your local configuration file. If you already have a checkout and a `.env`, open that checkout and keep your existing file.

   ```bash
   git clone https://github.com/diabhey/first-byte.git
   cd first-byte
   cp .env.example .env
   ```

   Edit `.env` and fill in `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, and `MOSS_INDEX_NAME`. Keep your credentials in the ignored `.env` file.

5. Install the locked dependencies, prepare the model assets, and check that both services authenticate.

   ```bash
   uv python install 3.13
   uv sync --frozen --python 3.13
   # No file list in this repo. Imports each installed livekit.plugins.* package
   # and calls its download_files(). This lockfile only installs Silero, and that
   # model already ships in the wheel, so this step fetches nothing.
   uv run --frozen -m livekit.agents download-files
   uv run --frozen python preflight.py
   ```

Moss supports Apple Silicon on macOS 14+, Windows x64, and Linux x64 or ARM64 with glibc 2.28+. Use Linux for the Moss exercises if you have an Intel Mac.

## Run the exercises

Run each command from the `first-byte` folder. Use headphones and allow microphone access if prompted. The agent runs in your terminal and uses LiveKit Inference over the network. Press `q` to quit before starting the next agent. Use the [learner worksheet](./LEARNER_WORKSHEET.md) if you want to record your results.

### Section 2 · Say hello

```bash
lk agent console sections/01-hello-voice/agent.py
```

Ask “How’s it going?” Check that your question is transcribed, you hear a reply, and the terminal prints `TOTAL pipeline` with whether that turn was under 1370 ms. The greeting has no total. Try pausing mid-sentence and speaking over a reply. Save those observations for the next exercise. [Hello Voice exercise](./sections/01-hello-voice/README.md)

### Section 3 · Compare turn handling

```bash
lk agent console sections/02-production-ux/agent.py
```

Repeat the same questions, pauses, and interruptions. Compare when the agent answers and how it reacts when you speak over it. [Production UX exercise](./sections/02-production-ux/README.md)

### Section 4 · Ground answers with Moss

Use an index built from the current course documents. If you already have one, skip the build command. If your index contains older course data, choose a new `MOSS_INDEX_NAME` before building.

```bash
uv run --frozen python sections/03-grounding-moss/build_index.py
```

Query the index before starting the agent. Check that it returns a source that matches the current `data/kb.json` for the first question and `(no results)` for the second.

```bash
uv run --frozen python sections/03-grounding-moss/query_index.py "Who is Abhimanyu Selvan?"
uv run --frozen python sections/03-grounding-moss/query_index.py "How do I tune a bicycle derailleur?"
```

Start the grounding agent in voice mode and check its startup status.

```bash
lk agent console sections/03-grounding-moss/agent.py
```

If you see `[moss] retrieval on`, ask “Who is Abhimanyu Selvan?” aloud, then “Tell me more about his work.” Check `[moss] searching` and `[moss] injected`. The live demo starts in this state. If your checkout starts with retrieval off, try the [optional comparison exercise](./sections/03-grounding-moss/README.md#optional-exercise-compare-retrieval-off-and-on) or run [the completed Section 5 agent](#section-5--check-the-completed-agent).

### Section 5 · Check the completed agent

```bash
lk agent console sections/04-ship-it/agent.py
```

This agent has retrieval enabled and uses the same Moss index. Repeat the Section 4 voice prompts, then check timing and usage in the terminal. [Observability exercise](./sections/04-ship-it/README.md#exercise-6-observe-one-local-worker)

## If audio gets in the way

Use `lk agent console --list-devices` to check your input and output. To try a typed turn, run the first agent in text mode and press `Ctrl+C` to quit. Text mode skips speech recognition, audio playback, and the Moss turn hook. To inspect retrieval without audio, use the standalone queries from Section 4.

```bash
lk agent console --text sections/01-hello-voice/agent.py
```

## If the agent won't start

- **SDK version is too old.** Check `pwd` and `git branch --show-current` to make sure you're using the checkout for this guide. Its lockfile uses LiveKit Agents 1.8.12. Run `uv sync --frozen --python 3.13` from that checkout to refresh your installed packages, then retry.
- **No LiveKit API key found.** Check that `.env` is in the `first-byte` folder beside `pyproject.toml`. Fill in the URL, API key, and secret for the same LiveKit Cloud project and rerun preflight. If the warning persists, pass the file explicitly with `uv run --frozen --env-file .env lk agent console sections/01-hello-voice/agent.py`.

## Optional Cloud deployment

Once the completed agent works locally, you can deploy it to your LiveKit Cloud project and try the browser orb. [Deployment steps](./sections/04-ship-it/README.md#instructor-walkthrough-deployment-lifecycle) · [Browser orb setup](./orb/README.md)
