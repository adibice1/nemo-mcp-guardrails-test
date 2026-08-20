import os
from collections.abc import Iterator
from contextlib import contextmanager

from _bootstrap import bootstrap_src

bootstrap_src()
os.environ["NEMO_POLICY_SOURCE"] = "defaults"

from nemo_mcp_guardrails.runtime_factory import (
    RuntimeEnvironment,
    github_mcp_client_config,
)


@contextmanager
def temporary_env(**values: str | None) -> Iterator[None]:
    """Temporarily set or remove environment variables."""

    original_values = {name: os.environ.get(name) for name in values}
    try:
        for name, value in values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        yield
    finally:
        for name, value in original_values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def build_environment() -> RuntimeEnvironment:
    """Create non-secret runtime values for launch configuration tests."""

    return RuntimeEnvironment(
        azure_api_key="fake-azure-key",
        azure_endpoint="https://example.openai.azure.com",
        azure_api_version="2024-12-01-preview",
        azure_deployment="fake-deployment",
        github_pat="fake-github-pat",
        github_mcp_read_only="1",
    )


def main() -> None:
    """Verify source and container GitHub MCP launch configurations."""

    environment = build_environment()

    with temporary_env(
        GITHUB_MCP_LAUNCH_MODE=None,
        GITHUB_MCP_BINARY_PATH=None,
    ):
        docker_config = github_mcp_client_config(environment)
        assert docker_config["command"] == "docker"
        assert "ghcr.io/github/github-mcp-server" in docker_config["args"]

    with temporary_env(
        GITHUB_MCP_LAUNCH_MODE="native",
        GITHUB_MCP_BINARY_PATH=None,
    ):
        native_config = github_mcp_client_config(environment)
        assert native_config["command"] == "/usr/local/bin/github-mcp-server"
        assert native_config["args"] == ["stdio"]

    with temporary_env(
        GITHUB_MCP_LAUNCH_MODE="native",
        GITHUB_MCP_BINARY_PATH="/custom/github-mcp-server",
    ):
        custom_config = github_mcp_client_config(environment)
        assert custom_config["command"] == "/custom/github-mcp-server"

    for config in (docker_config, native_config, custom_config):
        assert config["transport"] == "stdio"
        assert config["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "fake-github-pat"
        assert config["env"]["GITHUB_READ_ONLY"] == "1"
        assert config["env"]["GITHUB_TOOLSETS"] == "repos,issues,pull_requests"

    with temporary_env(GITHUB_MCP_LAUNCH_MODE="invalid"):
        try:
            github_mcp_client_config(environment)
        except RuntimeError as exc:
            assert "must be either 'native' or 'docker'" in str(exc)
        else:
            raise AssertionError("Invalid GitHub MCP launch mode should fail")

    print("Runtime GitHub MCP launch-mode checks passed.")
    print("- Source runs default to the Docker launcher.")
    print("- Container runs can use the bundled native stdio binary.")
    print("- Credential, read-only and toolset environment values are preserved.")
    print("- Invalid launch modes fail clearly.")


if __name__ == "__main__":
    main()
