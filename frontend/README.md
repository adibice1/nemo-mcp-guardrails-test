# GMS Frontend

Next.js 13 frontend prototype for the Guardrails Management System.

## Current Scope

This first UI slice recreates the uploaded Figma screens:

- `/login`
- `/signup`
- `/apps`
- `/apps/[clientId]`
- `/policies`
- `/settings`

The policy creation page includes the Figma interaction flow:

```text
choose connector
-> unlock action
-> unlock resource type
-> unlock custom resource and policy name
-> create policy at the top of the list
```

`/login` and `/signup` now call the real management-authentication endpoints.
Passwords are hashed with scrypt in the backend, and the frontend restores the
signed JWT identity through `/management-auth/me`. Management CRUD authorization
is the next slice; the current token does not yet restrict app/policy routes.
Settings loads that identity, keeps email read-only, saves name/username to
Postgres, and clears the stored session before Logout redirects to `/login`.

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
creates apps with one-way API-key hashing, deletes apps, and opens a dedicated
`/apps/[clientId]` management page. App details provide functional Overview,
Connectors, LLM, Policies, and Runtime Test tabs. GitHub connector management is
active; SharePoint is visibly deferred until backend/runtime support exists.
The LLM tab loads `GET /llm-configs` and presents named main-agent and guardrail
selectors without exposing connector or model credential references. It can
also create Azure deployment metadata using an optional backend environment
variable name; the browser never receives or submits the API key itself.

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
