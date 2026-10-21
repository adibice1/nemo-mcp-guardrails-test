"""Run the explicit offline regression catalogue with no inherited credentials."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OFFLINE_TESTS = (
    "test_app_main_models", "test_model_gateway",
    "test_branch_routing",
    "test_security_controls", "test_management_password_change", "test_management_audit_http",
    "test_app_authorization_http", "test_app_llm_grant_migration", "test_app_llm_grants_http",
    "test_connector_credential_security", "test_llm_endpoint_security",
    "test_output_classifier_fail_closed", "test_policy_fail_closed", "test_prompt_rule_literals",
    "test_resource_conditions", "test_github_resource_bindings", "test_resource_condition_inventory",
    "test_input_condition_storage", "test_runtime_policy_snapshot", "test_github_tool_contract",
    "test_runtime_policy_integration", "test_policy_assistant_http", "test_policy_options_capabilities",
    "test_tool_guard", "test_output_guard", "test_runtime_cache", "test_runtime_llm_grants",
    "test_runtime_connector_credentials", "test_runtime_mcp_launch", "test_runtime_llm_selection",
    "test_runtime_block_explanations", "test_runtime_debug_privacy", "test_runtime_events", "test_runtime_logs_http", "test_request_timing",
)
CHILD = """
import runpy, sys, socket, threading
internal = threading.local()
original_pair = socket.socketpair
def socketpair(*args, **kwargs):
    internal.socketpair = True
    try:
        return original_pair(*args, **kwargs)
    finally:
        internal.socketpair = False
socket.socketpair = socketpair
def deny_network(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo'} and not getattr(internal, 'socketpair', False):
        raise RuntimeError('External sockets are disabled by the offline regression runner')
sys.addaudithook(deny_network)
target = sys.argv[1]
sys.argv = [target]
runpy.run_path(target, run_name='__main__')
"""


def main() -> None:
    """Never discover and execute database/live tests implicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="classify checks without executing them")
    parser.add_argument("--test", action="append", choices=OFFLINE_TESTS, help="run only a named offline check")
    args = parser.parse_args()
    if args.list:
        for name in OFFLINE_TESTS:
            print(f"offline/disposable: {name}")
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if path.stem not in OFFLINE_TESTS:
                print(f"external/manual opt-in; excluded: {path.stem}")
        return
    environment = {k: os.environ[k] for k in (
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
    ) if k in os.environ}
    environment.update({
        "PYTHON_DOTENV_DISABLED": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "DATABASE_URL": "sqlite://", "GITHUB_MCP_READ_ONLY": "1",
        "PYTHONPATH": os.pathsep.join(str(ROOT / folder) for folder in ("src", "tests", "scripts")),
    })
    failed = []
    for name in args.test or OFFLINE_TESTS:
        print(f"Checking {name} ...", flush=True)
        try:
            result = subprocess.run([sys.executable, "-B", "-c", CHILD, str(ROOT / "tests" / f"{name}.py")],
                                    cwd=ROOT, env=environment, timeout=180)
            if result.returncode:
                failed.append(name)
        except subprocess.TimeoutExpired:
            failed.append(name)
            print(f"Timed out: {name}", flush=True)
    print(f"Offline checks: {len(args.test or OFFLINE_TESTS) - len(failed)} passed, {len(failed)} failed.")
    if failed:
        print("Failed: " + ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
