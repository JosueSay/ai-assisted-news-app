import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { LogIn, UserRound } from "lucide-react-native";

import { AppButton } from "../../components/AppButton";
import { colors, fonts, shadows, spacing } from "../../theme";

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
      <View style={styles.panel}>
        <View style={styles.brandBlock}>
          <Text style={styles.demo}>Edición de demostración</Text>
          <Text style={styles.title}>AI News</Text>
          <View style={styles.brandLine} />
        </View>

        <Text style={styles.subtitle}>
          Portada editorial con noticias simuladas, lectura completa, búsqueda y
          guardados locales.
        </Text>

        {isLoading ? <ActivityIndicator color={colors.action} /> : null}

        <View style={styles.actions}>
          <AppButton
            label="Iniciar sesión con Google"
            onPress={onSignInWithGoogle}
            disabled={!isGoogleConfigured || !canPromptGoogle || isLoading}
            icon={<LogIn size={18} color={colors.onSolid} />}
          />
          <AppButton
            label="Continuar como invitado"
            variant="secondary"
            onPress={onSignInAsGuest}
            disabled={isLoading}
            icon={<UserRound size={18} color={colors.ink} />}
          />
        </View>

        {!isGoogleConfigured ? (
          <Text style={styles.hint}>
            Google Sign-In aún no está configurado para este dispositivo. Puedes
            entrar como invitado para revisar la experiencia completa.
          </Text>
        ) : null}

        {error ? <Text style={styles.error}>{error}</Text> : null}
      </View>
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
  },
  panel: {
    width: "100%",
    maxWidth: 440,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: spacing.xl,
    gap: spacing.md,
    ...shadows.panel,
  },
  brandBlock: {
    alignItems: "flex-start",
    gap: spacing.xs,
  },
  demo: {
    color: colors.brand,
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    letterSpacing: 0.72,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontFamily: fonts.headingBold,
    fontSize: 40,
    lineHeight: 44,
  },
  brandLine: {
    width: 56,
    height: 3,
    backgroundColor: colors.brand,
  },
  subtitle: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 16,
    lineHeight: 25,
  },
  actions: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  hint: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 13,
    lineHeight: 20,
  },
  error: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    lineHeight: 20,
  },
});
