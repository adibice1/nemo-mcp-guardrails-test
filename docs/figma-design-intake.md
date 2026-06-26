# Figma Design Intake

This file tracks uploaded Figma exports and user-provided flow notes before
frontend implementation begins.

The user confirmed that all images have been uploaded. Frontend implementation
can begin from this design batch.

## Uploaded Batch 1

Received on 2026-06-26.

### Login / Registration

- `Login.png`
- `Sign up page.png`

### Settings

- `Settings.png`

### Policies Flow

Images received:

- `Policy Creation 01.png`
- `Policy Creation 02.png`
- `Policy Creation 03.png`
- `Policy Creation 04.png`
- `Policy Creation 05.png`
- `Policy Creation 06.png`
- `Policy Creation 07.png`
- `Policy Creation 08.png`
- `Policy Creation 09.png`
- `Policy Creation 10.png`
- `Policy Creation 11.png`
- `Policy Creation 12.png`
- `Policy Creation 13.png`

User notes for policy creation:

1. User sees global policies before selecting a specific app.
2. User selects app to change.
3. User sees app-specific policies.
4. User sees create-policy popup after clicking the create-policy button.
   Boxes are greyed out and cannot be typed/selected until the previous box is
   chosen. Red `*` means the field is compulsory. `Set Permission` is visible
   only to admins, not all users; it is present in the design for planning.
5. User chooses connector.
6. Choosing connector unlocks the action box.
7. User chooses action.
8. Action unlocks resource type.
9. User chooses resource type.
10. Resource type unlocks custom resource box.
11. User types custom resource.
12. User names policy.
13. New policy shifts to the top of the policy list.

Additional note:

- In the policy list, a blue row means the mouse is hovering over that row. It
  does not mean the first entry is selected by default.

## Follow-Up UI Fixes

Implemented after local preview:

- The app selector label stays as `APPS`; the selected app name appears only in
  the dropdown value.
- Modal dropdowns use scrollable custom menus for larger future lists.
- Created mock policies use the current browser time.
- Custom resource is optional. Policy name unlocks after resource type is
  selected, and policy creation only requires connector, action, resource type,
  and policy name.
- Settings placeholder toggles are interactive and can be saved.
- Returning from Settings keeps the last selected app policy view.
- Policy pagination uses 8 rows per page and shows real page/count metadata.
- Policy table sorts by newest created time by default and supports created/global
  sorting.
- The visible navigation tab was renamed from `Policy Creation` to `Policies`.
