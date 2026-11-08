"""Load the course's local models and run native inference without credentials.

Run after `uv run --frozen -m livekit.agents download-files`.
This checks binary/model compatibility; silence is not a conversational test.
"""

import math

import numpy as np
from livekit.agents import inference
from livekit.local_inference import EOT, EOT_MAX_SAMPLES, init_eot
from livekit.plugins import silero


def main() -> None:
    detector = inference.TurnDetector(version="v1-mini")
    if detector.model != "turn-detector-v1-mini":
        raise RuntimeError("The course requires the local v1-mini turn detector")

    init_eot()
    with EOT() as model:
        probability = model.predict(np.zeros(EOT_MAX_SAMPLES, dtype=np.int16))
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise RuntimeError(f"Native end-of-turn inference returned {probability!r}")
    print(f"Local v1-mini model loaded; silence inference probability={probability:.4f}")

    vad = silero.VAD.load()
    print(f"{vad.provider}/{vad.model} VAD loaded")
    print("Local model compatibility passed; no Cloud calls or credentials used.")


if __name__ == "__main__":
    main()
