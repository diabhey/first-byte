"""
Pre-flight check for the first-byte course.

Run before the live session:
    uv run python preflight.py

Verifies:
  - Python version is >= 3.11 and < 3.15
  - LiveKit CLI >= 2.19.3 is installed
  - Credentials are populated in .env or the exported environment
  - LiveKit Cloud credentials authenticate
  - Moss credentials authenticate
  - Required Python packages are importable

Use --offline to check local setup without contacting either service.
Credentials are still validated for presence and format. This does not test
Inference access, model downloads, audio, Moss index readiness, or deployment.
"""

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"
AUTH_TIMEOUT_SECONDS = 15
MIN_LIVEKIT_CLI_VERSION = (2, 19, 3)
MOSS_INDEX_PLACEHOLDER = "firstbyte-your-handle"
MOSS_INDEX_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?")


def ok(msg: str) -> None:
    print(f"  {GREEN}OK{RESET}  {msg}")


def fail(msg: str, hint: str | None = None) -> None:
    print(f"  {RED}FAIL{RESET}  {msg}")
    if hint:
        print(f"        {DIM}{hint}{RESET}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}WARN{RESET}  {msg}")


def section(title: str) -> None:
    print(f"\n{title}")


def check_python() -> bool:
    section("Python")
    major, minor = sys.version_info[:2]
    if (3, 11) <= (major, minor) < (3, 15):
        ok(f"Python {major}.{minor} (3.11–3.14 supported)")
        return True
    fail(f"Python {major}.{minor} found, need 3.11–3.14", "Install Python 3.13 via `uv python install 3.13`.")
    return False


def check_livekit_cli() -> bool:
    section("LiveKit CLI")
    minimum = ".".join(map(str, MIN_LIVEKIT_CLI_VERSION))
    if not shutil.which("lk"):
        fail("lk command not found", "Install the LiveKit CLI, then run `lk cloud auth`.")
        return False
    try:
        result = subprocess.run(["lk", "--version"], capture_output=True,
                                text=True, check=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        fail("Could not read the LiveKit CLI version",
             "Check `lk --version` and reinstall the CLI if needed.")
        return False
    match = re.search(r"\blk version v?(\d+)\.(\d+)\.(\d+)(?=$|\s|\+)",
                      result.stdout.strip())
    if not match:
        fail("Unrecognized LiveKit CLI version",
             f"Install a stable CLI release >= {minimum}; check `lk --version`.")
        return False
    version = tuple(map(int, match.groups()))
    installed = ".".join(map(str, version))
    if version < MIN_LIVEKIT_CLI_VERSION:
        fail(f"LiveKit CLI {installed} found; need >= {minimum}",
             "Upgrade the CLI for `lk agent dev` (macOS: `brew upgrade livekit-cli`).")
        return False
    ok(f"LiveKit CLI {installed} (>= {minimum} required)")
    return True


def check_env_file() -> bool:
    section("Environment file")
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        warn(".env not found; checking exported environment variables instead")
        return True
    ok(f".env present at {env_path}")
    return True


def check_env_vars() -> dict[str, bool]:
    section("Environment variables")
    required = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "MOSS_PROJECT_ID",
        "MOSS_PROJECT_KEY",
        "MOSS_INDEX_NAME",
    ]
    results = {}
    for key in required:
        val = os.environ.get(key, "").strip()
        try:
            parsed_url = urlparse(val) if key == "LIVEKIT_URL" else None
            valid_url = bool(parsed_url and parsed_url.scheme == "wss"
                             and parsed_url.hostname
                             and "your-project" not in parsed_url.hostname.lower())
        except ValueError:
            valid_url = False
        if key == "LIVEKIT_URL" and val and not valid_url:
            fail("LIVEKIT_URL must be your project's wss:// URL",
                 "Replace the example URL with the value from LiveKit Cloud.")
            results[key] = False
        elif key == "MOSS_INDEX_NAME" and val == MOSS_INDEX_PLACEHOLDER:
            fail(
                "MOSS_INDEX_NAME is still the placeholder",
                "Set it to your own index name, such as `firstbyte-yourname`.",
            )
            results[key] = False
        elif key == "MOSS_INDEX_NAME" and val and MOSS_INDEX_PATTERN.fullmatch(val) is None:
            fail(
                "MOSS_INDEX_NAME is not a valid index name",
                "Use 1-40 lowercase letters, digits, and hyphens, starting and "
                "ending with a letter or digit.",
            )
            results[key] = False
        elif val:
            ok(f"{key} set")
            results[key] = True
        else:
            fail(f"{key} not set", "Paste it into .env from your provider dashboard.")
            results[key] = False
    return results


def check_imports() -> bool:
    section("Required packages")
    all_ok = True
    for module, label in [
        ("livekit.agents", "livekit-agents"),
        ("livekit.plugins.silero", "livekit-plugins-silero"),
        ("livekit.agents.inference", "LiveKit Inference (built-in turn detector)"),
        ("moss", "moss"),
        ("dotenv", "python-dotenv"),
    ]:
        try:
            __import__(module)
            ok(label)
        except Exception as exc:
            fail(f"{label} not importable", f"Run `uv sync`. Error: {exc}")
            all_ok = False
    return all_ok


async def check_livekit() -> bool:
    section("LiveKit Cloud auth")
    try:
        from livekit import api  # type: ignore
    except ImportError:
        fail("livekit.api not importable", "Run `uv sync`.")
        return False

    url = os.environ.get("LIVEKIT_URL", "")
    key = os.environ.get("LIVEKIT_API_KEY", "")
    secret = os.environ.get("LIVEKIT_API_SECRET", "")
    if not (url and key and secret):
        warn("Skipping LiveKit auth check (env vars missing)")
        return False

    try:
        async with asyncio.timeout(AUTH_TIMEOUT_SECONDS):
            async with api.LiveKitAPI(url, key, secret) as client:
                await client.room.list_rooms(api.ListRoomsRequest())
        ok("LiveKit Cloud responded to authenticated request")
        return True
    except Exception as exc:
        fail("LiveKit Cloud auth failed", str(exc))
        return False


async def check_moss() -> bool:
    section("Moss auth")
    try:
        from moss import MossClient  # type: ignore
    except ImportError:
        fail("moss not importable", "Run `uv sync`.")
        return False

    project_id = os.environ.get("MOSS_PROJECT_ID", "")
    project_key = os.environ.get("MOSS_PROJECT_KEY", "")
    if not (project_id and project_key):
        warn("Skipping Moss auth check (env vars missing)")
        return False

    try:
        async with asyncio.timeout(AUTH_TIMEOUT_SECONDS):
            async with MossClient(project_id=project_id, project_key=project_key) as client:
                await client.list_indexes()
        ok("Moss responded to authenticated request")
        return True
    except Exception as exc:
        fail("Moss auth failed", str(exc))
        return False


async def main(*, offline: bool = False) -> int:
    print(f"\n{DIM}first-byte preflight{RESET}\n")

    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        fail("python-dotenv not importable", "Run `uv sync --frozen` first.")
        return 1
    load_dotenv(Path(__file__).parent / ".env")

    results = []
    results.append(check_python())
    results.append(check_livekit_cli())
    results.append(check_env_file())
    env_vars_ok = all(check_env_vars().values())
    results.append(env_vars_ok)
    results.append(check_imports())

    if offline:
        warn("Offline mode: LiveKit and Moss authentication were not tested")
    elif env_vars_ok:
        results.append(await check_livekit())
        results.append(await check_moss())

    print()
    if all(results):
        scope = "Local setup checks" if offline else "Setup and authentication checks"
        print(f"{GREEN}{scope} passed.{RESET}\n")
        print("Still rehearse model downloads, voice, retrieval, and deployment before class.\n")
        return 0
    print(f"{RED}Some checks failed.{RESET} Fix them before the live session.\n")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="Check local setup and credential format without network requests.")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(offline=args.offline)))
