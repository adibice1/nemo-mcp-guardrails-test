"""Offline regression for canonical title selectors in block explanations."""

import os
from types import SimpleNamespace
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Check readable title attribution without using it as an enforcement decision."""
    with patch.dict(os.environ, {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "defaults",
    }):
        from nemo_mcp_guardrails.api.runtime import _matching_input_policy_explanation
        from nemo_mcp_guardrails.policy_compiler import InputPolicyObject

        def explain(selector: str | None, message: str):
            """Explain one synthetic app-scoped issue policy."""
            policy = InputPolicyObject("github", "create", "issue", "block", selector)
            parts = SimpleNamespace(input_policy_entries=(
                SimpleNamespace(policy=policy, source_id=17),
            ))
            return _matching_input_policy_explanation(message, parts)

        for selector in ('title = "release[1]"', 'issue named "release[1]"'):
            result = explain(selector, 'Create a GitHub issue titled release[1].')
            assert result is not None
            assert result.policy_id == 17 and result.stage == "input"
            assert result.reason == "Blocked due to request to create a GitHub issue matching release[1]."
            assert result.policy_name == "Github create issue matching release[1]"
        assert explain('title = "test"', 'Create a GitHub issue titled contest.') is None
        assert explain('title = "test"', 'Create a GitHub issue titled testing.') is None
        assert explain('title = "test"', 'Read a GitHub issue titled test.') is None
        assert explain('title = "test"', 'Create a GitHub issue titled another.') is None
        assert explain('any issue where the title is test', 'Create a GitHub issue titled test.') is None
        assert explain(None, 'Create a GitHub issue titled another.').policy_id == 17
        assert explain('title = "Test"', 'Create a GitHub issue titled TEST.').policy_id == 17

    print("Block explanation checks passed: canonical/legacy titles, literal boundaries and safe fallback.")


if __name__ == "__main__":
    main()
