import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import AsyncStorage from "@react-native-async-storage/async-storage";

import type { AppUser } from "../types";

WebBrowser.maybeCompleteAuthSession();

const STORAGE_KEY = "ai-news:auth-user";

const discovery = {
  authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
  revocationEndpoint: "https://oauth2.googleapis.com/revoke",
};

function readClientId(): string | null {
  const id = Platform.select({
    ios: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
    android: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
    default: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
  });
  return id && id.trim().length > 0 ? id.trim() : null;
}

async function fetchGoogleProfile(accessToken: string): Promise<AppUser> {
  const response = await fetch("https://www.googleapis.com/userinfo/v2/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("No se pudo obtener el perfil de Google.");
  }
  const profile = (await response.json()) as {
    id: string;
    name: string;
    email: string;
    picture?: string;
  };
  return {
    id: profile.id,
    name: profile.name,
    email: profile.email,
    photoUrl: profile.picture,
    isGuest: false,
  };
}

/**
 * Login con Google (Authorization Code + PKCE, sin client secret) con
 * invitado como respaldo. El flujo de Google solo completa dentro de un
 * dev client propio (EAS build) porque Google no valida el redirect_uri de
 * Expo Go contra clientes OAuth de tipo Android/iOS; ver README del frontend.
 */
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
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (raw) setUser(JSON.parse(raw) as AppUser);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const persistUser = useCallback(async (nextUser: AppUser) => {
    setUser(nextUser);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
  }, []);

  useEffect(() => {
    if (!clientId) return;

    if (response?.type === "success" && request) {
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
        .then((tokenResponse) => fetchGoogleProfile(tokenResponse.accessToken))
        .then((profile) => persistUser(profile))
        .catch((err: Error) => setError(err.message))
        .finally(() => setIsLoading(false));
    } else if (response?.type === "error") {
      setError(response.error?.message ?? "El inicio de sesión con Google falló.");
    }
  }, [response, request, clientId, redirectUri, persistUser]);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    await promptAsync();
  }, [promptAsync]);

  const signInAsGuest = useCallback(async () => {
    setError(null);
    await persistUser({
      id: "guest",
      name: "Invitado",
      email: "invitado@demo.local",
      isGuest: true,
    });
  }, [persistUser]);

  const signOut = useCallback(async () => {
    setUser(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    user,
    isLoading,
    error,
    isGoogleConfigured: clientId !== null,
    canPromptGoogle: Boolean(request),
    signInWithGoogle,
    signInAsGuest,
    signOut,
  };
}
