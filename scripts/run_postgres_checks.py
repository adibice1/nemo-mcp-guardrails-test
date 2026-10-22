"""Run explicit diagnostics in a new internal-network, tmpfs PostgreSQL container."""

import argparse
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
DATABASE = "nemo_restore_check_automation"


def main() -> None:
    """Require opt-in and own every container/network that may be cleaned up."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="create and destroy an isolated test database")
    parser.add_argument("--backend-image", default="gms-verification:local", help="existing Linux backend dependency image")
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "HOME",
        "USERPROFILE", "APPDATA", "LOCALAPPDATA", "DOCKER_CONFIG", "DOCKER_HOST", "DOCKER_CONTEXT",
    }}

    def docker(*arguments: str, check: bool = True, capture: bool = True, timeout: int = 180):
        """Call Docker directly without a shell or inherited application credentials."""
        return subprocess.run(["docker", *arguments], env=environment, cwd=ROOT,
                              check=check, capture_output=capture, text=True, timeout=timeout)

    docker("image", "inspect", args.backend_image)
    run_id = uuid4().hex
    label = "gms.verification.run=" + run_id
    network_name = "gms-check-" + run_id
    password = secrets.token_hex(24)
    network_id = None
    container_ids = []
    try:
        network_id = docker("network", "create", "--internal", "--label", label, network_name).stdout.strip()
        postgres = docker("create", "--name", network_name + "-pg", "--label", label,
                          "--network", network_id, "--network-alias", "postgres",
                          "--tmpfs", "/var/lib/postgresql/data:rw",
                          "--env", "POSTGRES_USER=gms_check", "--env", "POSTGRES_PASSWORD=" + password,
                          "--env", "POSTGRES_DB=" + DATABASE, "postgres:16-alpine").stdout.strip()
        container_ids.append(postgres)
        docker("start", postgres)
        ready = False
        for _ in range(60):
            if docker("exec", postgres, "pg_isready", "-U", "gms_check", "-d", DATABASE,
                      check=False, timeout=5).returncode == 0:
                ready = True
                break
            time.sleep(1)
        if not ready:
            raise RuntimeError("Disposable PostgreSQL did not become ready")
        mounts = []
        for relative in ("src", "config", "scripts", "tests"):
            mounts.extend(["--mount", f"type=bind,source={ROOT / relative},target=/app/{relative},readonly"])
        worker = docker("create", "--name", network_name + "-worker", "--label", label,
                        "--network", network_id, *mounts,
                        "--env", "PYTHON_DOTENV_DISABLED=1", "--env", "GITHUB_MCP_READ_ONLY=1",
                        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "GMS_DISPOSABLE_VERIFICATION=1",
                        "--env", f"DATABASE_URL=postgresql+psycopg://gms_check:{password}@postgres:5432/{DATABASE}",
                        "--env", "GMS_JWT_SECRET=synthetic-postgres-check-secret-at-least-32-characters",
                        "--entrypoint", "python", args.backend_image,
                        "-B", "/app/tests/postgres_checks.py").stdout.strip()
        container_ids.append(worker)
        docker("start", "--attach", worker, capture=False, timeout=3600)
        code = int(docker("inspect", "--format", "{{.State.ExitCode}}", worker).stdout.strip())
        if code:
            raise SystemExit(code)
    finally:
        # IDs were returned by successful creates in this invocation; no name globbing.
        cleanup_failed = False
        for identifier in reversed(container_ids):
            if docker("rm", "--force", identifier, check=False, capture=False).returncode:
                cleanup_failed = True
        if network_id and docker("network", "rm", network_id, check=False, capture=False).returncode:
            cleanup_failed = True
        if cleanup_failed:
            raise RuntimeError("Docker cleanup failed; inspect resources labelled " + label)
        print("Disposable verification containers and network cleaned up.", flush=True)


if __name__ == "__main__":
    main()
