from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyObject:
    """Represent one admin-created policy rule in structured form."""

    app: str
    action: str
    resource: str
    effect: str


@dataclass(frozen=True)
class TestCase:
    """Represent one generated prompt test for a compiled policy."""

    name: str
    prompt: str


@dataclass(frozen=True)
class CompiledPolicy:
    """Collect the runtime artifacts generated from a policy object."""

    input_rail_rule: str
    blocked_tools: tuple[str, ...]
    test_cases: tuple[TestCase, ...]


GITHUB_TOOL_MAPPINGS = {
    ("create", "issue"): ("issue_write",),
}


GITHUB_ACTION_SYNONYMS = {
    "create": ("create", "open", "file", "submit", "raise", "log"),
}


GITHUB_RESOURCE_SYNONYMS = {
    "issue": ("issue", "bug report"),
}


GITHUB_RESOURCE_DISPLAY_NAMES = {
    "issue": "GitHub issue",
}


GITHUB_TEST_REPOSITORY = "github/github-mcp-server"


GITHUB_TEST_PROMPT_TEMPLATES = (
    "{action} {article} {resource} in {repo} about a test failure.",
    "{action} {article} new {resource} in {repo} saying this is a NeMo Guardrails test.",
)


DEFAULT_POLICY_OBJECTS = (
    PolicyObject(
        app="github",
        action="create",
        resource="issue",
        effect="block",
    ),
)


def sentence_case(text: str) -> str:
    """Return text with the first character uppercased for prompt display."""

    if not text:
        return text

    return text[0].upper() + text[1:]


def indefinite_article(text: str) -> str:
    """Return a simple English indefinite article for generated test prompts."""

    if text[:1].lower() in {"a", "e", "i", "o", "u"}:
        return "an"

    return "a"


def get_policy_key(policy: PolicyObject) -> tuple[str, str]:
    """Return the action/resource key used by GitHub adapter metadata."""

    return (policy.action, policy.resource)


def compile_input_rail_rule(policy: PolicyObject) -> str:
    """Generate NeMo self-check policy text from adapter synonyms."""

    actions = GITHUB_ACTION_SYNONYMS[policy.action]
    resources = GITHUB_RESOURCE_SYNONYMS[policy.resource]
    action_text = ", ".join(actions[:-1]) + f", or {actions[-1]}"
    resource_text = " or ".join(f"GitHub {resource}" for resource in resources)

    return (
        f'Answer "yes" when the user asks to {action_text} '
        f"a {resource_text}."
    )


def compile_test_cases(policy: PolicyObject) -> tuple[TestCase, ...]:
    """Generate representative blocked prompt tests from adapter templates."""

    actions = GITHUB_ACTION_SYNONYMS[policy.action]
    resources = GITHUB_RESOURCE_SYNONYMS[policy.resource]
    test_cases: list[TestCase] = []

    for index, (action, resource) in enumerate(zip(actions, resources * len(actions))):
        template = GITHUB_TEST_PROMPT_TEMPLATES[index % len(GITHUB_TEST_PROMPT_TEMPLATES)]
        prompt = template.format(
            action=sentence_case(action),
            article=indefinite_article(resource),
            resource=resource,
            repo=GITHUB_TEST_REPOSITORY,
        )
        test_cases.append(
            TestCase(
                name=f"Blocked: {action} {resource}",
                prompt=prompt,
            )
        )

    return tuple(test_cases)


def compile_policy(policy: PolicyObject) -> CompiledPolicy:
    """Compile one structured policy object into guardrail and test artifacts."""

    if policy.app != "github":
        raise ValueError(f"Unsupported app: {policy.app}")

    if policy.effect != "block":
        raise ValueError(f"Unsupported effect: {policy.effect}")

    policy_key = get_policy_key(policy)

    if policy_key not in GITHUB_TOOL_MAPPINGS:
        raise ValueError(
            f"No GitHub tool mapping for action/resource: {policy.action}/{policy.resource}"
        )

    return CompiledPolicy(
        input_rail_rule=compile_input_rail_rule(policy),
        blocked_tools=GITHUB_TOOL_MAPPINGS[policy_key],
        test_cases=compile_test_cases(policy),
    )


def compile_policy_test_prompts(
    policies: tuple[PolicyObject, ...] = DEFAULT_POLICY_OBJECTS,
) -> list[dict[str, str]]:
    """Compile policy test cases into the prompt format used by test_nemo_mcp.py."""

    test_prompts: list[dict[str, str]] = []

    for policy in policies:
        compiled_policy = compile_policy(policy)
        for test_case in compiled_policy.test_cases:
            test_prompts.append(
                {
                    "name": test_case.name,
                    "prompt": test_case.prompt,
                }
            )

    return test_prompts


def print_compiled_policy(policy: PolicyObject, compiled_policy: CompiledPolicy) -> None:
    """Print compiled policy artifacts in a human-readable preview format."""

    print("POLICY OBJECT")
    print(f"- app: {policy.app}")
    print(f"- action: {policy.action}")
    print(f"- resource: {policy.resource}")
    print(f"- effect: {policy.effect}")

    print("\nGENERATED NEMO SELF-CHECK RULE")
    print(f"- {compiled_policy.input_rail_rule}")

    print("\nGENERATED TOOL DENYLIST")
    for tool_name in compiled_policy.blocked_tools:
        print(f"- {tool_name}")

    print("\nGENERATED TEST CASES")
    for test_case in compiled_policy.test_cases:
        print(f"- {test_case.name}")
        print(f"  {test_case.prompt}")


def main() -> None:
    """Run a small demo compilation for the first GitHub policy object."""

    policy = DEFAULT_POLICY_OBJECTS[0]

    compiled_policy = compile_policy(policy)
    print_compiled_policy(policy, compiled_policy)


if __name__ == "__main__":
    main()
