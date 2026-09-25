import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { AppButton } from "../../components/AppButton";
import { colors, spacing } from "../../theme";

type Props = {
  isLoading: boolean;
  error: string | null;
  isGoogleConfigured: boolean;
  canPromptGoogle: boolean;
  onSignInWithGoogle: () => void;
  onSignInAsGuest: () => void;
};

export function LoginScreen({
  isLoading,
  error,
  isGoogleConfigured,
  canPromptGoogle,
  onSignInWithGoogle,
  onSignInAsGuest,
}: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI News</Text>
      <Text style={styles.subtitle}>
        Noticias resumidas y un asistente para entenderlas mejor.
      </Text>

      {isLoading ? <ActivityIndicator color={colors.primary} /> : null}

      <View style={styles.actions}>
        <AppButton
          label="Iniciar sesión con Google"
          onPress={onSignInWithGoogle}
          disabled={!isGoogleConfigured || !canPromptGoogle || isLoading}
        />
        <AppButton
          label="Continuar como invitado"
          variant="secondary"
          onPress={onSignInAsGuest}
          disabled={isLoading}
        />
      </View>

      {!isGoogleConfigured ? (
        <Text style={styles.hint}>
          El login con Google todavía no está configurado en este dispositivo.
          Mirá el README del frontend para activarlo, o entrá como invitado
          para ver la experiencia completa.
        </Text>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
    gap: spacing.md,
  },
  title: { fontSize: 32, fontWeight: "700", color: colors.text },
  subtitle: {
    fontSize: 16,
    color: colors.textMuted,
    textAlign: "center",
  },
  actions: { width: "100%", gap: spacing.sm, marginTop: spacing.lg },
  hint: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: "center",
    marginTop: spacing.md,
  },
  error: {
    fontSize: 13,
    color: colors.danger,
    textAlign: "center",
    marginTop: spacing.sm,
  },
});
