"""Offline course checks. No credentials, microphone, downloads, or cloud writes."""

import asyncio
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import subprocess
import tomllib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


preflight = load_module("course_preflight", "preflight.py")
index_builder = load_module("course_index_builder", "sections/03-grounding-moss/build_index.py")


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "LIVEKIT_URL": "wss://course.livekit.cloud",
            "LIVEKIT_API_KEY": "test-key",
            "LIVEKIT_API_SECRET": "test-secret",
            "MOSS_PROJECT_ID": "test-project",
            "MOSS_PROJECT_KEY": "test-project-key",
            "MOSS_INDEX_NAME": "firstbyte-offline-test",
        }
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def test_credentials_are_checked_without_printing_values(self):
        with patch.dict(os.environ, self.env, clear=True):
            self.assertTrue(all(preflight.check_env_vars().values()))
        self.assertNotIn("test-secret", self.output.getvalue())
        self.assertNotIn("test-project-key", self.output.getvalue())

    def test_example_url_and_index_fail_before_network_access(self):
        self.env.update(LIVEKIT_URL="wss://your-project.livekit.cloud",
                        MOSS_INDEX_NAME="firstbyte-your-handle")
        with patch.dict(os.environ, self.env, clear=True):
            result = preflight.check_env_vars()
        self.assertFalse(result["LIVEKIT_URL"])
        self.assertFalse(result["MOSS_INDEX_NAME"])

    def test_missing_and_malformed_values_fail(self):
        self.env.update(LIVEKIT_URL="https://course.livekit.cloud",
                        LIVEKIT_API_KEY="", MOSS_INDEX_NAME="Bad index")
        with patch.dict(os.environ, self.env, clear=True):
            result = preflight.check_env_vars()
        self.assertFalse(result["LIVEKIT_URL"])
        self.assertFalse(result["LIVEKIT_API_KEY"])
        self.assertFalse(result["MOSS_INDEX_NAME"])

    def test_exported_environment_does_not_require_env_file(self):
        with patch.object(Path, "exists", return_value=False):
            self.assertTrue(preflight.check_env_file())


class CLIVersionTests(unittest.TestCase):
    def check_output(self, output):
        with patch.object(preflight.shutil, "which", return_value="/mock/lk"), \
             patch.object(preflight.subprocess, "run", return_value=SimpleNamespace(stdout=output)), \
             contextlib.redirect_stdout(io.StringIO()):
            return preflight.check_livekit_cli()

    def test_current_and_newer_stable_cli_pass(self):
        for version in ("lk version 2.19.3", "lk version 2.20.0", "lk version 2.19.3+build.1"):
            with self.subTest(version=version):
                self.assertTrue(self.check_output(version))

    def test_older_cli_fails(self):
        self.assertFalse(self.check_output("lk version 2.16.0"))

    def test_malformed_and_prerelease_versions_fail(self):
        for version in ("", "unknown version", "lk version 2.19.3-beta.1"):
            with self.subTest(version=version):
                self.assertFalse(self.check_output(version))

    def test_missing_cli_fails(self):
        with patch.object(preflight.shutil, "which", return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(preflight.check_livekit_cli())

    def test_cli_version_timeout_fails_without_traceback(self):
        with patch.object(preflight.shutil, "which", return_value="/mock/lk"), \
             patch.object(preflight.subprocess, "run", side_effect=subprocess.TimeoutExpired("lk", 5)), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(preflight.check_livekit_cli())


class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_livekit_client_is_closed_after_auth_failure(self):
        from livekit import api
        client = MagicMock()
        client.room.list_rooms = AsyncMock(side_effect=RuntimeError("request failed"))
        manager = MagicMock()
        manager.__aenter__ = AsyncMock(return_value=client)
        manager.__aexit__ = AsyncMock(return_value=False)
        with patch.dict(os.environ, {"LIVEKIT_URL": "wss://test.livekit.cloud",
                                    "LIVEKIT_API_KEY": "key", "LIVEKIT_API_SECRET": "secret"}), \
             patch.object(api, "LiveKitAPI", return_value=manager), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(await preflight.check_livekit())
        manager.__aexit__.assert_awaited_once()

    async def test_moss_auth_does_not_hang(self):
        import moss
        async def hang():
            await asyncio.sleep(60)
        client = MagicMock(list_indexes=hang)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch.dict(os.environ, {"MOSS_PROJECT_ID": "id", "MOSS_PROJECT_KEY": "key"}), \
             patch.object(moss, "MossClient", return_value=client), \
             patch.object(preflight, "AUTH_TIMEOUT_SECONDS", 0.01), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(await preflight.check_moss())


    async def test_offline_mode_never_authenticates(self):
        with patch.object(preflight, "check_python", return_value=True), \
             patch.object(preflight, "check_livekit_cli", return_value=True), \
             patch.object(preflight, "check_env_file", return_value=True), \
             patch.object(preflight, "check_env_vars", return_value={"all": True}), \
             patch.object(preflight, "check_imports", return_value=True), \
             patch.object(preflight, "check_livekit", new_callable=AsyncMock) as livekit, \
             patch.object(preflight, "check_moss", new_callable=AsyncMock) as moss, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(await preflight.main(offline=True), 0)
        livekit.assert_not_awaited()
        moss.assert_not_awaited()


class IndexSafetyTests(unittest.IsolatedAsyncioTestCase):
    def test_invalid_names_are_rejected(self):
        for name in ("", "firstbyte-your-handle", "Upper", "two words", "-start", "end-", "x" * 41):
            with self.subTest(name=name), self.assertRaises(ValueError):
                index_builder.validate_index_name(name)
        self.assertEqual(index_builder.validate_index_name("my-index-2"), "my-index-2")

    async def test_existing_index_is_preserved_without_replace(self):
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.list_indexes = AsyncMock(return_value=[SimpleNamespace(name="firstbyte-test")])
        client.delete_index = AsyncMock()
        client.create_index = AsyncMock()
        with patch.dict(os.environ, {"MOSS_PROJECT_ID": "id", "MOSS_PROJECT_KEY": "key",
                                    "MOSS_INDEX_NAME": "firstbyte-test"}), \
             patch.object(index_builder, "MossClient", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                await index_builder.main()
        client.delete_index.assert_not_called()
        client.create_index.assert_not_called()

    async def test_noncourse_replace_needs_interactive_confirmation(self):
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.list_indexes = AsyncMock(return_value=[SimpleNamespace(name="production")])
        client.delete_index = AsyncMock()
        client.create_index = AsyncMock()
        with patch.dict(os.environ, {"MOSS_PROJECT_ID": "id", "MOSS_PROJECT_KEY": "key",
                                    "MOSS_INDEX_NAME": "production"}), \
             patch.object(index_builder, "MossClient", return_value=client), \
             patch.object(sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "without confirmation"):
                await index_builder.main(replace=True)
        client.delete_index.assert_not_called()
        client.create_index.assert_not_called()

    async def test_new_index_uses_required_embedding_model(self):
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.list_indexes = AsyncMock(return_value=[])
        client.create_index = AsyncMock(return_value=SimpleNamespace(
            job_id="job", index_name="firstbyte-test", doc_count=1))
        with patch.dict(os.environ, {"MOSS_PROJECT_ID": "id", "MOSS_PROJECT_KEY": "key",
                                    "MOSS_INDEX_NAME": "firstbyte-test"}), \
             patch.object(index_builder, "MossClient", return_value=client), \
             contextlib.redirect_stdout(io.StringIO()):
            await index_builder.main()
        self.assertEqual(client.create_index.call_args.kwargs["model_id"], "moss-minilm")
        self.assertGreater(len(client.create_index.call_args.args[1]), 0)


class GroundingTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ship = load_module("course_ship_it", "sections/04-ship-it/agent.py")

    async def test_retrieval_is_injected_before_reply_with_source(self):
        from livekit.agents import ChatContext, ChatMessage
        client = MagicMock()
        client.query = AsyncMock(return_value=SimpleNamespace(docs=[SimpleNamespace(
            text="HeartByte builds voice agents.", metadata={"source": "course-notes"})]))
        agent = self.ship.HeartByteAgent(client, "firstbyte-test")
        context = ChatContext()
        with contextlib.redirect_stdout(io.StringIO()):
            await agent.on_user_turn_completed(
                context, ChatMessage(role="user", content=["What is HeartByte?"]))
        self.assertEqual(client.query.await_count, 1)
        self.assertEqual(context.items[-1].role, "system")
        self.assertIn("HeartByte builds voice agents.", context.items[-1].text_content)
        self.assertIn('source="Course Notes"', context.items[-1].text_content)

    async def test_empty_user_turn_does_not_retrieve(self):
        from livekit.agents import ChatContext, ChatMessage
        client = MagicMock(query=AsyncMock())
        agent = self.ship.HeartByteAgent(client, "firstbyte-test")
        context = ChatContext()
        await agent.on_user_turn_completed(context, ChatMessage(role="user", content=[" "]))
        client.query.assert_not_called()
        self.assertEqual(len(context.items), 0)

    async def test_retrieval_failure_does_not_crash_voice_turn(self):
        from livekit.agents import ChatContext, ChatMessage
        client = MagicMock(query=AsyncMock(side_effect=RuntimeError("unavailable")))
        agent = self.ship.HeartByteAgent(client, "firstbyte-test")
        with contextlib.redirect_stdout(io.StringIO()):
            await agent.on_user_turn_completed(
                ChatContext(), ChatMessage(role="user", content=["What is HeartByte?"]))


class ObservabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_events_print_latency_and_final_usage_without_double_counting(self):
        from livekit.agents import ChatMessage, ConversationItemAddedEvent, SessionUsageUpdatedEvent
        from livekit.agents.metrics import AgentSessionUsage, LLMModelUsage
        ship = load_module("course_ship_metrics", "sections/04-ship-it/agent.py")
        callbacks = {}
        shutdown = []
        class Session:
            usage = AgentSessionUsage(model_usage=[LLMModelUsage(
                provider="test", model="test", input_tokens=100, output_tokens=20)])
            def on(self, event):
                def register(callback):
                    callbacks[event] = callback
                    return callback
                return register
        session = Session()
        ship._attach_observability(session, SimpleNamespace(add_shutdown_callback=shutdown.append))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            callbacks["conversation_item_added"](ConversationItemAddedEvent(item=ChatMessage(
                role="assistant", content=["Hello"], metrics={"e2e_latency": .8,
                "llm_node_ttft": .2, "tts_node_ttfb": .1})))
            for _ in range(2):
                callbacks["session_usage_updated"](SessionUsageUpdatedEvent(usage=session.usage))
            await shutdown[0]()
        text = output.getvalue()
        self.assertIn("server_e2e=800ms", text)
        self.assertIn("response=COMPLETE", text)
        self.assertIn("session summary:", text)
        self.assertEqual(text.count("llm_prompt=100"), 3)
        self.assertNotIn("llm_prompt=200", text)


class LockConsistencyTests(unittest.TestCase):
    def test_root_and_deployment_have_identical_runtime_dependencies(self):
        root = tomllib.loads((ROOT / "pyproject.toml").read_text())
        deployed = tomllib.loads((ROOT / "sections/04-ship-it/pyproject.toml").read_text())
        self.assertEqual(root["project"]["dependencies"], deployed["project"]["dependencies"])
        locks = [tomllib.loads(path.read_text()) for path in
                 (ROOT / "uv.lock", ROOT / "sections/04-ship-it/uv.lock")]
        packages = [{p["name"]: p["version"] for p in lock["package"]} for lock in locks]
        for name in packages[0].keys() & packages[1].keys():
            self.assertEqual(packages[0][name], packages[1][name], name)


if __name__ == "__main__":
    unittest.main()
