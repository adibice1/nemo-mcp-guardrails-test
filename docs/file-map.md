# Backend and Frontend File Map

Use this as the low-token debugging index: find the symptom first, then open
only the listed files. Each maintained backend and frontend file has a one-line
summary. Generated folders such as `frontend/.next/`, `node_modules/`, Python
cache files, TypeScript build metadata, and local secret files are intentionally
excluded.

## Start With The Symptom

| Symptom | Check first |
| --- | --- |
| Frontend cannot reach FastAPI | `frontend/lib/api-client.ts`, `frontend/.env.local`, `src/nemo_mcp_guardrails/api/main.py`, `scripts/run_api.py` |
| Frontend loads without styling | `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js` |
| Policies page data or state is wrong | `frontend/app/policies/page.tsx`, then `frontend/lib/api-client.ts` |
| Policy modal fields or cascading options are wrong | `frontend/components/policies/create-policy-modal.tsx`, `src/nemo_mcp_guardrails/api/policy_metadata.py` |
| Policy create/edit/delete behaves incorrectly | `frontend/app/policies/page.tsx`, `src/nemo_mcp_guardrails/api/policy_assignment_resolution.py`, `src/nemo_mcp_guardrails/policy_service.py` |
| Policies are missing, duplicated, or assigned to the wrong app | `src/nemo_mcp_guardrails/database/policy_loader.py`, `src/nemo_mcp_guardrails/policy_service.py`, `src/nemo_mcp_guardrails/api/apps.py` |
| Compiled NeMo rule is stale or incorrect | `src/nemo_mcp_guardrails/policy_rule_service.py`, `src/nemo_mcp_guardrails/policy_compiler.py`, `src/nemo_mcp_guardrails/prompt_rule_compiler.py` |
| Runtime returns an incorrect status or a 500 | `src/nemo_mcp_guardrails/api/runtime.py`, `src/nemo_mcp_guardrails/guarded_execution.py` |
| App credentials are rejected | `src/nemo_mcp_guardrails/api/auth.py`, `src/nemo_mcp_guardrails/app_auth.py` |
| MCP action is incorrectly allowed or blocked | `src/nemo_mcp_guardrails/tool_guard.py`, `src/nemo_mcp_guardrails/runtime_factory.py` |
| Output text is incorrectly allowed or blocked | `src/nemo_mcp_guardrails/output_guard.py`, `src/nemo_mcp_guardrails/guarded_execution.py`, `config/prompts.yml` |
| Conversation history is missing or too large | `src/nemo_mcp_guardrails/database/conversation_store.py`, `src/nemo_mcp_guardrails/api/runtime.py` |
| Database cannot connect | `src/nemo_mcp_guardrails/database/connection.py`, `.env`, `docker-compose.yml` |
| Docker frontend/backend is unhealthy | `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `docs/containerisation.md` |
| Apps list/detail UI is wrong | `frontend/app/apps/page.tsx`, `frontend/app/apps/[clientId]/page.tsx`, `frontend/components/apps/` |

## Backend Core

- `src/nemo_mcp_guardrails/__init__.py` - Marks `nemo_mcp_guardrails` as an importable Python package.
- `src/nemo_mcp_guardrails/app_auth.py` - Hashes app API keys and authenticates authorized client-ID/API-key pairs.
- `src/nemo_mcp_guardrails/management_auth.py` - Hashes management passwords and creates/verifies signed JWT access tokens.
- `src/nemo_mcp_guardrails/management_permissions.py` - Enforces system-admin roles and active app-developer links across management routes.
- `src/nemo_mcp_guardrails/guarded_execution.py` - Runs input rails, the agent and guarded tools, output rails, and structured Azure/GMS status handling.
- `src/nemo_mcp_guardrails/output_guard.py` - Applies deterministic checks for explicit restricted phrases in generated output.
- `src/nemo_mcp_guardrails/policy_compiler.py` - Converts structured input/output policy objects into NeMo rules, tool restrictions, and generated tests.
- `src/nemo_mcp_guardrails/policy_rule_service.py` - Creates and refreshes persisted `compiled_policy_rules` rows from policy definitions.
- `src/nemo_mcp_guardrails/policy_service.py` - Canonicalizes policies and resolves equivalent, reusable, or duplicate definitions.
- `src/nemo_mcp_guardrails/prompt_rule_compiler.py` - Injects app-scoped compiled DB rules into the NeMo prompt configuration.
- `src/nemo_mcp_guardrails/runtime_factory.py` - Builds app-scoped LLMs, NeMo rails, connector credentials, GitHub MCP tools, and the agent.
- `src/nemo_mcp_guardrails/tool_guard.py` - Blocks restricted MCP calls before execution, including custom-resource argument matching.
- `src/nemo_mcp_guardrails/helper/__init__.py` - Marks the helper directory as a Python package.
- `src/nemo_mcp_guardrails/helper/utility.py` - Reserved helper module; it currently contains no implementation.

## Backend API

- `src/nemo_mcp_guardrails/api/__init__.py` - Marks the FastAPI module directory as a Python package.
- `src/nemo_mcp_guardrails/api/main.py` - Creates FastAPI, configures CORS/lifespan, mounts routers, and exposes health endpoints.
- `src/nemo_mcp_guardrails/api/auth.py` - Reads runtime auth headers and rejects invalid app credentials before runtime work.
- `src/nemo_mcp_guardrails/api/management_auth.py` - Implements management signup, login, current-user identity, and bearer-token validation.
- `src/nemo_mcp_guardrails/api/management_auth_schemas.py` - Defines management authentication request, user, and token response schemas.
- `src/nemo_mcp_guardrails/api/runtime.py` - Implements authenticated auth-check/run endpoints, history trimming/storage, and runtime response assembly.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py` - Defines runtime conversation, request, and response Pydantic models.
- `src/nemo_mcp_guardrails/api/llm_configs.py` - Lists and creates Azure LLM configuration metadata without exposing credential references.
- `src/nemo_mcp_guardrails/api/policies.py` - Implements reusable policy CRUD, compile preview, and compiled-rule refresh endpoints.
- `src/nemo_mcp_guardrails/api/policy_schemas.py` - Defines policy, assignment-resolution, metadata, test-case, and compile-response schemas.
- `src/nemo_mcp_guardrails/api/policy_metadata.py` - Returns valid connector/action/resource combinations for cascading policy dropdowns.
- `src/nemo_mcp_guardrails/api/policy_assignment_resolution.py` - Implements duplicate-aware assignment creation and assignment-safe policy edits.
- `src/nemo_mcp_guardrails/api/apps.py` - Implements app, app-connector, app-policy, and effective-policy CRUD by ID or client ID.
- `src/nemo_mcp_guardrails/api/app_schemas.py` - Defines app, connector-link, LLM-selection, and app-assignment request/response schemas.
- `src/nemo_mcp_guardrails/api/assignment_serializers.py` - Adds readable app/policy labels to assignment API responses.
- `src/nemo_mcp_guardrails/api/global_policy_assignments.py` - Implements single and bulk global-policy assignment CRUD.
- `src/nemo_mcp_guardrails/api/allowed_test_cases.py` - Implements CRUD for DB-backed prompts that are expected to pass guardrails.

## Backend Database

- `src/nemo_mcp_guardrails/database/__init__.py` - Marks the database directory as a Python package.
- `src/nemo_mcp_guardrails/database/connection.py` - Creates the SQLAlchemy engine/session and provides DB health/table helpers.
- `src/nemo_mcp_guardrails/database/models.py` - Defines every SQLAlchemy ORM table and relationship.
- `src/nemo_mcp_guardrails/database/conversation_store.py` - Loads and appends app-scoped conversation turns in Postgres.
- `src/nemo_mcp_guardrails/database/policy_loader.py` - Loads enabled global/app policies and converts rows into compiler objects.
- `src/nemo_mcp_guardrails/database/prompt_rule_loader.py` - Loads enabled compiled NeMo rules with optional app assignment scope.
- `src/nemo_mcp_guardrails/database/test_case_loader.py` - Loads allowed test cases and falls back to default read tests when none exist.

## Frontend Routes

- `frontend/app/layout.tsx` - Defines the root HTML layout, global CSS import, metadata, and saved-theme restoration.
- `frontend/app/globals.css` - Contains the shared Tailwind layers and nearly all custom GMS visual styling.
- `frontend/app/page.tsx` - Redirects the frontend root route to `/policies`.
- `frontend/app/login/page.tsx` - Renders the login design and its client-side form interactions.
- `frontend/app/signup/page.tsx` - Displays the admin-managed account creation notice and links back to Login.
- `frontend/app/policies/page.tsx` - Orchestrates policy loading, filtering, sorting, pagination, creation, editing, deletion, and notices.
- `frontend/app/apps/page.tsx` - Loads, creates, deletes, sorts, and paginates the user's client applications.
- `frontend/app/apps/[clientId]/page.tsx` - Loads one app and coordinates its overview, connectors, LLM, policies, and runtime tabs.
- `frontend/app/user-management/page.tsx` - Lets system admins create users, reset temporary passwords, and link users to apps.
- `frontend/app/settings/page.tsx` - Wraps the account settings form in the shared GMS navigation/layout.
- `frontend/app/api/gms/[...path]/route.ts` - Proxies same-origin frontend API requests to FastAPI using the runtime server URL.

## Frontend Components

- `frontend/components/shared/app-top-nav.tsx` - Renders the shared Apps, Policies, admin-only User Management, and Settings navigation.
- `frontend/components/shared/auth-illustration.tsx` - Renders the decorative login/signup illustration.
- `frontend/components/shared/form-field.tsx` - Provides the reusable labeled authentication form field.
- `frontend/components/policies/create-policy-modal.tsx` - Implements the input/output policy builder and cascading dropdown UI.
- `frontend/components/policies/policy-table.tsx` - Renders sortable policy rows, connector icons, hover actions, and pagination controls.
- `frontend/components/policies/policy-summary-modal.tsx` - Fetches and displays a readable summary of one reusable policy.
- `frontend/components/settings/settings-form.tsx` - Loads/saves the authenticated profile, handles logout, and manages local theme/toggles.
- `frontend/components/apps/app-table.tsx` - Renders the app list with navigation and row actions.
- `frontend/components/apps/create-app-modal.tsx` - Collects a new app's identity and one-time API key.
- `frontend/components/apps/create-llm-config-modal.tsx` - Collects Azure deployment metadata and an optional backend environment-variable reference.
- `frontend/components/apps/app-overview.tsx` - Displays and edits core app details.
- `frontend/components/apps/app-connectors.tsx` - Lists and manages an app's connector links and credential references.
- `frontend/components/apps/app-llm-settings.tsx` - Creates and selects named main-agent and guardrail LLM configurations for an app.
- `frontend/components/apps/app-policy-summary.tsx` - Lists the app's effective global and app-specific policy assignments.
- `frontend/components/apps/app-runtime-test.tsx` - Sends authenticated runtime requests and displays rail/tool/history results.

## Frontend Data And Configuration

- `frontend/lib/api-client.ts` - Defines frontend API types and all fetch calls to FastAPI.
- `frontend/lib/management-auth.ts` - Saves, restores, and clears prototype management sessions in browser storage.
- `frontend/lib/mock-data.ts` - Supplies fallback policies/options for static demos without a backend URL.
- `frontend/lib/utils.ts` - Provides Tailwind class merging and policy date formatting helpers.
- `frontend/next.config.js` - Configures Next.js behavior and standalone container output.
- `frontend/next-env.d.ts` - Supplies generated Next.js TypeScript declarations; do not edit manually.
- `frontend/tailwind.config.ts` - Tells Tailwind which files to scan and defines theme extensions.
- `frontend/postcss.config.js` - Connects Tailwind and Autoprefixer to the CSS build.
- `frontend/tsconfig.json` - Configures frontend TypeScript, strictness, module resolution, and path aliases.
- `frontend/package.json` - Declares frontend scripts and npm dependencies.
- `frontend/package-lock.json` - Locks exact npm dependency versions for repeatable installs.
- `frontend/.env.example` - Documents safe placeholder frontend environment variables.
- `frontend/README.md` - Explains frontend routes, behavior, local setup, and backend integration.

## Runtime Configuration And Startup

- `config/config.yml` - Enables and configures the NeMo input/output rail flows.
- `config/prompts.yml` - Holds stable self-check prompt templates that receive compiled DB rules at runtime.
- `config/rails.co` - Defines the Colang input/output flow and safe refusal behavior.
- `.env.example` - Documents backend environment variables without storing real secrets.
- `Dockerfile` - Builds the FastAPI image with Linux wheels and a pinned native GitHub MCP executable for container deployments.
- `.dockerignore` - Keeps secrets, frontend files, caches, tests and docs out of the backend image context.
- `frontend/Dockerfile` - Builds and runs the Next.js standalone production image.
- `frontend/.dockerignore` - Keeps local secrets, dependencies, build output and logs out of the frontend image context.
- `docker-compose.yml` - Runs the frontend, backend, Postgres and pgAdmin local stack with health ordering.
- `docs/containerisation.md` - Documents direct image builds, local verification, ACR publishing, and the recommended ACI layout.
- `scripts/run_api.py` - Starts the FastAPI/Uvicorn development server.
- `scripts/migrate_management_auth.py` - Adds the system-wide developer/admin role to existing user tables.
- `scripts/backfill_existing_app_users.py` - Idempotently links existing demo users to pre-RBAC apps.
- `AGENTS.md` - Stores project terminology, current architecture, safety rules, and agent handoff instructions.

## Tests, Scripts, And Deeper Explanations

- Use `docs/testing-notes.md` for test/debug scripts and their commands.
- `tests/test_management_rbac_http.py` proves admin-created apps, developer isolation, app-developer links, and system-admin overrides.
- Use `docs/policy-schema-design.md` for schema and migration details.
- Use `docs/runtime-flow-map.md` when one-line descriptions are not enough and function-level execution order is needed.
- Use `docs/troubleshooting.md` for known local setup, Postgres, DBeaver, NeMo, and GitHub MCP failures.
