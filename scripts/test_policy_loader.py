import argparse

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.database.policy_loader import (
    load_input_policy_objects,
    load_output_policy_objects,
)
from nemo_mcp_guardrails.database.prompt_rule_loader import (
    load_prompt_policy_rules,
)
from nemo_mcp_guardrails.policy_compiler import (
    compile_blocked_tools,
    compile_output_rail_rules,
)


def print_section(title: str) -> None:
    """Print a readable section heading."""

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def parse_args() -> argparse.Namespace:
    """Parse an optional client-app ID for assignment-aware loader testing."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--app-id", type=int)
    return parser.parse_args()


def main() -> None:
    """Print the active policies loaded from the database policy loader."""

    args = parse_args()
    input_policies = load_input_policy_objects(app_id=args.app_id)
    output_policies = load_output_policy_objects(app_id=args.app_id)
    prompt_rules = load_prompt_policy_rules(app_id=args.app_id)

    print_section("Policy scope")
    if args.app_id is None:
        print(
            "No app ID was provided. For current implementation and testing "
            "purposes, every enabled policy will be loaded. Production "
            "requests must require an authenticated app ID."
        )
    else:
        print(f"- app ID: {args.app_id}")

    print_section("Loaded input policies")
    for policy in input_policies:
        print(
            f"- {policy.connector} {policy.action} {policy.resource} "
            f"{policy.effect}"
        )

    print_section("Compiled blocked tools")
    for tool_name in sorted(compile_blocked_tools(input_policies)):
        print(f"- {tool_name}")

    print_section("Loaded output policies")
    for policy in output_policies:
        print(f"- {policy.category} {policy.effect}: {policy.description}")

    print_section("Compiled output rail rules")
    for rule in compile_output_rail_rules(output_policies):
        print(f"- {rule}")

    print_section("Loaded compiled prompt rules")
    for rule in prompt_rules:
        print(f"- {rule.rail_type} policy #{rule.policy_id}: {rule.rule_text}")


if __name__ == "__main__":
    main()
