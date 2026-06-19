import os
from contextlib import contextmanager
from collections.abc import Iterator

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.runtime_factory import load_runtime_environment


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


def main() -> None:
    """Verify connector credential references resolve from environment values."""

    with temporary_env(
        AZURE_OPENAI_API_KEY="fake-azure-key",
        AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
        AZURE_OPENAI_API_VERSION="2024-12-01-preview",
        AZURE_OPENAI_DEPLOYMENT="fake-deployment",
        GITHUB_PERSONAL_ACCESS_TOKEN="default-github-pat",
        APP_A_GITHUB_PAT="app-a-github-pat",
        GITHUB_MCP_READ_ONLY="1",
    ):
        default_environment = load_runtime_environment()
        assert default_environment.github_pat == "default-github-pat"

        app_environment = load_runtime_environment("env:APP_A_GITHUB_PAT")
        assert app_environment.github_pat == "app-a-github-pat"

        spaced_environment = load_runtime_environment("env: APP_A_GITHUB_PAT ")
        assert spaced_environment.github_pat == "app-a-github-pat"

        try:
            load_runtime_environment("env:")
        except RuntimeError as exc:
            assert "env: is missing a variable name" in str(exc)
        else:
            raise AssertionError("Empty env credential reference should fail")

        try:
            load_runtime_environment("vault:github/app-a")
        except RuntimeError as exc:
            assert "Unsupported connector credential reference" in str(exc)
        else:
            raise AssertionError("Unsupported credential reference should fail")

        try:
            load_runtime_environment("env:MISSING_GITHUB_PAT")
        except RuntimeError as exc:
            assert "Missing connector credential environment value" in str(exc)
        else:
            raise AssertionError("Missing env credential should fail")

    print("Runtime connector credential checks passed.")
    print("- Empty credential reference uses GITHUB_PERSONAL_ACCESS_TOKEN.")
    print("- env:VAR_NAME references resolve app-specific PAT env vars.")
    print("- Empty env: references fail clearly.")
    print("- Unsupported credential reference schemes fail clearly.")
    print("- Missing env vars fail clearly.")


if __name__ == "__main__":
    main()
