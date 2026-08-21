# GMS Frontend

Next.js 13 frontend prototype for the Guardrails Management System.

## Current Scope

This first UI slice recreates the uploaded Figma screens:

- `/login`
- `/apps`
- `/apps/[clientId]`
- `/policies`
- `/user-management`
- `/settings`

The policy creation page includes the Figma interaction flow:

```text
choose connector
-> unlock action
-> unlock resource type
-> unlock custom resource and policy name
-> create policy at the top of the list
```

`/login` now calls the real management-authentication endpoint. Public signup is
disabled; `/signup` shows an admin-managed account notice and returns users to
Login. Passwords are hashed with scrypt in the backend, and the frontend
restores the signed JWT identity through `/management-auth/me`. Settings loads
that identity, keeps email read-only, saves name/username to Postgres, and
clears the stored session before Logout redirects to `/login`.

Current frontend behavior:

- The selected app is persisted in `localStorage`, so returning from Settings
  keeps the last policy view.
- New mock policies use the current browser time.
- Custom resource is optional; policy name is required.
- Modal dropdowns are custom scrollable menus so larger connector/action/resource
  lists fit later.
- The frontend connector selector is intentionally limited to GitHub and
  SharePoint for the current demo scope. Global policy rows use a globe icon;
  app-specific rows use a GitHub brand icon or a Microsoft/SharePoint-colored
  connector mark. Unknown legacy connectors retain the folder fallback.
- Policy rows default to newest-created first and can sort by `Created` or
  `Global`.
- Policy pagination uses 8 rows per page.
- Settings placeholder toggles are interactive, and Save Changes enables only
  after a setting is changed.
- Dark mode previews immediately from Settings and persists to `gms:theme` in
  browser `localStorage` when Save Changes is clicked. The root layout restores
  the saved theme before the app renders.

The `/policies` page has a FastAPI adapter for policy reads, duplicate-aware
creation, assignment-safe editing, and assignment-only deletion. It stays in mock mode
when no API base URL is configured, which keeps the static/Vercel design demo
usable without a backend.

To use local backend data, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then restart with `npm run dev:clean` while the FastAPI backend is running.

Current backend reads:

```text
GET /apps
GET /global-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
```

Create is backend-wired: the modal creates a reusable policy, assigns it to the
selected app or global scope, reloads the DB-backed view, and then closes.
Equivalent policy behavior is reused and produces a visible `created`,
`reused`, or `already assigned` notice. Delete removes only the assignment,
leaving the reusable definition available to other apps. Edit resolves and
switches only the selected assignment.

Clicking a policy row on either `/policies` or the app-detail Policies tab opens
the same policy-summary modal. It loads the reusable definition and displays
scope, connector, action, resource type, custom resource, effect, policy type,
and status. Edit/Delete controls stop row-click propagation and retain their
existing actions.

The `/apps` page lists real database applications, connector/policy counts,
hides app creation from non-admin users, and opens a dedicated `/apps/[clientId]`
management page. App details provide functional Overview, Connectors, LLM,
Policies, and Runtime Test tabs. GitHub connector management is active;
SharePoint is visibly deferred until backend/runtime support exists.
The LLM tab loads `GET /llm-configs` and presents named main-agent and guardrail
selectors without exposing connector or model credential references. It can
also create Azure deployment metadata using an optional backend environment
variable name; the browser never receives or submits the API key itself.

The `/user-management` page is visible only to system admins. It lists users,
creates admin-managed accounts with a one-time temporary password, resets lost
passwords, blocks/enables accounts, changes system role, and links users to
apps as app developers.

Optional custom-resource text is stored as `conditions.custom_resource`, but
the current backend compiler does not enforce that condition yet.

## Component Layout

```text
components/
  shared/
    app-top-nav.tsx
    auth-illustration.tsx
    form-field.tsx
  policies/
    create-policy-modal.tsx
    policy-table.tsx
    policy-summary-modal.tsx
  apps/
    app-table.tsx
    create-app-modal.tsx
    app-overview.tsx
    app-connectors.tsx
    app-llm-settings.tsx
    app-policy-summary.tsx
    app-runtime-test.tsx
  settings/
    settings-form.tsx
```

## Run Locally

```powershell
cd frontend
npm install
npm run dev:clean
```

Open:

```text
http://127.0.0.1:3000/policies
```

## Run In Docker

From the repository root, build and start the complete stack:

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

The containerized frontend uses `/api/gms` as its browser API base. Next.js
proxies requests to `GMS_API_BASE_URL=http://backend:8000` inside the Compose
network, so `frontend/.env.local` is not required for the containerized build.
The production image listens directly on port `80` as the non-root `nextjs`
user. Compose exposes it at `http://127.0.0.1` by default; set
`FRONTEND_PORT=3000` in the root `.env` when local host port `80` is occupied.
See `docs/containerisation.md` for health checks and the ACI network contract.

## Verify

```powershell
cd frontend
npm run build
npm audit --omit=dev
```

`npm run build` may need to run outside Codex sandboxing on Windows because
Next.js spawns worker processes during type checking.

Do not run `npm run build` while `npm run dev` is already running. Both commands
write to `.next`, and the dev server can end up pointing at a stale CSS file.
Use `npm run dev:clean` after builds or CSS cache issues.
