import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Auth } from "@firebase/auth";

const mocks = vi.hoisted(() => ({
  configure: vi.fn(), checkPlayServices: vi.fn(), presentExplicitSignIn: vi.fn(),
  signOut: vi.fn(), credential: vi.fn(), signInWithCredential: vi.fn(),
}));
vi.mock("react-native-nitro-google-signin", () => ({ GoogleOneTapSignIn: mocks }));
vi.mock("@firebase/auth", () => ({
  GoogleAuthProvider: { credential: mocks.credential },
  signInWithCredential: mocks.signInWithCredential,
}));

import { signInWithAndroidGoogle, clearAndroidGoogleSession } from "../src/services/androidGoogleSignIn.android";
import { isAndroidGoogleConfigured as availableOnOtherPlatforms } from "../src/services/androidGoogleSignIn";

const auth = {} as Auth;
beforeEach(() => {
  vi.clearAllMocks();
  mocks.checkPlayServices.mockResolvedValue(undefined);
  mocks.signOut.mockResolvedValue(undefined);
  mocks.credential.mockReturnValue({ providerId: "google.com" });
  mocks.signInWithCredential.mockResolvedValue({});
});

describe("Android Google credentials into Firebase", () => {
  it("opens an explicit account picker and exchanges the Google ID token for a Firebase session", async () => {
    mocks.presentExplicitSignIn.mockResolvedValue({ type: "success", data: { idToken: "google-test-id-token" } });
    expect(await signInWithAndroidGoogle(auth)).toBe(true);
    expect(mocks.configure).toHaveBeenCalledWith({ webClientId: "autoDetect" });
    expect(mocks.checkPlayServices).toHaveBeenCalledWith(true);
    expect(mocks.presentExplicitSignIn).toHaveBeenCalledOnce();
    expect(mocks.credential).toHaveBeenCalledWith("google-test-id-token");
    expect(mocks.signInWithCredential).toHaveBeenCalledWith(auth, { providerId: "google.com" });
  });
  it("lets a person cancel without creating a Firebase session", async () => {
    mocks.presentExplicitSignIn.mockResolvedValue({ type: "cancelled", data: null });
    expect(await signInWithAndroidGoogle(auth)).toBe(false);
    expect(mocks.signInWithCredential).not.toHaveBeenCalled();
  });
  it.each([
    { type: "success", data: { idToken: null } },
    { type: "noSavedCredentialFound", data: null },
  ])("rejects a response without a usable Google credential: %j", async response => {
    mocks.presentExplicitSignIn.mockResolvedValue(response);
    await expect(signInWithAndroidGoogle(auth)).rejects.toThrow();
    expect(mocks.signInWithCredential).not.toHaveBeenCalled();
  });
  it("preserves native setup errors and does not try a browser fallback", async () => {
    mocks.checkPlayServices.mockRejectedValueOnce(new Error("Play Services unavailable"));
    await expect(signInWithAndroidGoogle(auth)).rejects.toThrow("Play Services unavailable");
    expect(mocks.presentExplicitSignIn).not.toHaveBeenCalled();
    expect(mocks.signInWithCredential).not.toHaveBeenCalled();
  });
  it("propagates Firebase verification failure", async () => {
    mocks.presentExplicitSignIn.mockResolvedValue({ type: "success", data: { idToken: "invalid-test-token" } });
    mocks.signInWithCredential.mockRejectedValueOnce(new Error("Firebase rejected credential"));
    await expect(signInWithAndroidGoogle(auth)).rejects.toThrow("Firebase rejected credential");
  });
  it("clears the native Google session on logout", async () => {
    mocks.presentExplicitSignIn.mockResolvedValue({ type: "cancelled", data: null });
    await signInWithAndroidGoogle(auth);
    await clearAndroidGoogleSession();
    expect(mocks.signOut).toHaveBeenCalledOnce();
  });
  it("does not enable this Android implementation on web or iOS", () => {
    expect(availableOnOtherPlatforms).toBe(false);
  });
});
