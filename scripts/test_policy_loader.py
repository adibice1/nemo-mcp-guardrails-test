from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.database.policy_loader import (
    load_input_policy_objects,
    load_output_policy_objects,
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


def main() -> None:
    """Print the active policies loaded from the database policy loader."""

    input_policies = load_input_policy_objects()
    output_policies = load_output_policy_objects()

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


if __name__ == "__main__":
    main()
