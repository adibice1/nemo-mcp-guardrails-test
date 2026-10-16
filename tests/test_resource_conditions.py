"""Offline grammar checks without database, environment or external services."""

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.resource_conditions import (
    ResourceCondition,
    UnsupportedResourceCondition,
    parse_resource_condition,
)


def main() -> None:
    """Verify supported literal selectors and rejection of ambiguous logic."""

    for empty in (None, "", "  "):
        assert parse_resource_condition("issue", empty) is None

    supported = (
        ("issue", "test", "title", "test"),
        ("issue", 'issue named "test"', "title", "test"),
        ("issue", "Issues called 'Release Ready!'", "title", "Release Ready!"),
        ("issue", 'title = "Release Ready!"', "title", "Release Ready!"),
        ("issue", 'title = "  Release  "', "title", "  Release  "),
        ("issue", 'title = "Fix and verify"', "title", "Fix and verify"),
        ("issue", 'title = "Fix \\"quoted\\" text"', "title", 'Fix "quoted" text'),
        ("issue", 'title = "日本語の課題"', "title", "日本語の課題"),
        ("issue", "issue #42", "number", 42),
        ("issue", "numbered 42", "number", 42),
        ("issue", "number = 42", "number", 42),
        ("pull_request", "pull requests #42", "number", 42),
        ("pull_request", 'title = "Release"', "title", "Release"),
        ("pull_request", 'source_branch = "staging"', "source_branch", "staging"),
        ("pull_request", 'target_branch = "Production"', "target_branch", "Production"),
        ("file", 'files path "src/Auth.py"', "path", "src/Auth.py"),
        ("file", 'path = ".env"', "path", ".env"),
        ("file", "src/Auth.py", "path", "src/Auth.py"),
        ("branch", 'branches named "Release/v1"', "branch", "Release/v1"),
        ("branch", 'branch = "release/v1"', "branch", "release/v1"),
        ("repository", "repositories named 'My.Repo'", "name", "My.Repo"),
        ("repository", 'name = "My.Repo"', "name", "My.Repo"),
    )
    for resource, text, field, value in supported:
        assert parse_resource_condition(resource, text) == ResourceCondition(field, value), text

    unsupported = (
        ("issue", 'path = "test"'),
        ("file", 'title = "test"'),
        ("branch", "#42"),
        ("commit", 'name = "main"'),
        ("issue", "Release Ready"),
        ("issue", "title = test"),
        ("issue", 'title != "test"'),
        ("issue", 'title == "test"'),
        ("issue", 'title = "test" or title = "other"'),
        ("issue", '"test" and "other"'),
        ("issue", 'title = "test" trailing'),
        ("issue", 'title = "unterminated'),
        ("issue", 'title = ""'),
        ("issue", "''"),
        ("issue", 'title = "\\n"'),
        ("issue", 'title = "\\u0000"'),
        ("issue", 'title = "\\ud800"'),
        ("issue", 'title = "\\udfff"'),
        ("issue", "title = 'test\\n'"),
        ("issue", "number = 0"),
        ("issue", "number = -1"),
        ("issue", "number = 01"),
        ("issue", 'number = "42"'),
        ("issue", "number = 4.2"),
        ("issue", "number = true"),
        ("issue", "x" * 1001),
        ("issue", 42),
        ("issue", {"title": "test"}),
        ("pull_request", "whose target is production and whose source is not staging"),
        ("pull_request", "whose target branch is production and whose source branch is not staging"),
        ("pull_request", 'target_branch = "production" OR source_branch != "staging"'),
        ("pull_request", "merge only after A -> B -> C"),
    )
    for resource, text in unsupported:
        try:
            parse_resource_condition(resource, text)
        except UnsupportedResourceCondition:
            pass
        else:
            raise AssertionError(f"Unsupported condition was accepted: {text!r}")

    assert parse_resource_condition("file", "src/Auth.py") != parse_resource_condition(
        "file", "src/auth.py",
    )
    assert parse_resource_condition("issue", '"a.b"') != parse_resource_condition("issue", '"a b"')
    print(f"Resource grammar checks passed: {len(supported)} selectors, {len(unsupported)} rejections.")


if __name__ == "__main__":
    main()
