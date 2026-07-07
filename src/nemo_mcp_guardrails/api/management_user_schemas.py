from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ManagementSystemRole = Literal["developer", "admin"]
AppUserRole = Literal["admin"]


class ManagedUserRead(BaseModel):
    """Response body for one admin-managed GMS user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    username: str
    system_role: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ManagedUserCreate(BaseModel):
    """Request body for admin-created GMS users."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "developer@example.com",
                "name": "Developer User",
                "username": "developer@example.com",
                "system_role": "developer",
                "enabled": True,
            }
        },
    )

    email: str = Field(min_length=3, max_length=320)
    name: str | None = Field(default=None, max_length=320)
    username: str | None = Field(default=None, max_length=320)
    system_role: ManagementSystemRole = "developer"
    enabled: bool = True


class ManagedUserCreateRead(ManagedUserRead):
    """Response body for user creation with one-time password display."""

    temporary_password: str
    temporary_password_notice: str


class ManagedUserUpdate(BaseModel):
    """Request body for admin-updating a GMS user."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Updated Developer",
                "username": "updated.developer",
                "system_role": "developer",
                "enabled": True,
            }
        },
    )

    name: str | None = Field(default=None, min_length=1, max_length=320)
    username: str | None = Field(default=None, min_length=1, max_length=320)
    system_role: ManagementSystemRole | None = None
    enabled: bool | None = None


class ManagedUserPasswordResetRead(BaseModel):
    """Response body for one admin-generated temporary password."""

    user_id: int
    email: str
    temporary_password: str
    temporary_password_notice: str


class UserAppLinkCreate(BaseModel):
    """Request body for linking one user to one app."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "client_id": "test-app",
                "role": "admin",
            }
        },
    )

    app_id: int | None = None
    client_id: str | None = Field(default=None, max_length=100)
    role: AppUserRole = "admin"

    @model_validator(mode="after")
    def require_app_reference(self) -> "UserAppLinkCreate":
        """Require exactly one app identifier."""

        if self.app_id is None and self.client_id is None:
            raise ValueError("Provide app_id or client_id")
        if self.app_id is not None and self.client_id is not None:
            raise ValueError("Provide only one of app_id or client_id")
        return self


class UserAppLinkRead(BaseModel):
    """Response body for one user/app role assignment."""

    id: int
    user_id: int
    user_email: str
    app_id: int
    app_name: str
    client_id: str
    role: str
    created_at: datetime
    updated_at: datetime
