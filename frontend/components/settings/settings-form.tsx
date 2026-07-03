"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getCurrentManagementUser,
  updateCurrentManagementUser
} from "@/lib/api-client";
import {
  clearManagementSession,
  loadManagementSession,
  updateStoredManagementUser
} from "@/lib/management-auth";
import { cn } from "@/lib/utils";

type SettingsState = {
  darkMode: boolean;
  placeholderOne: boolean;
  placeholderTwo: boolean;
  placeholderThree: boolean;
};

type ProfileState = {
  name: string;
  username: string;
  email: string;
};

const initialSettings: SettingsState = {
  darkMode: false,
  placeholderOne: true,
  placeholderTwo: true,
  placeholderThree: true
};

const initialProfile: ProfileState = {
  name: "",
  username: "",
  email: ""
};

export function SettingsForm() {
  const router = useRouter();
  const [settings, setSettings] = useState<SettingsState>(initialSettings);
  const [profile, setProfile] = useState<ProfileState>(initialProfile);
  const [accessToken, setAccessToken] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const darkMode = window.localStorage.getItem("gms:theme") === "dark";
    setSettings((current) => ({ ...current, darkMode }));
    document.documentElement.classList.toggle("dark", darkMode);

    const session = loadManagementSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    setAccessToken(session.access_token);
    getCurrentManagementUser(session.access_token)
      .then((user) => {
        setProfile({
          name: user.name,
          username: user.username,
          email: user.email
        });
        updateStoredManagementUser(user);
      })
      .catch(() => {
        clearManagementSession();
        router.replace("/login");
      });
  }, [router]);

  function toggleSetting(key: keyof SettingsState) {
    setSettings((current) => ({
      ...current,
      [key]: !current[key]
    }));
    setDirty(true);
    setSaved(false);
  }

  function updateProfile(key: keyof ProfileState, value: string) {
    setProfile((current) => ({
      ...current,
      [key]: value
    }));
    setDirty(true);
    setSaved(false);
  }

  async function handleSave() {
    if (!accessToken || saving || !profile.name.trim() || !profile.username.trim()) {
      return;
    }

    setSaving(true);
    setError("");
    try {
      const user = await updateCurrentManagementUser(accessToken, {
        name: profile.name.trim(),
        username: profile.username.trim()
      });
      updateStoredManagementUser(user);
      setProfile({ name: user.name, username: user.username, email: user.email });
      window.localStorage.setItem(
        "gms:theme",
        settings.darkMode ? "dark" : "light"
      );
      setDirty(false);
      setSaved(true);
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "Could not save settings."
      );
    } finally {
      setSaving(false);
    }
  }

  function handleLogout() {
    clearManagementSession();
    router.replace("/login");
  }

  function toggleDarkMode() {
    const enabled = !settings.darkMode;
    document.documentElement.classList.toggle("dark", enabled);
    toggleSetting("darkMode");
  }

  return (
    <div className="relative min-h-[780px]">
      <button
        className={cn(
          "absolute right-0 top-0 h-12 rounded-2xl px-7 text-sm font-extrabold uppercase tracking-wide transition",
          dirty
            ? "bg-gms-blue text-white shadow-button"
            : "bg-[#dedede] text-[#777b85] dark:bg-[#30343e] dark:text-[#777f91]"
        )}
        disabled={!dirty || saving || !profile.name.trim() || !profile.username.trim()}
        type="button"
        onClick={handleSave}
      >
        {saving ? "Saving" : saved ? "Saved" : "Save Changes"}
      </button>

      <h1 className="text-[26px] font-extrabold text-gms-text">Account</h1>

      <div className="mt-9 grid gap-14 lg:grid-cols-[560px_1fr]">
        <div className="space-y-8">
          <div className="grid grid-cols-[160px_1fr] items-start gap-10">
            <span className="pt-5 text-right text-sm font-extrabold">
              Profile picture
            </span>
            <div>
              <button
                className="h-12 rounded-xl border border-[#dddddd] bg-white px-5 text-sm font-extrabold uppercase tracking-widest text-gms-blue shadow-[0_4px_0_rgba(0,0,0,0.08)] dark:border-gms-line dark:bg-[#252932]"
                type="button"
              >
                Choose File
              </button>
              <p className="mt-3 text-sm text-[#9a9a9a]">no file selected</p>
              <p className="mt-3 text-base text-[#9a9a9a]">
                maximum image size is 1 MB
              </p>
            </div>
          </div>

          <SettingsInput
            label="Name"
            value={profile.name}
            onChange={(value) => updateProfile("name", value)}
          />
          <SettingsInput
            label="Username"
            value={profile.username}
            onChange={(value) => updateProfile("username", value)}
          />
          <SettingsInput
            disabled
            label="Email"
            value={profile.email}
          />

          <div className="-mt-6 grid grid-cols-[160px_1fr] items-center gap-10">
            <span />
            <p className="whitespace-nowrap text-sm text-gms-muted">
              Email changes and verification are not available yet.
            </p>
          </div>

          {error && (
            <div className="grid grid-cols-[160px_1fr] gap-10">
              <span />
              <p className="text-sm font-semibold text-gms-danger">{error}</p>
            </div>
          )}

          <SettingsToggle
            enabled={settings.darkMode}
            label="Dark Mode"
            onToggle={toggleDarkMode}
          />
          <SettingsToggle
            enabled={settings.placeholderOne}
            label="Placeholder"
            onToggle={() => toggleSetting("placeholderOne")}
          />
          <SettingsToggle
            enabled={settings.placeholderTwo}
            label="Placeholder"
            onToggle={() => toggleSetting("placeholderTwo")}
          />
          <SettingsToggle
            enabled={settings.placeholderThree}
            label="Placeholder"
            onToggle={() => toggleSetting("placeholderThree")}
          />

          <div className="ml-[200px] space-y-8 pt-2 text-sm font-extrabold uppercase tracking-widest">
            <button
              className="block text-[#b8b8b8] hover:text-gms-blue"
              type="button"
              onClick={handleLogout}
            >
              Logout
            </button>
            <button className="block text-[#b8b8b8]" type="button">
              Export My Data
            </button>
            <button className="block text-[#ff4141]" type="button">
              Delete My Account
            </button>
          </div>
        </div>

        <div className="pt-7">
          <h2 className="text-lg font-extrabold text-gms-text">
            Profile picture
          </h2>
          <div className="mt-2 flex h-[180px] w-[180px] items-end justify-center overflow-hidden rounded-xl bg-[#ffc2d5] text-[116px]">
            <span aria-hidden="true">🙂</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingsInput({
  disabled = false,
  label,
  value,
  onChange
}: {
  disabled?: boolean;
  label: string;
  value: string;
  onChange?: (value: string) => void;
}) {
  return (
    <label className="grid grid-cols-[160px_1fr] items-center gap-10">
      <span className="text-right text-sm font-extrabold">{label}</span>
      <input
        className="h-12 max-w-[390px] rounded-2xl border border-[#dddddd] bg-[#f7f7f7] px-3 text-xl text-[#545454] outline-none disabled:cursor-not-allowed disabled:opacity-70 dark:border-gms-line dark:bg-[#252932] dark:text-gms-text"
        disabled={disabled}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
      />
    </label>
  );
}

function SettingsToggle({
  label,
  enabled,
  onToggle
}: {
  label: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="grid grid-cols-[160px_1fr] items-center gap-10">
      <span className="text-right text-sm font-extrabold">{label}</span>
      <button
        className={cn(
          "relative h-8 w-[58px] rounded-full transition",
          enabled ? "bg-gms-blue" : "bg-[#dedede] dark:bg-[#3b404b]"
        )}
        type="button"
        onClick={onToggle}
      >
        <span
          className={cn(
            "absolute top-[-2px] h-9 w-9 rounded-xl border-2 bg-white transition",
            enabled
              ? "left-7 border-gms-blue"
              : "left-0 border-[#dddddd] dark:border-[#626a7a] dark:bg-[#e6e8ee]"
          )}
        />
      </button>
    </div>
  );
}
