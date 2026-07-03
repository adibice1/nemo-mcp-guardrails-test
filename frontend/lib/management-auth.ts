import {
  type ManagementSession,
  type ManagementUser
} from "@/lib/api-client";


const SESSION_KEY = "gms:management-session";


export function saveManagementSession(
  session: ManagementSession,
  remember: boolean
) {
  if (typeof window === "undefined") return;

  clearManagementSession();
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(SESSION_KEY, JSON.stringify(session));
}


export function loadManagementSession(): ManagementSession | null {
  if (typeof window === "undefined") return null;

  for (const storage of [window.sessionStorage, window.localStorage]) {
    const value = storage.getItem(SESSION_KEY);
    if (!value) continue;
    try {
      return JSON.parse(value) as ManagementSession;
    } catch {
      storage.removeItem(SESSION_KEY);
    }
  }
  return null;
}


export function clearManagementSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_KEY);
  window.sessionStorage.removeItem(SESSION_KEY);
}


export function updateStoredManagementUser(user: ManagementUser) {
  if (typeof window === "undefined") return;

  for (const storage of [window.sessionStorage, window.localStorage]) {
    const value = storage.getItem(SESSION_KEY);
    if (!value) continue;
    try {
      const session = JSON.parse(value) as ManagementSession;
      storage.setItem(SESSION_KEY, JSON.stringify({ ...session, user }));
    } catch {
      storage.removeItem(SESSION_KEY);
    }
  }
}
