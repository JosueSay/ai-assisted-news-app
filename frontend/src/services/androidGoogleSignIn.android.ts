import { GoogleAuthProvider, signInWithCredential, type Auth } from "@firebase/auth";

export const isAndroidGoogleConfigured = true;

type GoogleSdk = typeof import("react-native-nitro-google-signin").GoogleOneTapSignIn;
let googleSdk: GoogleSdk | undefined;

async function getGoogleSdk(): Promise<GoogleSdk> {
  if (!googleSdk) {
    // Lazy loading keeps guest access usable even without the native module
    // (for example in Expo Go). A signed APK includes it through autolinking.
    const { GoogleOneTapSignIn } = await import("react-native-nitro-google-signin");
    GoogleOneTapSignIn.configure({ webClientId: "autoDetect" });
    googleSdk = GoogleOneTapSignIn;
  }
  return googleSdk;
}

export async function signInWithAndroidGoogle(auth: Auth): Promise<boolean> {
  const sdk = await getGoogleSdk();
  await sdk.checkPlayServices(true);
  const response = await sdk.presentExplicitSignIn();
  if (response.type === "cancelled") return false;
  if (response.type !== "success" || !response.data?.idToken) {
    throw new Error("Google no devolvió una credencial de acceso. Vuelve a seleccionar tu cuenta.");
  }
  const credential = GoogleAuthProvider.credential(response.data.idToken);
  await signInWithCredential(auth, credential);
  return true;
}

export async function clearAndroidGoogleSession(): Promise<void> {
  // Do not load Nitro solely to sign out a guest session.
  if (googleSdk) await googleSdk.signOut();
}
