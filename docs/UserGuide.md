# Guardrails Management System — User Guide

Maintained by: GMS project maintainers  
Last reviewed: 23 October 2026  
Companion document: [Developer Guide](DeveloperGuide.md)

This guide follows the organisation of the [SE-EDU AddressBook Level 4 User Guide](https://se-education.org/addressbook-level4/UserGuide.html), adapted to a browser application. Its instructions describe the current repository. The fresh online database/admin are initialized, but the second public Azure deployment is still pending; see the [actual work execution record](workday-online-execution-2026-10-23.md) for status and the recorded title-specific input-classifier finding. The public website continues using its existing deployment until the supervisor performs cutover.

## Contents

- [1. Introduction](#1-introduction)
- [2. Quick Start](#2-quick-start)
- [3. Features](#3-features)
  - [3.1. Signing in and setting your password](#31-signing-in-and-setting-your-password)
  - [3.2. Updating your account and signing out](#32-updating-your-account-and-signing-out)
  - [3.3. Managing users](#33-managing-users)
  - [3.4. Giving a developer access to an app](#34-giving-a-developer-access-to-an-app)
  - [3.5. Creating and finding apps](#35-creating-and-finding-apps)
  - [3.6. Updating an app and its API key](#36-updating-an-app-and-its-api-key)
  - [3.7. Connecting GitHub](#37-connecting-github)
  - [3.8. Adding your main-agent model](#38-adding-your-main-agent-model)
  - [3.9. Approving models and choosing a classifier](#39-approving-models-and-choosing-a-classifier)
  - [3.10. Creating input policies](#310-creating-input-policies)
  - [3.11. Creating output policies](#311-creating-output-policies)
  - [3.12. Drafting policies with AI](#312-drafting-policies-with-ai)
  - [3.13. Viewing, editing and removing policies](#313-viewing-editing-and-removing-policies)
  - [3.14. Running a guarded request](#314-running-a-guarded-request)
  - [3.15. Reading Traffic and Audit Logs](#315-reading-traffic-and-audit-logs)
  - [3.16. Saving data and understanding limitations](#316-saving-data-and-understanding-limitations)
- [4. FAQ](#4-faq)
- [5. Command Summary — browser actions](#5-command-summary--browser-actions)

## 1. Introduction

The Guardrails Management System (GMS) lets administrators and linked app developers configure policies for applications that use an AI agent. GMS receives a request, checks input policies, runs the agent with guarded connector tools, checks the assistant's output and returns the permitted response.

An **app** is a client application consuming GMS. A **connector** is an external integration used by that app. GitHub MCP is the currently executable connector; SharePoint and Outlook are future integrations.

Two model roles are separate:

- The **main agent** interprets the request, calls tools and writes an answer.
- The **guardrail classifier** checks requests and responses against policy rules.

Global policies apply to every app. An app's own assignments add policies; they cannot override a global restriction.

### Access at a glance

| Task | System admin | Developer linked to the app |
| --- | --- | --- |
| View apps | All apps | Linked apps |
| Create an app | Yes | No |
| Rename/delete an accessible app; regenerate its key | Yes | Yes |
| Create/manage users and their app links | Yes | No |
| Provision a connector link or change its credential reference | Yes | No |
| Enable, disable or unlink an existing connector link | Yes | Yes |
| Register an app-owned main model with a provider key | Yes | Yes |
| Choose an available main model | Yes | Yes |
| Manage explicit model approvals and classifier selections | Yes | No |
| Manage policies assigned to the app | Yes | Yes |
| Change global policies | Yes | No |
| View Traffic/Audit Logs | Yes | No |

Permissions are checked by the backend as well as the interface. A GMS system admin does not automatically have Azure or PostgreSQL administration access.

## 2. Quick Start

**Prerequisites:** a running GMS service, an account issued by its administrator and a supported modern browser. You do not need Python, Node.js or direct database access to use the deployed interface.

1. Open the GMS address supplied by your administrator and go to `/login`. The currently recorded deployment address is `http://guardrails-fe.southeastasia.azurecontainer.io`. It uses HTTP; follow the deployment owner's access arrangements when entering credentials. Encrypted database storage does not protect HTTP traffic in transit.
2. Sign in with your issued **email** and temporary password. Public self-registration is disabled.
3. Complete the password setup page and sign in again using your new password. Temporary passwords expire after 24 hours.
4. Open **Apps**. Developers see only apps linked to them. An empty list may mean that your administrator has not linked an app yet.
5. Open your app. Its tabs are **Overview**, **Connectors**, **Models**, **Policies** and **Runtime Test**.
6. Have an administrator provision GitHub access and approve the app's classifier. Add/select a main model or use an already approved main model. Both roles must be available before runtime can start.
7. In **Runtime Test**, enter the app's API key, use a new conversation ID and submit a safe read request, for example:

   ```text
   List the existing branches in OWNER/REPOSITORY using the GitHub list_branches tool. Do not create or modify anything.
   ```

   Replace `OWNER/REPOSITORY` with a repository accessible to the configured GitHub credential.
8. Inspect the response and stage indicators. Ask an administrator to verify the actual tool events in **Logs** when checking connector execution.

For a completely fresh installation, the operator must initialize the platform and first admin before these steps. The [Developer Guide](DeveloperGuide.md#13-initialising-a-fresh-database) covers that process.

## 3. Features

**How to read the instructions:** **bold text** identifies controls or fields. `Apps → APP → Models` means open Apps, select the required app and select its Models tab. Example names and URLs are illustrative. Use your own approved values; never paste real credentials into a policy description, conversation or support report.

### 3.1. Signing in and setting your password

**Access:** all issued accounts. **Location:** `/login`.

1. Enter your email and password and select the sign-in control.
2. If prompted to replace a temporary password, enter the current temporary password and a new personal password.
3. Submit the change. GMS ends the setup session and returns you to Login.
4. Sign in with the replacement password.

New passwords must be 15–256 characters, must not be all whitespace and must differ from the current password. Before setup completes, normal management actions are unavailable. If the temporary password has expired or you have forgotten your password, ask an administrator to issue a replacement; there is no public email-reset workflow.

Password changes and administrator resets invalidate earlier management sessions. Repeated attempts can be rate limited; wait for the indicated retry period.

### 3.2. Updating your account and signing out

**Access:** signed-in users. **Location:** **Settings**.

1. Edit **Name** or **Username** and save your changes. Email is read-only.
2. Use **Change password** to provide your current password and a new password. After a successful change, sign in again.
3. Use **Dark Mode** for the browser's appearance preference.
4. Select **Logout** when finished, especially on a shared computer.

Do not select Remember Me on a shared device. Signing out clears the stored frontend session; closing a tab alone is not a substitute when a persistent session was chosen.

### 3.3. Managing users

**Access:** system admins. **Location:** **User Management**.

To create an account:

1. Select **Create User**.
2. Enter the user's email, name and username; choose **Developer** or **Admin**.
3. Submit the form and copy the generated temporary password before dismissing its notice.
4. Deliver the password privately. It is shown once, expires in 24 hours and requires replacement at first login.

Open a user row to manage their role, enabled/blocked status and app links. Use the password-reset action to issue a replacement temporary password. Resetting a password invalidates that user's earlier sessions.

Deleting a user removes their account and app links. Review the confirmation before proceeding. An administrator cannot delete their own current account. Use a developer account for people who only need to manage assigned apps.

### 3.4. Giving a developer access to an app

**Access:** system admins. **Location:** **User Management → USER → App Links**.

1. Choose an existing app.
2. Select **Link**. The user receives developer access to that app.
3. Ask the user to refresh their Apps page.

Use the unlink control beside an app link to remove access. Linking a user does not approve models, enable connectors or disclose the app's API key. Assign only the apps that user needs.

### 3.5. Creating and finding apps

**Access:** admins create apps; linked developers and admins find/open accessible apps. **Location:** **Apps**.

1. As an admin, select **Create App** and enter an **Application Name**, such as `Research Assistant`.
2. Submit the form. GMS generates the client ID and an app API key.
3. Copy the API key before closing the notice and store it privately for the consuming application's backend.
4. Open the new app and configure its connector, models and policy assignments.

Use **Search applications** and the page controls to find an app. Open its row to view its details. A newly created app is not automatically ready to run: its default model selections still need appropriate approvals and its GitHub connector must be linked.

The app-list delete action removes the app and its associated application data. Use it only when that app is no longer required; changing a label or model does not require deleting the app.

### 3.6. Updating an app and its API key

**Access:** admins and linked developers. **Location:** **Apps → APP → Overview**.

To rename the app, change **Application Name** and select **Save Changes**. The displayed **Client ID** is read-only in this screen.

To replace a lost or exposed key:

1. Select **Regenerate Key** and confirm the replacement.
2. Copy the newly displayed key before leaving the page.
3. Update the consuming application's private backend configuration.
4. Verify its next authenticated request.

The old key stops working immediately. GMS stores a hash of the app API key, so it cannot display the old key again. Coordinate regeneration with the consuming app owner to avoid an unexpected interruption.

| Credential | Purpose | Where it belongs |
| --- | --- | --- |
| Management password/session | Sign in and manage GMS | Your login session |
| App API key | Authenticate the consuming app to GMS | Consuming app backend; Runtime Test only for controlled testing |
| Provider API key | Authenticate GMS to the selected model service | Masked model-registration form or protected backend configuration |
| Backend credential reference | Identify an already provisioned backend secret | Reference/name fields, such as `env:TEAM_GITHUB_PAT` |

These credentials are separate. A provider key or management password will not authenticate an app runtime request.

### 3.7. Connecting GitHub

**Access:** admins provision links/credentials; linked developers can manage existing links. **Location:** **Apps → APP → Connectors**.

For administrators:

1. Choose **GitHub**.
2. Enter a **Credential Reference**, for example `env:GITHUB_PERSONAL_ACCESS_TOKEN`, or leave it blank to use the configured default.
3. Select **Link Connector**.
4. Confirm the link is enabled and the underlying GitHub connector is available.

The field accepts a reference to a credential already provisioned and approved on the backend. Entering `env:TEAM_GITHUB_PAT` does not create that variable or grant its token access to a repository. Ask the deployment operator to provision it privately first.

Developers can toggle **Enabled/Disabled** or unlink an existing connector. They cannot provision a replacement link or change its credential reference. If a developer unlinks it, an admin must recreate it.

Normal verification uses GitHub MCP read-only mode. A policy screen does not enable GitHub writes, and a connector's read-only refusal is different from evidence that a GMS policy blocked an action.

### 3.8. Adding your main-agent model

**Access:** admins and linked developers. **Location:** **Apps → APP → Models → Add model profile**.

The form starts with the same **API Type** choice for both roles:

| API Type | Model identifier | Endpoint field |
| --- | --- | --- |
| Azure OpenAI | Exact Azure **Deployment Name** | **Azure Endpoint**, such as `https://example.openai.azure.com` |
| Compatible API / Model Gateway | Exact **Model / Gateway Alias** | **API Base URL**, such as `https://models.example.com/v1` |

1. Choose the API type.
2. Enter a unique **Profile Name**, the model/deployment identifier and endpoint.
3. Enter the service's actual key in **Provider API key**.
4. Select **Add model profile**.
5. Review the new main-agent selection, then select **Save model selections** to activate it.

**Expected result:** the new profile receives main-agent access for this app automatically. It needs no individual admin approval, but its destination must already be allowed by backend configuration. It cannot serve another app or act as a classifier.

GMS encrypts the submitted provider key and does not return it after saving. The form clears its key field after submission; re-enter it if a failed submission needs retrying. The system's encryption key is maintained separately by the deployment owner.

Use an already running, approved service. This form does not download a model, start Ollama or deploy a gateway. Azure API version is configured on the backend. For full recipes, see the [supported-model setup guide](supported-llm-setup-guide.md).

**A saved profile is not proof of model suitability.** Verify real tool calling and correct use of tool results with a fresh conversation. Existing grants and an available classifier remain necessary.

### 3.9. Approving models and choosing a classifier

**Access:** system admins. **Location:** **Apps → APP → Models**.

To use an already provisioned backend credential:

1. Open **Add model profile** and choose its **API Type**.
2. Expand **Advanced credentials** and select **Use a backend-managed credential**.
3. Enter the profile/model fields and **Credential Environment Variable**. Enter only the variable name, such as `TEAM_MODEL_KEY`; do not enter its value or the `env:` prefix in this field.
4. For Azure only, leaving the endpoint/key-variable fields blank uses the configured Azure defaults. Compatible profiles require the explicit approved API base URL and key-variable name.
5. Create the profile. Under **Approve model access for this app**, choose it and the required purpose, then select **Approve access**.
6. Choose the approved profile in **Main agent** or **Guardrail classifier**, then select **Save model selections**.

The main-agent and classifier approvals are separate, including for **Azure environment default**. A profile's presence in the catalogue does not approve it for every app. Developer-created app-owned profiles remain main-only even for admins.

**Revoke access** disables the selected approval without automatically choosing a replacement. If the revoked profile is currently selected, future runtime setup is unavailable until an approved configuration is selected. An already admitted request may finish.

Developers can select their available main-agent models. Their classifier selector is read-only, and admin approval/Advanced credentials controls are unavailable.

### 3.10. Creating input policies

**Access:** linked developers for their apps; admins for apps and global scope. **Location:** **Policies** or **Apps → APP → Policies**.

1. Choose the app scope. For an admin's global policy, choose **Global policies**; an admin creating from app scope can also select **Set Policy as Global**.
2. Open the create-policy form and choose **Input** under **Choose Rail Type**.
3. Enter **Name Policy**, such as `Block issue creation`.
4. Choose the supported **Connector**, **Action** and **Resource Type**.
5. Leave **Customise Resource** empty to block that action broadly, or enter a supported condition using the fields shown in the form's help.
6. Review the intended scope and select **Create**.

Example broad rule: GitHub + create + issue, with an empty condition. An example narrow rule for the same combination is:

```text
title = "presentation-test"
```

The narrow rule targets the supported title field, rather than every issue. Conditions are limited to the advertised fields for the selected action/resource. Quote text values; use a positive integer for supported `number` fields, for example `number = 17`.

Titles/repository names ignore case in supported comparisons; paths and branch names preserve case. A combination with no condition fields supports broad scope only. Unsupported read-block combinations and arbitrary workflows cannot be saved as executable input policies.

For pull-request branch conditions, use the branch controls for **equals**, **does not equal** and **AND**. All selected comparisons must match. PR creation can inspect its source/target arguments. **Selective merging is unavailable:** a branch-conditional merge policy can also cause nonmatching merges to be refused. Do not use it as a promise that every other merge is allowed.

The form offers supported runtime combinations. SharePoint/Outlook policies do not establish working connectors. If a related write's target cannot be established safely, GMS may refuse execution with an evaluation error rather than assert that the named policy matched.

### 3.11. Creating output policies

**Access:** linked developers for app scope; admins also manage global scope. **Location:** the create-policy form.

1. Select **Output** as the rail type.
2. Enter a policy name, such as `Do not disclose credentials`.
3. Enter a clear restriction in **Output Rule**, for example:

   ```text
   Do not reveal API keys, access tokens, passwords, environment variables or other secrets.
   ```

4. Review app/global scope and select **Create**.

Output policies inspect the assistant's answer. They do not select a connector/action/resource. A mandatory global credential-protection policy should be established by the administrator during fresh setup.

Output checks do not guarantee that the model's factual answer agrees with GitHub data. They also run after agent/tool execution, so an output block cannot undo a tool's completed operation.

### 3.12. Drafting policies with AI

**Access:** authenticated users, with existing save permissions still applied. **Location:** the create-policy form's authoring assistant.

1. Select Input or Output first.
2. Describe the restriction and select **Generate policy**, or inspect an example preview.
3. Review the proposed fields, explanation, examples and any related suggestions.
4. Apply the intended draft to the form, inspect its scope and condition, then explicitly create the policy.

Generation does not save or assign a policy and does not execute GitHub tools. Example outcomes are illustrations, not completed tests. Built-in example previews can be loaded without a new live model call; edited descriptions use live generation.

If the request is ambiguous or unsupported, the assistant can ask for clarification without producing a draft. Do not remove an important condition merely to make a suggestion save successfully. AI authoring uses its own backend configuration, defaulting to Azure; switching an app's main model does not switch the authoring service.

### 3.13. Viewing, editing and removing policies

**Location:** **Policies**, with the required app/global scope selected.

- Open a row to inspect the policy summary. Use search and page controls to locate the intended assignment.
- Use **Edit**, review its name, rail and restriction, and select **Save Changes**. Closing without saving leaves the assignment unchanged.
- Use the delete action and confirm to remove the assignment from that scope.

GMS can reuse equivalent policy definitions across apps. Editing an app assignment changes that assignment's resolved behaviour without silently changing another app's policy. Removing an app assignment does not delete a global assignment or a policy still used elsewhere. Global changes remain administrator-only.

Saved policy changes automatically refresh their compiled rules. Users do not need to edit backend files or press a separate compile control. Requests already admitted can finish with their existing policy snapshot.

### 3.14. Running a guarded request

**Access:** admins and linked developers with the app's API key. **Location:** **Apps → APP → Runtime Test**.

1. Enter **App API Key**. This is the GMS app key, not the model-provider key.
2. Set **Conversation ID**. Use a unique ID for an independent test, such as `guide-read-20261023-01`. Reuse an ID only when you intend a follow-up conversation; stored context can influence subsequent answers. Leave it blank for no server-stored conversation associated with an ID.
3. Enter a safe message naming an accessible repository.
4. Select **Run Guardrails** and inspect the response.

| Indicator | Meaning |
| --- | --- |
| Input passed | The input rail allowed this request under the loaded rules |
| Input blocked | The request was withheld before agent/tool execution |
| Tool guard passed | A guarded tool invocation passed the execution check; inspect events to confirm the tool and completion |
| Tool guard not run | No guarded tool invocation occurred, or an earlier stage stopped execution |
| Tool guard blocked | GMS blocked a tool invocation before forwarding it |
| Tool error | Tool execution or safe evaluation failed; it is not automatically a matched policy |
| Output passed | The final response passed the configured output checks |
| Output blocked | The final response was withheld; earlier tool actions are not rolled back |
| Blocked (Azure) | Azure filtering caused a block; inspect the reported source rather than treating it as a completed NeMo decision |

The result also displays the block reason/policy when available, loaded policy counts and history usage. **Guarded tool types** is a restriction summary, not a count of executed tools. All green stages do not certify the answer's factual accuracy or a complete tool call/result trace.

A policy-test prompt must be chosen for the actual effective policy. Keep normal tests read-only. To verify a write restriction safely, use a request that should be stopped at input and have an admin confirm zero tool starts. Full execution-level write testing needs a separate controlled repository and approval.

### 3.15. Reading Traffic and Audit Logs

**Access:** system admins. **Location:** **Logs**.

**Traffic Logs** show runtime requests. Filter by app/outcome, refresh and use the previous/next controls. Open a request to inspect its ID, HTTP status, UTC timestamps, duration, available input/final response and ordered execution events.

For a real GitHub read, look for `tool.started` and `tool.returned` with the expected tool, for example `list_branches`. A returned event records control returning; it does not independently prove correct tool arguments, nonempty data or a faithful summary. Verify the expected answer separately. A blocked input request should have no tool-start events.

**Audit Logs** show management mutations such as user creation, model registration, app updates and key regeneration. Filter by entity/outcome. Successful audit metadata shows the action succeeded; it does not reveal the generated secret or prove later model quality.

Audit entries omit request bodies, passwords, keys and raw tool arguments/results. Traffic may contain the user prompt and final response when captured; access and retention are deployment responsibilities. Avoid putting secrets into test prompts. Historical records may lack content or newer events; an absent field is not evidence of a successful check.

### 3.16. Saving data and understanding limitations

Form changes take effect after their explicit create/save action succeeds. Merely selecting a different model or applying an AI draft to an unsaved form does not activate it. Persistent app, user, policy and conversation records are held in PostgreSQL. Appearance preferences and login-session state are browser-side.

Backups and recovery are performed by the operator. Keep the database backup and matching model-encryption key under separate protected custody. Copying a guide or reinstalling a browser does not transfer the database. App keys cannot be recovered from their stored hashes.

Current limitations include GitHub-only runtime integration, no selective branch-merge guarantee, no automatic key-rotation/re-encryption workflow and role-specific model acceptance. A model recipe in the setup guide does not imply that every model has been tested. SharePoint, Outlook and automated deployment are not completed features of this release.

## 4. FAQ

**Why is my Apps list empty?**  
Ask an administrator to link your account to an app. A fresh database intentionally contains no old demo apps or developer links.

**Why is the classifier disabled for my developer account?**  
Classifiers and explicit model approvals are admin-managed. You can register and select a main model for your linked app.

**Why did registration work but runtime fail?**  
Check that you saved the selection, both model roles have valid access, the connector is enabled and the provider is reachable with the configured key/model ID. Registration does not make a remote model exist or test its tool calling. Give the administrator the request ID and sanitized error.

**What does “Current selection unavailable” mean?**  
The stored choice is no longer among valid approved options. An admin may need to restore its approval/configuration or choose an available replacement.

**What is the difference between API key and backend credential?**  
Provider API key mode accepts the secret itself for an encrypted, app-owned main profile. Admin Advanced credentials points to a secret already provisioned on the backend and requires explicit per-app/purpose approval.

**Can I use any model in the supported-model guide?**  
Use a model served through the documented Azure/compatible API contract or an approved gateway. It still needs the correct endpoint, model ID, credential and tests for its intended role. Native/specialist integrations marked as additional work are not enabled by profile creation.

**Why was the answer wrong even though all rails passed?**  
Rails check the configured restrictions. They do not certify factual grounding. Check tool events and the expected result. Retry an independent test with a new conversation ID; a successful retry alone does not establish the original root cause.

**Why does HTTP 200 contain a blocked result?**  
The request can complete successfully as a policy decision. Read the response's execution status and block fields as well as its HTTP status.

**What should I do for 401, 403, 429, 503 or 504?**  
For 401, check the relevant management session or app credentials. For 403, complete password setup or ask for the required permission. For 429, wait for the retry period. For 503, ask the operator to check target configuration, grants, credentials, policy loading and dependencies. For 504, report the request ID; do not blindly retry a potentially mutating operation. Never include authorization headers or secret values in support screenshots.

**Can I access GMS from home without direct SQL access?**  
Yes, if the deployed website is reachable and its backend can reach PostgreSQL. A laptop-to-database timeout and an application login problem have different diagnostic paths. Ordinary users do not need DBeaver.

**How do I report a problem?**  
Send the supervisor/administrator the page, UTC time, app identity, request ID, expected behaviour and sanitized error. Do not send API keys, passwords, bearer tokens, full environment files or database dumps through an ordinary bug report.

## 5. Command Summary — browser actions

GMS is operated through browser controls rather than AddressBook-style commands.

| Goal | Route/action | Access | Result |
| --- | --- | --- | --- |
| Sign in | Login → email/password | Issued account | Management session or required password setup |
| Change own password | Settings → Change password | Signed-in user | Password changed; sign in again |
| Create/reset account | User Management | Admin | Temporary password shown once |
| Give app access | User Details → App Links → Link | Admin | Developer sees that app |
| Create app | Apps → Create App | Admin | Client ID/key generated |
| Rename app | Overview → Save Changes | Admin/linked developer | Stored name updated |
| Replace app key | Overview → Regenerate Key | Admin/linked developer | Previous key invalidated |
| Link GitHub | Connectors → Link Connector | Admin | Enabled app connector link |
| Add own main model | Models → Add model profile | Admin/linked developer | App-owned profile/main grant created |
| Activate model selection | Models → Save model selections | Admin/linked developer; classifier admin-only | Stored model choice updated |
| Approve a model role | Models → Approve access | Admin | Per-app/purpose approval enabled |
| Add a restriction | Policies → create form → Create | App developer; global admin-only | Assignment and compiled policy saved |
| Remove a restriction | Policies → delete assignment | Same scope permissions | That assignment removed |
| Send a test | Runtime Test → Run Guardrails | App access and app key | Guarded execution response |
| Inspect execution/mutations | Logs → Traffic Logs / Audit Logs | Admin | Recorded evidence displayed |
| Sign out | Settings → Logout | Signed-in user | Browser management session cleared |
