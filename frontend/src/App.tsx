import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { LoginScreen } from "./features/auth/LoginScreen";
import { NewsFeedScreen } from "./features/news/NewsFeedScreen";
import { useGoogleAuth } from "./services/googleAuth";
import { colors } from "./theme";

export default function App() {
  const {
    user,
    isLoading,
    error,
    isGoogleConfigured,
    canPromptGoogle,
    signInWithGoogle,
    signInAsGuest,
    signOut,
  } = useGoogleAuth();

  if (isLoading && !user) {
    return (
      <View style={styles.splash}>
        <StatusBar style="light" />
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      {user ? (
        <NewsFeedScreen user={user} onSignOut={() => void signOut()} />
      ) : (
        <LoginScreen
          isLoading={isLoading}
          error={error}
          isGoogleConfigured={isGoogleConfigured}
          canPromptGoogle={canPromptGoogle}
          onSignInWithGoogle={() => void signInWithGoogle()}
          onSignInAsGuest={() => void signInAsGuest()}
        />
      )}
    </>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.background,
  },
});
