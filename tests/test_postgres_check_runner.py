"""Exercise disposable runner ownership and cleanup without Docker or a database."""

from contextlib import redirect_stdout
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()

import run_postgres_checks as runner


class PostgresRunnerTests(unittest.TestCase):
    """Ensure only resources created by this invocation can be removed."""

    def invoke(self, failure=None, *, run=True):
        """Mock the Docker protocol while keeping orchestration logic real."""
        commands = []

        def docker(command, **kwargs):
            """Return owned IDs and optionally inject a partial-startup failure."""
            arguments = command[1:]
            commands.append((arguments, kwargs))
            if failure == "image" and arguments[:2] == ["image", "inspect"]:
                raise subprocess.CalledProcessError(1, command)
            if arguments[:2] == ["network", "create"]:
                output = "owned-network-id"
            elif arguments[0] == "create":
                worker = "--entrypoint" in arguments
                if failure == "worker-create" and worker:
                    raise subprocess.CalledProcessError(1, command)
                output = "owned-worker-id" if worker else "owned-postgres-id"
            elif arguments[0] == "inspect":
                output = "7" if failure == "worker-exit" else "0"
            else:
                output = ""
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        with patch.object(sys, "argv", ["run_postgres_checks.py"] + (["--run"] if run else [])), \
                patch.object(runner.subprocess, "run", side_effect=docker), \
                patch.dict(os.environ, {"PRIVATE_SENTINEL": "never-inherit"}), \
                redirect_stdout(io.StringIO()):
            try:
                runner.main()
            except (subprocess.CalledProcessError, SystemExit) as error:
                return commands, error
        return commands, None

    def test_default_never_starts_docker(self):
        """Keep the diagnostic deliberately opt-in."""
        commands, error = self.invoke(run=False)
        self.assertIsNone(error)
        self.assertEqual(commands, [])

    def test_success_uses_no_host_database_or_credentials(self):
        """Create internal networking/tmpfs, and clean only returned owned IDs."""
        commands, error = self.invoke()
        self.assertIsNone(error)
        arguments = [command for command, _ in commands]
        self.assertIn("--internal", arguments[1])
        creates = [command for command in arguments if command[0] == "create"]
        self.assertIn("--tmpfs", creates[0])
        self.assertNotIn("--publish", repr(creates))
        self.assertNotIn("--env-file", repr(creates))
        self.assertNotIn(".env", repr(creates))
        self.assertNotIn("PRIVATE_SENTINEL", repr(commands))
        self.assertIn(["rm", "--force", "owned-worker-id"], arguments)
        self.assertIn(["rm", "--force", "owned-postgres-id"], arguments)
        self.assertEqual(arguments[-1], ["network", "rm", "owned-network-id"])

    def test_partial_worker_creation_cleans_postgres_only(self):
        """Never delete a worker whose create did not return ownership."""
        commands, error = self.invoke("worker-create")
        self.assertIsInstance(error, subprocess.CalledProcessError)
        removed = [command for command, _ in commands if command[0] == "rm"]
        self.assertEqual(removed, [["rm", "--force", "owned-postgres-id"]])
        self.assertEqual(commands[-1][0], ["network", "rm", "owned-network-id"])

    def test_missing_dependency_image_creates_nothing(self):
        """Fail before network creation when the selected local image is absent."""
        commands, error = self.invoke("image")
        self.assertIsInstance(error, subprocess.CalledProcessError)
        self.assertEqual(len(commands), 1)

    def test_failing_diagnostic_is_reported_and_cleaned(self):
        """Preserve a nonzero suite result while removing both owned containers."""
        commands, error = self.invoke("worker-exit")
        self.assertIsInstance(error, SystemExit)
        self.assertEqual(error.code, 7)
        self.assertEqual(sum(command[0] == "rm" for command, _ in commands), 2)


if __name__ == "__main__":
    unittest.main()
