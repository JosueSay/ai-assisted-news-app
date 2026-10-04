import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import {
  Newsreader_600SemiBold,
  Newsreader_700Bold,
} from "@expo-google-fonts/newsreader";
import {
  Roboto_400Regular,
  Roboto_500Medium,
  Roboto_700Bold,
} from "@expo-google-fonts/roboto";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { LoginScreen } from "./features/auth/LoginScreen";
import { NewsFeedScreen } from "./features/news/NewsFeedScreen";
import { useGoogleAuth } from "./services/googleAuth";
import { colors } from "./theme";

export default function App() {
  const [fontsLoaded] = useFonts({
    Newsreader_600SemiBold,
    Newsreader_700Bold,
    Roboto_400Regular,
    Roboto_500Medium,
    Roboto_700Bold,
  });

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

  if (!fontsLoaded || (isLoading && !user)) {
    return (
      <View style={styles.splash}>
        <StatusBar style="dark" />
        <ActivityIndicator color={colors.action} />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
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
