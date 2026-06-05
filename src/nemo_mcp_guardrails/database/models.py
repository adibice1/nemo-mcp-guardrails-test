from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class AppRecord(Base):
    """Persist one protected app or connector."""

    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AppActionRecord(Base):
    """Persist one action supported by one app."""

    __tablename__ = "app_actions"
    __table_args__ = (
        UniqueConstraint("app_id", "name", name="uq_app_actions_app_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AppResourceRecord(Base):
    """Persist one resource supported by one app."""

    __tablename__ = "app_resources"
    __table_args__ = (
        UniqueConstraint("app_id", "name", name="uq_app_resources_app_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ToolMappingRecord(Base):
    """Map an app/action/resource combination to a concrete tool name."""

    __tablename__ = "tool_mappings"
    __table_args__ = (
        UniqueConstraint(
            "app_id",
            "action_id",
            "resource_id",
            "tool_name",
            name="uq_tool_mappings_app_action_resource_tool",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    action_id: Mapped[int] = mapped_column(
        ForeignKey("app_actions.id", ondelete="CASCADE"),
        index=True,
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("app_resources.id", ondelete="CASCADE"),
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(200), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PolicyRecord(Base):
    """Persist one input or output policy object."""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_type: Mapped[str] = mapped_column(String(20), index=True)
    app: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect: Mapped[str] = mapped_column(String(20), default="block")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AllowedTestCaseRecord(Base):
    """Persist one safe test prompt that should pass the guardrails."""

    __tablename__ = "allowed_test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    expected_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AllowedTestCaseExpectedToolRecord(Base):
    """Map one allowed test case to one expected tool mapping."""

    __tablename__ = "allowed_test_case_expected_tools"
    __table_args__ = (
        UniqueConstraint(
            "allowed_test_case_id",
            "tool_mapping_id",
            name="uq_allowed_test_case_expected_tools_case_tool",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    allowed_test_case_id: Mapped[int] = mapped_column(
        ForeignKey("allowed_test_cases.id", ondelete="CASCADE"),
        index=True,
    )
    tool_mapping_id: Mapped[int] = mapped_column(
        ForeignKey("tool_mappings.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CompiledPolicyRuleRecord(Base):
    """Persist generated NeMo rail rule text for one policy."""

    __tablename__ = "compiled_policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"),
        index=True,
    )
    rail_type: Mapped[str] = mapped_column(String(20), index=True)
    rule_text: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
