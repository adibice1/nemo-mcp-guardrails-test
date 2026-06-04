from dataclasses import dataclass
from pathlib import Path

import yaml
from nemoguardrails import RailsConfig

from nemo_mcp_guardrails.database.prompt_rule_loader import (
    LoadedPromptRule,
    load_prompt_policy_rules,
)


@dataclass(frozen=True)
class PromptRuleConfig:
    """Represent a NeMo config built with optional DB prompt rules."""

    rails_config: RailsConfig
    prompt_rules: tuple[LoadedPromptRule, ...]
    input_rule_count: int
    output_rule_count: int


def format_prompt_rule_block(
    rules: tuple[LoadedPromptRule, ...],
    rail_type: str,
) -> str:
    """Format loaded prompt rules as a bullet list for prompts.yml injection."""

    matching_rules = [
        rule.rule_text.strip()
        for rule in rules
        if rule.rail_type == rail_type and rule.rule_text.strip()
    ]

    if not matching_rules:
        return "- No dynamic database policy rules were loaded."

    return "\n".join(f"- {rule_text}" for rule_text in matching_rules)


def indent_continuation_lines(text: str, spaces: int) -> str:
    """Indent all but the first line for replacement inside a YAML block scalar."""

    lines = text.splitlines()
    if not lines:
        return text

    indentation = " " * spaces
    return "\n".join([lines[0], *(f"{indentation}{line}" for line in lines[1:])])


def build_rails_config_with_prompt_rules(
    config_path: str = "config",
) -> PromptRuleConfig:
    """Build a RailsConfig using config files plus compiled DB prompt rules."""

    config_dir = Path(config_path)
    prompt_rules = load_prompt_policy_rules()

    config_yaml = yaml.safe_load((config_dir / "config.yml").read_text())
    prompts_text = (config_dir / "prompts.yml").read_text()
    rails_co = (config_dir / "rails.co").read_text()

    input_policy_rules = indent_continuation_lines(
        format_prompt_rule_block(prompt_rules, "input"),
        spaces=6,
    )
    output_policy_rules = indent_continuation_lines(
        format_prompt_rule_block(prompt_rules, "output"),
        spaces=6,
    )

    rendered_prompts_text = (
        prompts_text.replace("{{ input_policy_rules }}", input_policy_rules)
        .replace("{{ output_policy_rules }}", output_policy_rules)
    )

    prompts_yaml = yaml.safe_load(rendered_prompts_text)
    merged_yaml = {**config_yaml, **prompts_yaml}

    rails_config = RailsConfig.from_content(
        colang_content=rails_co,
        yaml_content=yaml.safe_dump(merged_yaml, sort_keys=False),
    )

    return PromptRuleConfig(
        rails_config=rails_config,
        prompt_rules=prompt_rules,
        input_rule_count=sum(rule.rail_type == "input" for rule in prompt_rules),
        output_rule_count=sum(rule.rail_type == "output" for rule in prompt_rules),
    )
