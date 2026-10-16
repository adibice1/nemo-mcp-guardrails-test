"""Offline checks for reviewed argument targets and fail-closed decisions."""

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.github_resource_bindings import (
    InvalidResourceArguments, compile_resource_binding,
)
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject
from nemo_mcp_guardrails.resource_conditions import UnsupportedResourceCondition


def binding(action: str, resource: str, condition: str):
    """Compile a GitHub block restriction for isolated matching checks."""

    result = compile_resource_binding(InputPolicyObject("github", action, resource, "block", condition))
    assert result is not None
    return result


def main() -> None:
    """Verify observable fields, shared methods and malformed-target rejection."""

    cases = (
        ("create", "issue", 'title = "Deploy!"', "issue_write", {"method": "create", "title": "deploy!"}),
        ("update", "issue", "number = 42", "issue_write", {"method": "update", "issue_number": 42.0}),
        ("comment", "issue", "#42", "add_issue_comment", {"issue_number": 42}),
        ("create", "pull_request", 'title = "Deploy!"', "create_pull_request", {"title": "Deploy!"}),
        ("create", "pull_request", 'source_branch = "staging"', "create_pull_request", {"head": "alice:staging"}),
        ("create", "pull_request", 'target_branch = "production"', "create_pull_request", {"base": "production"}),
        ("merge", "pull_request", "#42", "merge_pull_request", {"pullNumber": 42}),
        ("review", "pull_request", "#42", "pull_request_review_write", {"method": "submit_pending", "pullNumber": 42}),
        ("delete", "file", 'path = "src/Auth.py"', "delete_file", {"path": "src/Auth.py"}),
        ("push", "file", 'path = ".env"', "push_files", {"files": [{"path": "safe.txt"}, {"path": ".env"}]}),
        ("create", "repository", 'name = "Example"', "create_repository", {"name": "example"}),
        ("fork", "repository", 'name = "Example"', "fork_repository", {"repo": "Example"}),
    )
    for action, resource, condition, tool, arguments in cases:
        assert binding(action, resource, condition).matches(tool, arguments)

    issue = binding("create", "issue", 'title = "Deploy!"')
    assert not issue.matches("issue_write", {"method": "create", "title": "other", "body": "Deploy!"})
    assert not issue.matches("issue_write", {"method": "create", "title": "Deploy"})
    assert not issue.matches("issue_write", {"method": "update", "title": "Deploy!"})
    assert not issue.matches("search_issues", {})
    path = binding("delete", "file", 'path = "src/Auth.py"')
    assert not path.matches("delete_file", {"path": "src/auth.py", "message": "src/Auth.py"})
    head = binding("create", "pull_request", 'source_branch = "staging"')
    assert not head.matches("create_pull_request", {"head": "feature", "base": "staging"})
    assert not head.matches("create_pull_request", {"head": "Staging"})

    invalid = (
        (issue, "issue_write", {}),
        (issue, "issue_write", {"method": "delete", "title": "other"}),
        (issue, "issue_write", {"method": "create", "title": None}),
        (issue, "issue_write", {"method": "create", "title": " Deploy! "}),
        (path, "delete_file", {"path": "/src/Auth.py"}),
        (path, "delete_file", {"path": "src/../src/Auth.py"}),
        (path, "delete_file", {"path": "src%2fAuth.py"}),
        (head, "create_pull_request", {"head": "alice:refs/heads/staging"}),
        (binding("merge", "pull_request", "#42"), "merge_pull_request", {"pullNumber": True}),
        (binding("merge", "pull_request", "#42"), "merge_pull_request", {"pullNumber": "42"}),
        (binding("merge", "pull_request", "#42"), "merge_pull_request", {"pullNumber": 42.5}),
        (binding("review", "pull_request", "#42"), "pull_request_review_write", {"method": "resolve_thread", "pullNumber": 42}),
        (binding("push", "file", 'path = ".env"'), "push_files", {"files": []}),
        (binding("push", "file", 'path = ".env"'), "push_files", {"files": [{"path": "safe"}, {"content": ".env"}]}),
        (binding("create", "repository", 'name = "example"'), "create_repository", {"name": "example.git"}),
    )
    for rule, tool, arguments in invalid:
        try:
            rule.matches(tool, arguments)
        except InvalidResourceArguments:
            pass
        else:
            raise AssertionError("Unobservable or malformed target was accepted.")

    for action, resource, condition in (
        ("update", "issue", 'title = "Deploy!"'),
        ("create", "issue", "#42"),
        ("review", "pull_request", 'target_branch = "production"'),
        ("update", "pull_request", 'title = "Deploy!"'),
        ("update", "pull_request", "#42"),
        ("review", "pull_request", 'source_branch = "staging"'),
        ("create", "file", 'path = ".env"'),
        ("update", "file", 'path = ".env"'),
        ("delete", "file", 'path = "../.env"'),
        ("read", "file", 'path = ".env"'),
        ("create", "repository", 'name = "example repo"'),
        ("create", "branch", 'branch = "production"'),
        ("create", "branch", 'branch = "refs/heads/main"'),
        ("push", "file", 'path = "README.md"'),
    ):
        try:
            binding(action, resource, condition)
        except UnsupportedResourceCondition:
            pass
        else:
            raise AssertionError("Unsupported action/field was accepted.")
    assert compile_resource_binding(InputPolicyObject("github", "create", "file", "block")) is None
    print("GitHub resource bindings passed: targets, shared methods, malformed and unsupported cases.")


if __name__ == "__main__":
    main()
