# GMS Frontend

Next.js 13 frontend prototype for the Guardrails Management System.

## Current Scope

This first UI slice recreates the uploaded Figma screens with local mock data:

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
- Policy rows default to newest-created first and can sort by `Created` or
  `Global`.
- Policy pagination uses 8 rows per page.
- Settings placeholder toggles are interactive, and Save Changes enables only
  after a setting is changed.

The current implementation is intentionally not wired to the FastAPI backend
yet. Backend wiring should use `docs/frontend-api-map.md`.

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
