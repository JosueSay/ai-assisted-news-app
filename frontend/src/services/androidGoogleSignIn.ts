import type { Auth } from "@firebase/auth";

// Metro replaces this file with .android.ts only for an Android bundle.
export const isAndroidGoogleConfigured = false;

export async function signInWithAndroidGoogle(_auth: Auth): Promise<boolean> {
  throw new Error("Google nativo Android no está disponible en esta plataforma.");
}

export async function clearAndroidGoogleSession(): Promise<void> {}
