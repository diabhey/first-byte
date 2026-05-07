"""
Pre-flight check for the first-byte course.

Run before the live session:
    uv run python preflight.py

Verifies:
  - Python version is >= 3.11
  - .env is present and populated
  - LiveKit Cloud credentials authenticate
  - Moss credentials authenticate
  - Required Python packages are importable

Every check should be green before class. If a check fails, post in the
course Discord at least 24 hours before the live session.
"""

import asyncio
import os
import sys
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"


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
    if (major, minor) >= (3, 11):
        ok(f"Python {major}.{minor} (>= 3.11 required)")
        return True
    fail(f"Python {major}.{minor} found, need >= 3.11", "Install Python 3.11+ via uv or your system package manager.")
    return False


def check_env_file() -> bool:
    section("Environment file")
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        fail(".env not found", "Run `cp .env.example .env` and paste your credentials.")
        return False
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
        if val:
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
        ("livekit.plugins.turn_detector", "livekit-plugins-turn-detector"),
        ("moss", "moss"),
        ("dotenv", "python-dotenv"),
    ]:
        try:
            __import__(module)
            ok(label)
        except ImportError as exc:
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
        client = api.LiveKitAPI(url, key, secret)
        await client.room.list_rooms(api.ListRoomsRequest())
        await client.aclose()
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
        client = MossClient(project_id=project_id, project_key=project_key)
        await client.list_indexes()
        ok("Moss responded to authenticated request")
        return True
    except Exception as exc:
        fail("Moss auth failed", str(exc))
        return False


async def main() -> int:
    print(f"\n{DIM}first-byte preflight{RESET}\n")

    from dotenv import load_dotenv  # type: ignore

    load_dotenv()

    results = []
    results.append(check_python())
    results.append(check_env_file())
    env_vars_ok = all(check_env_vars().values())
    results.append(env_vars_ok)
    results.append(check_imports())

    if env_vars_ok:
        results.append(await check_livekit())
        results.append(await check_moss())

    print()
    if all(results):
        print(f"{GREEN}All checks passed.{RESET} You are ready for class.\n")
        return 0
    print(f"{RED}Some checks failed.{RESET} Fix them before the live session.\n")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
