import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { getApp, getApps, initializeApp } from "@firebase/app";
import {
  getAuth,
  initializeAuth,
  type Auth,
  type User,
} from "@firebase/auth";
import * as FirebaseAuthModule from "@firebase/auth";

const config = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY?.trim() ?? "",
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN?.trim() ?? "",
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID?.trim() ?? "",
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID?.trim() ?? "",
};

export const isFirebaseConfigured = Object.values(config).every(Boolean);

let auth: Auth | null = null;

if (isFirebaseConfigured) {
  const app = getApps().length ? getApp() : initializeApp(config);
  if (Platform.OS === "web") {
    auth = getAuth(app);
  } else {
    try {
      // Firebase exposes this RN-specific helper through Metro's native entrypoint.
      // The web entrypoint intentionally does not export it.
      const rnPersistence = (
        FirebaseAuthModule as unknown as {
        getReactNativePersistence?: (storage: typeof AsyncStorage) => unknown;
        }
      ).getReactNativePersistence;
      if (typeof rnPersistence !== "function") {
        throw new Error("La persistencia de Firebase para React Native no está disponible.");
      }
      auth = initializeAuth(app, { persistence: rnPersistence(AsyncStorage) as never });
    } catch (error) {
      if ((error as { code?: string }).code === "auth/already-initialized") {
        auth = getAuth(app);
      } else {
        throw error;
      }
    }
  }
}

export { auth as firebaseAuth };

export async function getCurrentFirebaseIdToken(): Promise<string> {
  const currentUser: User | null = auth?.currentUser ?? null;
  if (!currentUser) {
    throw new Error("Inicia sesión para continuar.");
  }
  return currentUser.getIdToken();
}
