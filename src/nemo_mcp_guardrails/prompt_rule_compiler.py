import json
import re
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


def literal_prompt_rule_block(
    rules: tuple[LoadedPromptRule, ...],
    rail_type: str,
) -> str:
    """Encode policy rules as a literal Jinja value, never as template code."""

    rule_text = format_prompt_rule_block(rules, rail_type)
    return "{{ " + json.dumps(rule_text, ensure_ascii=False) + " }}"


def build_rails_config_with_prompt_rules(
    config_path: str = "config",
    app_id: int | None = None,
    *,
    prompt_rules: tuple[LoadedPromptRule, ...] | None = None,
) -> PromptRuleConfig:
    """Build a RailsConfig using compiled DB rules, optionally scoped to one app."""

    config_dir = Path(config_path)
    if prompt_rules is None:
        prompt_rules = load_prompt_policy_rules(app_id=app_id)

    config_yaml = yaml.safe_load((config_dir / "config.yml").read_text())
    prompts_yaml = yaml.safe_load((config_dir / "prompts.yml").read_text())
    rails_co = (config_dir / "rails.co").read_text()

    policy_rule_blocks = {
        "input_policy_rules": literal_prompt_rule_block(prompt_rules, "input"),
        "output_policy_rules": literal_prompt_rule_block(prompt_rules, "output"),
    }

    for prompt in prompts_yaml.get("prompts", []):
        if isinstance(prompt.get("content"), str):
            prompt["content"] = re.sub(
                r"\{\{\s*(input_policy_rules|output_policy_rules)\s*\}\}",
                lambda match: policy_rule_blocks[match.group(1)],
                prompt["content"],
            )

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
