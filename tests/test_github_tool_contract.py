"""Offline checks for reviewed write routes, schemas and conditional artifacts."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Exercise pure contract logic without dotenv, database, model or MCP startup."""

    with patch("dotenv.load_dotenv", side_effect=AssertionError("Unexpected dotenv load")):
        from nemo_mcp_guardrails.github_resource_bindings import InvalidResourceArguments
        from nemo_mcp_guardrails.github_tool_contract import (
            REVIEWED_MCP_IMAGE, compile_github_execution_rule, select_reviewed_github_tools,
        )
        from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
        from nemo_mcp_guardrails.policy_compiler import (
            GITHUB_WRITE_TOOL_MAPPINGS, InputPolicyObject, compile_policy, compile_policy_test_prompts,
        )
        from nemo_mcp_guardrails.resource_conditions import UnsupportedResourceCondition

        assert f"FROM {REVIEWED_MCP_IMAGE} AS github_mcp" in Path("Dockerfile").read_text()

        def rule(action, resource, selector=None):
            """Compile a rule against the same reviewed policy capability gate."""

            return compile_github_execution_rule(InputPolicyObject("github", action, resource, "block", selector))

        def indeterminate(executable, name, arguments) -> None:
            """Require an explicit evaluation error rather than an allowed write."""

            try:
                executable.matches(name, arguments)
            except InvalidResourceArguments as error:
                assert "PRIVATE" not in str(error)
            else:
                raise AssertionError("Indeterminate write route was accepted")

        create = rule("create", "issue", 'title = "Deploy!"')
        assert create.matches("issue_write", {"method": "create", "title": "DEPLOY!"})
        assert not create.matches("issue_write", {"method": "create", "title": "other", "body": "Deploy!"})
        assert not create.matches("issue_write", {"method": "update", "title": "Deploy!"})
        assert not create.matches("search_issues", {})
        for arguments in ({}, {"method": "PRIVATE_METHOD"}, {"method": "create"},
                          {"method": "create", "title": True}, {"method": "create", "title": " Deploy! "}):
            indeterminate(create, "issue_write", arguments)
        broad_create = rule("create", "issue")
        assert broad_create.matches("issue_write", {"method": "create"})
        assert not broad_create.matches("issue_write", {"method": "update"})
        assert rule("update", "pull_request").matches("issue_write", {"method": "update"})
        assert not rule("update", "pull_request").matches("issue_write", {"method": "create"})
        update = rule("update", "issue", "number = 42")
        for name, arguments in (("issue_write", {"method": "update", "issue_number": 42.0}),
                                ("update_pull_request", {"pullNumber": 42}), ("merge_pull_request", {"pullNumber": 42})):
            assert update.matches(name, arguments)
        assert not update.matches("update_pull_request", {"pullNumber": 43, "body": "42"})
        indeterminate(update, "update_pull_request", {"pullNumber": "42"})
        assert rule("comment", "issue", "#42").matches("add_issue_comment", {"issue_number": 42})
        for field, argument in (("source_branch", "head"), ("target_branch", "base")):
            branch = rule("create", "pull_request", f'{field} = "Production"')
            assert branch.matches("create_pull_request", {argument: "Production"})
            assert not branch.matches("create_pull_request", {argument: "production", "title": "Production"})
        assert rule("create", "pull_request", 'source_branch = "release"').matches(
            "create_pull_request", {"head": "alice:release"})
        review = rule("review", "pull_request", "#42")
        assert review.matches("pull_request_review_write", {"method": "submit_pending", "pullNumber": 42})
        indeterminate(review, "pull_request_review_write", {"method": "resolve_thread", "threadId": "PRIVATE", "pullNumber": 42})
        assert rule("review", "pull_request").matches("pull_request_review_write", {"method": "resolve_thread"})
        path = rule("delete", "file", 'path = "src/Auth.py"')
        assert path.matches("delete_file", {"path": "src/Auth.py"})
        assert not path.matches("delete_file", {"path": "src/auth.py", "message": "src/Auth.py"})
        indeterminate(path, "merge_pull_request", {"pullNumber": 42, "path": "src/Auth.py"})
        push = rule("push", "file", 'path = ".env"')
        for name in ("create_or_update_file", "delete_file"):
            assert push.matches(name, {"path": ".env"})
            assert not push.matches(name, {"path": "safe.txt", "content": ".env"})
        assert push.matches("push_files", {"files": [{"path": "safe"}, {"path": ".env"}]})
        indeterminate(push, "push_files", {"files": [{"path": ".env"}, {"content": "PRIVATE"}]})
        for name, arguments in (("merge_pull_request", {"pullNumber": 42}),
                                ("create_repository", {"name": "safe", "autoInit": True}),
                                ("fork_repository", {"repo": "safe"})):
            indeterminate(push, name, arguments)
        assert not push.matches("create_repository", {"name": "safe"})
        repository = rule("create", "repository", 'name = "Example"')
        assert repository.matches("create_repository", {"name": "example"})
        assert repository.matches("fork_repository", {"repo": "EXAMPLE"})
        assert not repository.matches("fork_repository", {"repo": "other", "owner": "Example"})
        for action, resource in (("create", "branch"), ("create", "file"), ("update", "file"), ("push", "file")):
            assert rule(action, resource).matches("push_files", {})
        assert rule("create", "branch").matches("create_or_update_file", {})  # Empty-repo initialization.
        for action, resource in (("create", "file"), ("update", "file"), ("delete", "file"), ("push", "file")):
            assert rule(action, resource).matches("merge_pull_request", {})
        for action, resource in (("create", "branch"), ("create", "file"), ("push", "file")):
            executable = rule(action, resource)
            assert executable.matches("fork_repository", {})
            assert executable.matches("create_repository", {"autoInit": True})
            assert not executable.matches("create_repository", {})
            assert not executable.matches("create_repository", {"autoInit": False})
            indeterminate(executable, "create_repository", {"autoInit": "false"})
        try:
            create.routes = ()
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("Execution rule was mutable")
        assert "Deploy!" not in repr(create)

        for action, resource, selector in (
            ("read", "file", None), ("create", "branch", 'branch = "production"'),
            ("update", "file", 'path = ".env"'), ("create", "file", 'path = ".env"'),
            ("review", "pull_request", 'target_branch = "production"'),
            ("create", "pull_request", "whose target is production and source is not staging"),
        ):
            policy = InputPolicyObject("github", action, resource, "block", selector)
            for compile_value in (lambda: compile_policy(policy),
                                  lambda: prepare_input_conditions(policy, {"custom_resource": selector})):
                try:
                    compile_value()
                except (UnsupportedResourceCondition, ValueError):
                    pass
                else:
                    raise AssertionError("Unsupported policy capability was accepted")

        # Every supported literal produces a matching, narrow blocked prompt.
        for action, resource, selector, value in (
            ("create", "issue", 'title = "O\'Reilly 日本語!"', "O'Reilly 日本語!"),
            ("update", "issue", "number = 42", 42),
            ("comment", "issue", "#42", 42),
            ("create", "pull_request", 'source_branch = "Release"', "Release"),
            ("create", "pull_request", 'target_branch = "Production"', "Production"),
            ("merge", "pull_request", "#42", 42), ("review", "pull_request", "#42", 42),
            ("delete", "file", 'path = "src/Auth.py"', "src/Auth.py"),
            ("push", "file", 'path = ".env"', ".env"),
            ("create", "repository", 'name = "example"', "example"),
            ("fork", "repository", 'name = "example"', "example"),
        ):
            policy = InputPolicyObject("github", action, resource, "block", selector)
            compiled = compile_policy(policy)
            literal = json.dumps(value, ensure_ascii=False)
            assert literal in compiled.input_rail_rule
            assert "unrelated fields" in compiled.input_rail_rule
            assert literal in compiled.test_cases[0].prompt
            assert compile_policy_test_prompts((policy,))[0]["prompt"] == compiled.test_cases[0].prompt
            assert set(compiled.blocked_tools) == rule(action, resource, selector).tool_names
        for action, resource in GITHUB_WRITE_TOOL_MAPPINGS:
            compiled = compile_policy(InputPolicyObject("github", action, resource, "block"))
            assert compiled.test_cases
            assert set(compiled.blocked_tools) <= {name for names in GITHUB_WRITE_TOOL_MAPPINGS.values() for name in names}

        def fake_tool(name, schema):
            """Represent an adapter tool without any callable MCP boundary."""

            return SimpleNamespace(name=name, args_schema=schema)

        def schema(**fields):
            """Build independent minimal fixtures from the reviewed upstream schemas."""

            return {"type": "object", "properties": {name: {"type": kind} for name, kind in fields.items()}}

        schemas = {
            "issue_write": schema(method="string", title="string", issue_number="number"),
            "add_issue_comment": schema(issue_number="number"),
            "create_pull_request": schema(title="string", head="string", base="string"),
            "update_pull_request": schema(pullNumber="number"),
            "merge_pull_request": schema(pullNumber="number"),
            "pull_request_review_write": schema(method="string", pullNumber="number"),
            "create_branch": schema(branch="string"),
            "create_or_update_file": schema(path="string"),
            "delete_file": schema(path="string"),
            "push_files": schema(files="array"),
            "create_repository": schema(name="string", autoInit="boolean"),
            "fork_repository": schema(repo="string"),
        }
        schemas["issue_write"]["properties"]["method"]["enum"] = ["create", "update"]
        schemas["pull_request_review_write"]["properties"]["method"]["enum"] = [
            "create", "submit_pending", "delete_pending", "resolve_thread", "unresolve_thread",
        ]
        schemas["push_files"]["properties"]["files"]["items"] = {
            "type": "object", "properties": {"path": {"type": "string"}},
        }
        assert set(schemas) == {name for names in GITHUB_WRITE_TOOL_MAPPINGS.values() for name in names}
        tools = [fake_tool(name, schema) for name, schema in schemas.items()]
        read = fake_tool("search_repositories", {"type": "object", "properties": {}})
        unknown = fake_tool("PRIVATE_UNREVIEWED_WRITE", None)
        assert select_reviewed_github_tools([*tools, read, unknown]) == tuple([*tools, read])
        assert select_reviewed_github_tools([read]) == (read,)  # Read-only catalogues are valid.

        def rejected(tools) -> None:
            """Require a generic contract error without server-provided details."""

            try:
                select_reviewed_github_tools(tools)
            except ValueError as error:
                assert str(error) == "GitHub MCP tool contract is unavailable."
            else:
                raise AssertionError("Unreviewed tool schema was accepted")

        rejected([])
        rejected([unknown])
        rejected([read, read])
        rejected([fake_tool(None, {})])
        rejected([fake_tool("issue_write", None)])
        for name, schema in schemas.items():
            broken = deepcopy(schema)
            broken["properties"].pop(next(iter(schema["properties"])))
            rejected([fake_tool(name, broken)])
        for value in (None, ["string", "null"], "boolean"):
            broken = deepcopy(schemas["issue_write"])
            broken["properties"]["title"]["type"] = value
            rejected([fake_tool("issue_write", broken)])
        broken = deepcopy(schemas["issue_write"])
        broken["properties"]["method"]["enum"].append("PRIVATE_METHOD")
        rejected([fake_tool("issue_write", broken)])
        for items in (None, {"type": "object", "properties": {"path": None}},
                      {"type": "object", "properties": {"path": {"type": "number"}}}):
            broken = deepcopy(schemas["push_files"])
            broken["properties"]["files"]["items"] = items
            rejected([fake_tool("push_files", broken)])
        print("GitHub contract passed: field-bound rules, indirect writes, schema gate and literal compiler artifacts.")


if __name__ == "__main__":
    main()
