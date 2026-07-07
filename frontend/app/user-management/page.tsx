"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Check,
  Copy,
  Link2,
  RefreshCw,
  Search,
  UserPlus,
  X
} from "lucide-react";
import { AppTopNav } from "@/components/shared/app-top-nav";
import {
  createManagedUser,
  hasApiBaseUrl,
  linkManagedUserApp,
  listApps,
  listManagedUserApps,
  listManagedUsers,
  resetManagedUserPassword,
  unlinkManagedUserApp,
  updateManagedUser,
  type ClientApp,
  type ManagedUser,
  type ManagedUserCreateResponse,
  type ManagedUserPasswordResetResponse,
  type UserAppLink
} from "@/lib/api-client";
import { formatPolicyDate } from "@/lib/utils";

type SecretDisplay = {
  email: string;
  password: string;
  notice: string;
};

const EMPTY_CREATE_FORM = {
  email: "",
  name: "",
  username: "",
  systemRole: "developer" as "developer" | "admin",
  enabled: true
};

export default function UserManagementPage() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [apps, setApps] = useState<ClientApp[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [links, setLinks] = useState<UserAppLink[]>([]);
  const [search, setSearch] = useState("");
  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);
  const [linkForm, setLinkForm] = useState({
    appId: ""
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [secret, setSecret] = useState<SecretDisplay | null>(null);
  const [copied, setCopied] = useState(false);

  const selectedUser = users.find((user) => user.id === selectedUserId) ?? null;

  const visibleUsers = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return users;
    return users.filter(
      (user) =>
        user.email.toLowerCase().includes(needle) ||
        user.name.toLowerCase().includes(needle) ||
        user.username.toLowerCase().includes(needle)
    );
  }, [search, users]);

  const linkedAppIds = useMemo(
    () => new Set(links.map((link) => link.app_id)),
    [links]
  );
  const linkableApps = apps.filter((app) => !linkedAppIds.has(app.id));

  const loadUserLinks = useCallback(async (userId: number) => {
    const nextLinks = await listManagedUserApps(userId);
    setLinks(nextLinks);
  }, []);

  const loadData = useCallback(async () => {
    if (!hasApiBaseUrl()) {
      setLoading(false);
      setError("Configure NEXT_PUBLIC_API_BASE_URL to manage users.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const [nextUsers, nextApps] = await Promise.all([
        listManagedUsers(),
        listApps()
      ]);
      setUsers(nextUsers);
      setApps(nextApps);
      const nextSelectedId = selectedUserId ?? nextUsers[0]?.id ?? null;
      setSelectedUserId(nextSelectedId);
      if (nextSelectedId !== null) {
        await loadUserLinks(nextSelectedId);
      } else {
        setLinks([]);
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not load user management data."
      );
    } finally {
      setLoading(false);
    }
  }, [loadUserLinks, selectedUserId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function handleSelectUser(user: ManagedUser) {
    setSelectedUserId(user.id);
    setSecret(null);
    setNotice("");
    setError("");
    try {
      await loadUserLinks(user.id);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not load app links."
      );
    }
  }

  async function handleCreateUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;

    setSaving(true);
    setError("");
    setNotice("");
    setSecret(null);
    try {
      const created: ManagedUserCreateResponse = await createManagedUser({
        email: createForm.email.trim(),
        name: createForm.name.trim() || null,
        username: createForm.username.trim() || null,
        system_role: createForm.systemRole,
        enabled: createForm.enabled
      });
      setUsers((current) =>
        [...current, created].sort((left, right) =>
          left.email.localeCompare(right.email)
        )
      );
      setCreateForm(EMPTY_CREATE_FORM);
      setSelectedUserId(created.id);
      setLinks([]);
      setSecret({
        email: created.email,
        password: created.temporary_password,
        notice: created.temporary_password_notice
      });
      setNotice(`${created.email} was created.`);
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : "Could not create user."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateSelected(
    values: Partial<Pick<ManagedUser, "system_role" | "enabled">>
  ) {
    if (!selectedUser) return;
    try {
      setError("");
      const updated = await updateManagedUser(selectedUser.id, values);
      setUsers((current) =>
        current.map((user) => (user.id === updated.id ? updated : user))
      );
      setNotice(`${updated.email} was updated.`);
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Could not update user."
      );
    }
  }

  async function handleResetPassword() {
    if (!selectedUser) return;
    const confirmed = window.confirm(
      `Reset the password for ${selectedUser.email}? The new temporary password will be shown once.`
    );
    if (!confirmed) return;

    try {
      setError("");
      const reset: ManagedUserPasswordResetResponse =
        await resetManagedUserPassword(selectedUser.id);
      setSecret({
        email: reset.email,
        password: reset.temporary_password,
        notice: reset.temporary_password_notice
      });
      setNotice(`Temporary password generated for ${reset.email}.`);
    } catch (resetError) {
      setError(
        resetError instanceof Error
          ? resetError.message
          : "Could not reset password."
      );
    }
  }

  async function handleLinkApp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedUser || !linkForm.appId) return;

    try {
      setError("");
      const link = await linkManagedUserApp(selectedUser.id, {
        app_id: Number(linkForm.appId),
        role: "admin"
      });
      setLinks((current) => [
        ...current.filter((item) => item.app_id !== link.app_id),
        link
      ]);
      setLinkForm({ appId: "" });
      setNotice(`${selectedUser.email} was linked to ${link.app_name}.`);
    } catch (linkError) {
      setError(
        linkError instanceof Error
          ? linkError.message
          : "Could not link app."
      );
    }
  }

  async function handleUnlinkApp(link: UserAppLink) {
    if (!selectedUser) return;
    const confirmed = window.confirm(
      `Remove ${selectedUser.email} from ${link.app_name}?`
    );
    if (!confirmed) return;

    try {
      setError("");
      await unlinkManagedUserApp(selectedUser.id, link.app_id);
      setLinks((current) => current.filter((item) => item.id !== link.id));
      setNotice(`${selectedUser.email} was removed from ${link.app_name}.`);
    } catch (unlinkError) {
      setError(
        unlinkError instanceof Error
          ? unlinkError.message
          : "Could not unlink app."
      );
    }
  }

  async function handleCopySecret() {
    if (!secret) return;
    await navigator.clipboard.writeText(secret.password);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="user-management" />
      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-12 shadow-shell transition-colors dark:bg-[#1b1e25] lg:px-20">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-normal text-gms-text lg:text-[42px]">
              User Management
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gms-muted">
              Create developer accounts, issue temporary passwords, and link
              users to the applications they can manage.
            </p>
          </div>
          <label className="relative block w-full lg:w-[405px]">
            <input
              className="h-11 w-full rounded-xl border border-gms-line bg-white px-4 pr-11 text-sm text-gms-text shadow-field outline-none placeholder:text-gms-muted dark:bg-[#252932]"
              placeholder="Search users"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <Search className="absolute right-5 top-3 h-5 w-5 text-gms-text" />
          </label>
        </div>

        <div className="mt-8 grid gap-6 xl:grid-cols-[1fr_1.1fr]">
          <div className="space-y-6">
            <form
              className="rounded-lg border border-gms-line bg-[#fbfcff] p-5 dark:bg-[#20242c]"
              onSubmit={handleCreateUser}
            >
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gms-blue-soft text-gms-blue">
                  <UserPlus className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-extrabold text-gms-text">
                    Create User
                  </h2>
                  <p className="text-xs text-gms-muted">
                    The temporary password is shown once after creation.
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <input
                  className="h-11 rounded-md border border-gms-line bg-white px-3 text-sm outline-none dark:bg-[#252932]"
                  placeholder="Email"
                  type="email"
                  value={createForm.email}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      email: event.target.value
                    }))
                  }
                />
                <input
                  className="h-11 rounded-md border border-gms-line bg-white px-3 text-sm outline-none dark:bg-[#252932]"
                  placeholder="Name"
                  value={createForm.name}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      name: event.target.value
                    }))
                  }
                />
                <input
                  className="h-11 rounded-md border border-gms-line bg-white px-3 text-sm outline-none dark:bg-[#252932]"
                  placeholder="Username"
                  value={createForm.username}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      username: event.target.value
                    }))
                  }
                />
                <select
                  className="h-11 rounded-md border border-gms-line bg-white px-3 text-sm outline-none dark:bg-[#252932]"
                  value={createForm.systemRole}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      systemRole: event.target.value as "developer" | "admin"
                    }))
                  }
                >
                  <option value="developer">Developer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm font-semibold text-gms-text">
                  <input
                    checked={createForm.enabled}
                    type="checkbox"
                    onChange={(event) =>
                      setCreateForm((current) => ({
                        ...current,
                        enabled: event.target.checked
                      }))
                    }
                  />
                  Enabled
                </label>
                <button
                  className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-4 text-sm font-semibold text-white shadow-button disabled:opacity-50"
                  disabled={!createForm.email.trim() || saving}
                  type="submit"
                >
                  <UserPlus className="h-4 w-4" />
                  Create User
                </button>
              </div>
            </form>

            <div className="space-y-3">
              {visibleUsers.map((user) => (
                <button
                  key={user.id}
                  className={`grid min-h-[64px] w-full grid-cols-[1fr_120px_100px] items-center rounded-md border px-4 text-left text-sm transition ${
                    selectedUserId === user.id
                      ? "border-gms-blue bg-gms-blue text-white"
                      : "border-gms-line bg-white text-gms-text hover:border-gms-blue dark:bg-[#20242c]"
                  }`}
                  type="button"
                  onClick={() => void handleSelectUser(user)}
                >
                  <span>
                    <span className="block font-extrabold">{user.name}</span>
                    <span
                      className={
                        selectedUserId === user.id
                          ? "text-white/80"
                          : "text-gms-muted"
                      }
                    >
                      {user.email}
                    </span>
                  </span>
                  <span className="capitalize">{user.system_role}</span>
                  <span>{user.enabled ? "Enabled" : "Blocked"}</span>
                </button>
              ))}
              {!loading && visibleUsers.length === 0 && (
                <div className="rounded-md border border-dashed border-gms-line py-12 text-center text-sm text-gms-muted">
                  No users found.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-gms-line bg-[#fbfcff] p-5 dark:bg-[#20242c]">
            {selectedUser ? (
              <>
                <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gms-blue">
                      Selected User
                    </p>
                    <h2 className="mt-1 text-2xl font-extrabold text-gms-text">
                      {selectedUser.name}
                    </h2>
                    <p className="mt-1 text-sm text-gms-muted">
                      {selectedUser.email}
                    </p>
                    <p className="mt-1 text-xs text-gms-muted">
                      Created {formatPolicyDate(selectedUser.created_at)}
                    </p>
                  </div>
                  <button
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-gms-blue px-4 text-sm font-semibold text-white shadow-button"
                    type="button"
                    onClick={() => void handleResetPassword()}
                  >
                    <RefreshCw className="h-4 w-4" />
                    Reset Password
                  </button>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <label className="text-xs font-bold uppercase text-gms-muted">
                    System Role
                    <select
                      className="mt-2 h-11 w-full rounded-md border border-gms-line bg-white px-3 text-sm normal-case text-gms-text outline-none dark:bg-[#252932]"
                      value={selectedUser.system_role}
                      onChange={(event) =>
                        void handleUpdateSelected({
                          system_role: event.target.value as
                            | "developer"
                            | "admin"
                        })
                      }
                    >
                      <option value="developer">Developer</option>
                      <option value="admin">Admin</option>
                    </select>
                  </label>
                  <label className="text-xs font-bold uppercase text-gms-muted">
                    Account Status
                    <select
                      className="mt-2 h-11 w-full rounded-md border border-gms-line bg-white px-3 text-sm normal-case text-gms-text outline-none dark:bg-[#252932]"
                      value={selectedUser.enabled ? "enabled" : "blocked"}
                      onChange={(event) =>
                        void handleUpdateSelected({
                          enabled: event.target.value === "enabled"
                        })
                      }
                    >
                      <option value="enabled">Enabled</option>
                      <option value="blocked">Blocked</option>
                    </select>
                  </label>
                </div>

                <div className="mt-8">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gms-blue-soft text-gms-blue">
                      <Link2 className="h-5 w-5" />
                    </span>
                    <div>
                      <h3 className="text-lg font-extrabold text-gms-text">
                        App Links
                      </h3>
                      <p className="text-xs text-gms-muted">
                        Assign which apps this user can manage.
                      </p>
                    </div>
                  </div>

                  <form
                    className="mt-5 grid gap-3 sm:grid-cols-[1fr_120px]"
                    onSubmit={handleLinkApp}
                  >
                    <select
                      className="h-11 rounded-md border border-gms-line bg-white px-3 text-sm outline-none dark:bg-[#252932]"
                      value={linkForm.appId}
                      onChange={(event) =>
                        setLinkForm((current) => ({
                          ...current,
                          appId: event.target.value
                        }))
                      }
                    >
                      <option value="">Choose app</option>
                      {linkableApps.map((app) => (
                        <option key={app.id} value={app.id}>
                          {app.name}
                        </option>
                      ))}
                    </select>
                    <button
                      className="h-11 rounded-md bg-gms-blue text-sm font-semibold text-white shadow-button disabled:opacity-50"
                      disabled={!linkForm.appId}
                      type="submit"
                    >
                      Link
                    </button>
                  </form>

                  <div className="mt-5 space-y-3">
                    {links.map((link) => (
                      <div
                        key={link.id}
                        className="grid min-h-[58px] grid-cols-[1fr_120px_80px] items-center rounded-md border border-gms-line bg-white px-4 text-sm text-gms-text dark:bg-[#252932]"
                      >
                        <span>
                          <span className="block font-extrabold">
                            {link.app_name}
                          </span>
                          <span className="text-gms-muted">
                            {link.client_id}
                          </span>
                        </span>
                        <span>App Developer</span>
                        <button
                          className="justify-self-end rounded-full bg-[#fff0f1] p-2 text-gms-danger"
                          type="button"
                          onClick={() => void handleUnlinkApp(link)}
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    {links.length === 0 && (
                      <div className="rounded-md border border-dashed border-gms-line py-10 text-center text-sm text-gms-muted">
                        This user is not linked to any apps yet.
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="py-24 text-center text-sm text-gms-muted">
                Select or create a user to manage app access.
              </div>
            )}
          </div>
        </div>

        {loading && <p className="mt-4 text-xs text-gms-muted">Loading users...</p>}
        {error && <p className="mt-4 text-xs font-semibold text-gms-danger">{error}</p>}
      </section>

      {secret && (
        <div className="fixed right-6 top-6 z-[80] w-full max-w-md rounded-md border border-gms-line bg-white p-5 text-sm text-gms-text shadow-modal dark:bg-[#252932]">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-extrabold">Temporary password for {secret.email}</p>
              <p className="mt-1 text-xs text-gms-muted">{secret.notice}</p>
            </div>
            <button type="button" onClick={() => setSecret(null)}>
              <X className="h-4 w-4" />
            </button>
          </div>
          <code className="mt-4 block break-all rounded-md bg-[#f5f7ff] p-3 text-xs dark:bg-[#1b1e25]">
            {secret.password}
          </code>
          <button
            className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-4 text-sm font-semibold text-white"
            type="button"
            onClick={() => void handleCopySecret()}
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied!" : "Copy Password"}
          </button>
        </div>
      )}

      {notice && (
        <div className="fixed bottom-6 right-6 z-[70] flex max-w-md items-start gap-4 rounded-md border border-[#8bc9a7] bg-white px-5 py-4 text-sm text-[#245d3b] shadow-modal dark:bg-[#252932] dark:text-[#9ee1b7]">
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice("")}>
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </main>
  );
}
