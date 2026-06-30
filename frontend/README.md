# GMS Frontend

Next.js 13 frontend prototype for the Guardrails Management System.

## Current Scope

This first UI slice recreates the uploaded Figma screens:

- `/login`
- `/signup`
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

Current frontend behavior:

- The selected app is persisted in `localStorage`, so returning from Settings
  keeps the last policy view.
- New mock policies use the current browser time.
- Custom resource is optional; policy name is required.
- Modal dropdowns are custom scrollable menus so larger connector/action/resource
  lists fit later.
- The frontend connector selector is intentionally limited to GitHub and
  SharePoint for the current demo scope. Policy rows display a GitHub brand icon
  or a Microsoft/SharePoint-colored connector mark instead of a generic folder.
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
leaving the reusable definition available to other apps. Assignment-safe Edit
is the next frontend slice.

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
