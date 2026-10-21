// @vitest-environment happy-dom
import * as React from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  platform: "android",
  nativeSignIn: vi.fn(), nativeSignOut: vi.fn(), popup: vi.fn(), guest: vi.fn(), logout: vi.fn(),
  prompt: vi.fn(), exchange: vi.fn(), profile: vi.fn(),
  listener: undefined as undefined | ((user: unknown) => Promise<void> | void),
}));
vi.mock("react-native", () => ({ Platform: {
  get OS() { return mocks.platform; },
  select: (values: Record<string, unknown>) => values[mocks.platform] ?? values.default,
} }));
vi.mock("expo-auth-session", () => ({
  makeRedirectUri: () => "ainews://",
  useAuthRequest: () => [{ codeVerifier: "test-verifier" }, null, mocks.prompt],
  ResponseType: { Code: "code" }, exchangeCodeAsync: mocks.exchange,
}));
vi.mock("expo-web-browser", () => ({ maybeCompleteAuthSession: vi.fn() }));
vi.mock("@firebase/auth", () => ({
  GoogleAuthProvider: class { setCustomParameters() {} },
  onAuthStateChanged: (_: unknown, callback: typeof mocks.listener) => {
    mocks.listener = callback;
    void callback?.(null);
    return vi.fn();
  },
  signInAnonymously: mocks.guest, signInWithPopup: mocks.popup,
  signInWithCredential: vi.fn(), signOut: mocks.logout,
}));
vi.mock("../src/services/firebaseClient", () => ({ firebaseAuth: {}, isFirebaseConfigured: true }));
vi.mock("../src/services/newsService", () => ({ fetchAuthenticatedProfile: mocks.profile }));
vi.mock("../src/services/androidGoogleSignIn", () => ({
  get isAndroidGoogleConfigured() { return mocks.platform === "android"; },
  signInWithAndroidGoogle: mocks.nativeSignIn,
  clearAndroidGoogleSession: mocks.nativeSignOut,
}));

import { useGoogleAuth } from "../src/services/googleAuth";
let auth: ReturnType<typeof useGoogleAuth>;
let root: Root;
function Harness() { auth = useGoogleAuth(); return null; }
async function mount() {
  await act(async () => { root.render(React.createElement(Harness)); });
}
beforeEach(() => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  vi.resetAllMocks();
  mocks.platform = "android";
  mocks.nativeSignIn.mockResolvedValue(false);
  mocks.nativeSignOut.mockResolvedValue(undefined);
  root = createRoot(document.createElement("div"));
});
afterEach(async () => {
  await act(async () => root.unmount());
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

it("Android enables native Google without the browser Client ID and handles cancellation", async () => {
  await mount();
  expect(auth.isGoogleConfigured).toBe(true);
  expect(auth.canPromptGoogle).toBe(true);
  await act(async () => auth.signInWithGoogle());
  expect(mocks.nativeSignIn).toHaveBeenCalledOnce();
  expect(mocks.prompt).not.toHaveBeenCalled();
  expect(mocks.exchange).not.toHaveBeenCalled();
  expect(mocks.popup).not.toHaveBeenCalled();
  expect(auth.isLoading).toBe(false);
  expect(auth.error).toBeNull();
});
it("surfaces a native failure and allows another attempt", async () => {
  mocks.nativeSignIn.mockRejectedValueOnce(new Error("Native configuration mismatch"));
  await mount();
  await act(async () => auth.signInWithGoogle());
  expect(auth.error).toBe("Native configuration mismatch");
  expect(auth.isLoading).toBe(false);
  await act(async () => auth.signInWithGoogle());
  expect(auth.error).toBeNull();
});
it("web retains Firebase popup login and never calls Android login", async () => {
  mocks.platform = "web";
  await mount();
  await act(async () => auth.signInWithGoogle());
  expect(mocks.popup).toHaveBeenCalledOnce();
  expect(mocks.nativeSignIn).not.toHaveBeenCalled();
  expect(mocks.prompt).not.toHaveBeenCalled();
});
it("guest login still uses Firebase Anonymous", async () => {
  await mount();
  await act(async () => auth.signInAsGuest());
  expect(mocks.guest).toHaveBeenCalledOnce();
  expect(mocks.nativeSignIn).not.toHaveBeenCalled();
});
it("iOS retains its existing AuthSession flow", async () => {
  mocks.platform = "ios";
  vi.stubEnv("EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID", "ios-test-client");
  await mount();
  await act(async () => auth.signInWithGoogle());
  expect(mocks.prompt).toHaveBeenCalledOnce();
  expect(mocks.nativeSignIn).not.toHaveBeenCalled();
  expect(mocks.popup).not.toHaveBeenCalled();
});
it("fetches a verified profile after Firebase login instead of trusting a native role", async () => {
  mocks.profile.mockResolvedValue({ firebaseUid: "firebase-test-user", displayName: "Lector", role: "reader" });
  await mount();
  await act(async () => mocks.listener?.({ getIdToken: async () => "firebase-test-id-token", isAnonymous: false }));
  expect(mocks.profile).toHaveBeenCalledWith("firebase-test-id-token");
  expect(auth.user?.id).toBe("firebase-test-user");
  expect(auth.user?.role).toBe("reader");
  expect(auth.isLoading).toBe(false);
});
it("finishes Firebase logout even if native Google cleanup fails", async () => {
  mocks.nativeSignOut.mockRejectedValueOnce(new Error("Play Services failed"));
  await mount();
  await act(async () => auth.signOut());
  expect(mocks.logout).toHaveBeenCalledOnce();
  expect(mocks.nativeSignOut).toHaveBeenCalledOnce();
  expect(auth.user).toBeNull();
});
