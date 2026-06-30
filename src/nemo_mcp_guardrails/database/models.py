from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class UserRecord(Base):
    """Persist one developer or administrator using the GMS."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255))
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

    app_links: Mapped[list[AppUserRecord]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class LlmConfigRecord(Base):
    """Persist one selectable main-agent or guardrail LLM configuration."""

    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(200))
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    credential_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
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


class AppRecord(Base):
    """Persist one client application authorized to consume the GMS."""

    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    client_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )
    api_key_hash: Mapped[str] = mapped_column(String(255))
    authorized: Mapped[bool] = mapped_column(Boolean, default=True)
    main_llm_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    guardrail_llm_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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

    main_llm_config: Mapped[LlmConfigRecord | None] = relationship(
        foreign_keys=[main_llm_config_id],
    )
    guardrail_llm_config: Mapped[LlmConfigRecord | None] = relationship(
        foreign_keys=[guardrail_llm_config_id],
    )
    user_links: Mapped[list[AppUserRecord]] = relationship(
        back_populates="app",
        cascade="all, delete-orphan",
    )
    connector_links: Mapped[list[AppConnectorRecord]] = relationship(
        back_populates="app",
        cascade="all, delete-orphan",
    )
    policy_assignments: Mapped[list[AppPolicyAssignmentRecord]] = relationship(
        back_populates="app",
        cascade="all, delete-orphan",
    )
    conversation_messages: Mapped[list[ConversationMessageRecord]] = relationship(
        back_populates="app",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ConnectorRecord(Base):
    """Persist one external connector supported by the GMS."""

    __tablename__ = "connectors"

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

    app_links: Mapped[list[AppConnectorRecord]] = relationship(
        back_populates="connector",
        cascade="all, delete-orphan",
    )


class AppUserRecord(Base):
    """Link one user to one client app with a management role."""

    __tablename__ = "app_users"
    __table_args__ = (
        UniqueConstraint(
            "app_id",
            "user_id",
            name="uq_app_users_app_id_user_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="viewer",
        server_default="viewer",
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

    app: Mapped[AppRecord] = relationship(back_populates="user_links")
    user: Mapped[UserRecord] = relationship(back_populates="app_links")


class AppConnectorRecord(Base):
    """Link one client app to one enabled external connector."""

    __tablename__ = "app_connectors"
    __table_args__ = (
        UniqueConstraint(
            "app_id",
            "connector_id",
            name="uq_app_connectors_app_id_connector_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    connector_id: Mapped[int] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"),
        index=True,
    )
    credential_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
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

    app: Mapped[AppRecord] = relationship(back_populates="connector_links")
    connector: Mapped[ConnectorRecord] = relationship(
        back_populates="app_links",
    )


class ConnectorActionRecord(Base):
    """Persist one action supported by one connector."""

    __tablename__ = "connector_actions"
    __table_args__ = (
        UniqueConstraint(
            "connector_id",
            "name",
            name="uq_connector_actions_connector_id_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"),
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


class ConnectorResourceRecord(Base):
    """Persist one resource supported by one connector."""

    __tablename__ = "connector_resources"
    __table_args__ = (
        UniqueConstraint(
            "connector_id",
            "name",
            name="uq_connector_resources_connector_id_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"),
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


class ConnectorToolMappingRecord(Base):
    """Map a connector/action/resource combination to a concrete tool name."""

    __tablename__ = "connector_tool_mappings"
    __table_args__ = (
        UniqueConstraint(
            "connector_id",
            "action_id",
            "resource_id",
            "tool_name",
            name="uq_connector_tool_mappings_connector_action_resource_tool",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"),
        index=True,
    )
    action_id: Mapped[int] = mapped_column(
        ForeignKey("connector_actions.id", ondelete="CASCADE"),
        index=True,
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("connector_resources.id", ondelete="CASCADE"),
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
    connector_id: Mapped[int | None] = mapped_column(
        ForeignKey("connectors.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    action_id: Mapped[int | None] = mapped_column(
        ForeignKey("connector_actions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("connector_resources.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    # Compatibility fields retained until all callers use normalized references.
    connector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect: Mapped[str] = mapped_column(String(20), default="block")
    priority: Mapped[int] = mapped_column(
        Integer,
        default=100,
        server_default="100",
    )
    conditions: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    policy_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )
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

    normalized_connector: Mapped[ConnectorRecord | None] = relationship(
        foreign_keys=[connector_id],
    )
    normalized_action: Mapped[ConnectorActionRecord | None] = relationship(
        foreign_keys=[action_id],
    )
    normalized_resource: Mapped[ConnectorResourceRecord | None] = relationship(
        foreign_keys=[resource_id],
    )
    app_assignments: Mapped[list[AppPolicyAssignmentRecord]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
    )
    global_assignment: Mapped[GlobalPolicyAssignmentRecord | None] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AppPolicyAssignmentRecord(Base):
    """Apply one reusable policy to one client app."""

    __tablename__ = "app_policy_assignments"
    __table_args__ = (
        UniqueConstraint(
            "app_id",
            "policy_id",
            name="uq_app_policy_assignments_app_id_policy_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"),
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
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

    app: Mapped[AppRecord] = relationship(back_populates="policy_assignments")
    policy: Mapped[PolicyRecord] = relationship(back_populates="app_assignments")


class GlobalPolicyAssignmentRecord(Base):
    """Apply one mandatory policy to every client app."""

    __tablename__ = "global_policy_assignments"
    __table_args__ = (
        UniqueConstraint(
            "policy_id",
            name="uq_global_policy_assignments_policy_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"),
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
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

    policy: Mapped[PolicyRecord] = relationship(
        back_populates="global_assignment",
    )


class ConversationMessageRecord(Base):
    """Persist one runtime conversation turn for one client app."""

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(
        ForeignKey("apps.id", ondelete="CASCADE"),
        index=True,
    )
    conversation_id: Mapped[str] = mapped_column(String(200), index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    app: Mapped[AppRecord] = relationship(back_populates="conversation_messages")


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

    expected_tool_links: Mapped[list[AllowedTestCaseExpectedToolRecord]] = relationship(
        back_populates="allowed_test_case",
        cascade="all, delete-orphan",
    )

    @property
    def normalized_expected_tools(self) -> list[str]:
        """Return unique expected tool names from normalized mappings."""

        return sorted(
            {
                link.connector_tool_mapping.tool_name
                for link in self.expected_tool_links
                if link.connector_tool_mapping
            }
        )


class AllowedTestCaseExpectedToolRecord(Base):
    """Map one allowed test case to one expected tool mapping."""

    __tablename__ = "allowed_test_case_expected_tools"
    __table_args__ = (
        UniqueConstraint(
            "allowed_test_case_id",
            "connector_tool_mapping_id",
            name="uq_allowed_test_case_expected_tools_case_connector_tool",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    allowed_test_case_id: Mapped[int] = mapped_column(
        ForeignKey("allowed_test_cases.id", ondelete="CASCADE"),
        index=True,
    )
    connector_tool_mapping_id: Mapped[int] = mapped_column(
        ForeignKey("connector_tool_mappings.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    allowed_test_case: Mapped[AllowedTestCaseRecord] = relationship(
        back_populates="expected_tool_links",
    )
    connector_tool_mapping: Mapped[ConnectorToolMappingRecord] = relationship()


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
    policy_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )
    stale: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
    )
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
