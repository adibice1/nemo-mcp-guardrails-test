from pydantic import BaseModel, ConfigDict, Field


class ManagementSignupRequest(BaseModel):
    """Request body for creating a developer management account."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)


class ManagementLoginRequest(BaseModel):
    """Request body for management-user login."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class ManagementUserRead(BaseModel):
    """Safe public identity for one management user."""

    id: int
    email: str
    name: str
    username: str
    system_role: str


class ManagementProfileUpdate(BaseModel):
    """Request body for changing the current user's editable profile."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=320)
    username: str = Field(min_length=1, max_length=320)


class ManagementTokenResponse(BaseModel):
    """Return a bearer token and its authenticated user identity."""

    access_token: str
    token_type: str = "bearer"
    user: ManagementUserRead
