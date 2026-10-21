import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInAnonymously,
  signInWithCredential,
  signInWithPopup,
  signOut as firebaseSignOut,
} from "@firebase/auth";

import type { AppUser } from "../types";
import { firebaseAuth, isFirebaseConfigured } from "./firebaseClient";
import { fetchAuthenticatedProfile } from "./newsService";

WebBrowser.maybeCompleteAuthSession();

const discovery = {
  authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
  revocationEndpoint: "https://oauth2.googleapis.com/revoke",
};

function readClientId(): string | null {
  const id = Platform.select({
    ios: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
    android: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
    default: null,
  });
  return id && id.trim().length > 0 ? id.trim() : null;
}

function toAppUser(
  profile: Awaited<ReturnType<typeof fetchAuthenticatedProfile>>,
  isGuest: boolean,
): AppUser {
  return {
    id: profile.firebaseUid,
    name: profile.displayName || (isGuest ? "Invitado" : "Usuario"),
    email: profile.email,
    photoUrl: profile.photoUrl || undefined,
    isGuest,
    role: profile.role,
  };
}

/** Firebase Authentication para Google y personas invitadas. */
export function useGoogleAuth() {
  const clientId = readClientId();
  const redirectUri = AuthSession.makeRedirectUri({ scheme: "ainews" });
  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: clientId ?? "not-configured",
      scopes: ["openid", "profile", "email"],
      redirectUri,
      responseType: AuthSession.ResponseType.Code,
      usePKCE: true,
    },
    discovery,
  );

  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!firebaseAuth) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    return onAuthStateChanged(firebaseAuth, async (firebaseUser) => {
      if (!firebaseUser) {
        setUser(null);
        setError(null);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const idToken = await firebaseUser.getIdToken();
        const profile = await fetchAuthenticatedProfile(idToken);
        setUser(toAppUser(profile, firebaseUser.isAnonymous));
        setError(null);
      } catch (authError) {
        setUser(null);
        setError(
          authError instanceof Error
            ? authError.message
            : "No pudimos validar tu sesión con AI News.",
        );
      } finally {
        setIsLoading(false);
      }
    });
  }, []);

  useEffect(() => {
    if (response?.type === "error") {
      setError(response.error?.message ?? "Google Sign-In falló.");
      setIsLoading(false);
      return;
    }
    if (response?.type !== "success" || !request || Platform.OS === "web") return;
    const auth = firebaseAuth;
    if (!auth || !clientId) {
      setError("Completa la configuración de Firebase y Google para esta app.");
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    AuthSession.exchangeCodeAsync(
      {
        clientId,
        code: response.params.code,
        redirectUri,
        extraParams: request.codeVerifier
          ? { code_verifier: request.codeVerifier }
          : undefined,
      },
      discovery,
    )
      .then(async (tokenResponse) => {
        if (!tokenResponse.accessToken) {
          throw new Error("Google no devolvió una credencial de acceso.");
        }
        const credential = GoogleAuthProvider.credential(null, tokenResponse.accessToken);
        await signInWithCredential(auth, credential);
      })
      .catch((authError: Error) => {
        setError(authError.message);
        setIsLoading(false);
      });
  }, [response, request, clientId, redirectUri]);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    if (!isFirebaseConfigured || !firebaseAuth) {
      setError("Completa la configuración pública de Firebase en frontend/.env.");
      return;
    }
    if (Platform.OS === "web") {
      setIsLoading(true);
      try {
        const provider = new GoogleAuthProvider();
        provider.setCustomParameters({ prompt: "select_account" });
        await signInWithPopup(firebaseAuth, provider);
      } catch (authError) {
        setError(authError instanceof Error ? authError.message : "Google Sign-In falló.");
        setIsLoading(false);
      }
      return;
    }
    if (!clientId || !request) {
      setError("Configura el OAuth Client ID de Google para este dispositivo.");
      return;
    }
    await promptAsync();
  }, [clientId, promptAsync, request]);

  const signInAsGuest = useCallback(async () => {
    setError(null);
    if (!firebaseAuth) {
      setError("Completa la configuración pública de Firebase en frontend/.env.");
      return;
    }
    setIsLoading(true);
    try {
      await signInAnonymously(firebaseAuth);
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "No pudimos crear la sesión invitada.");
      setIsLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    if (firebaseAuth) await firebaseSignOut(firebaseAuth);
    setUser(null);
    setError(null);
  }, []);

  return {
    user,
    isLoading,
    error,
    isFirebaseConfigured,
    isGoogleConfigured:
      isFirebaseConfigured && (Platform.OS === "web" || clientId !== null),
    canPromptGoogle: Platform.OS === "web" ? isFirebaseConfigured : Boolean(request),
    signInWithGoogle,
    signInAsGuest,
    signOut,
  };
}
