import { useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from "react-native";
import { LogIn, ShieldCheck, UserRound } from "lucide-react-native";

import { AppButton } from "../../components/AppButton";
import { colors, fonts, shadows, spacing } from "../../theme";

type Props = {
  isLoading: boolean;
  error: string | null;
  isGoogleConfigured: boolean;
  canPromptGoogle: boolean;
  onSignInWithGoogle: () => void;
  onSignInAsGuest: () => void;
  onSignInAsAdmin: (username: string, password: string) => Promise<void>;
};

export function LoginScreen({
  isLoading,
  error,
  isGoogleConfigured,
  canPromptGoogle,
  onSignInWithGoogle,
  onSignInAsGuest,
  onSignInAsAdmin,
}: Props) {
  const [showAdmin, setShowAdmin] = useState(false);
  const [adminUsername, setAdminUsername] = useState("admin");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminError, setAdminError] = useState<string | null>(null);

  const handleAdminLogin = async () => {
    setAdminError(null);
    if (!adminUsername.trim() || !adminPassword.trim()) {
      setAdminError("Completa usuario y contraseña admin.");
      return;
    }
    try {
      await onSignInAsAdmin(adminUsername.trim(), adminPassword);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "No pudimos iniciar sesión admin.");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.panel}>
        <View style={styles.brandBlock}>
          <Text style={styles.eyebrow}>AI Assisted News</Text>
          <Text style={styles.title}>AI News</Text>
          <View style={styles.brandLine} />
        </View>

        <Text style={styles.subtitle}>
          Portada editorial conectada a MongoDB, lectura completa, búsqueda y
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
          <AppButton
            label={showAdmin ? "Ocultar acceso admin" : "Acceso admin"}
            variant="ghost"
            onPress={() => {
              setAdminError(null);
              setShowAdmin((current) => !current);
            }}
            disabled={isLoading}
            icon={<ShieldCheck size={18} color={colors.action} />}
          />
        </View>

        {showAdmin ? (
          <View style={styles.adminPanel}>
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Usuario admin</Text>
              <TextInput
                accessibilityLabel="Usuario admin"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
                onChangeText={setAdminUsername}
                returnKeyType="next"
                style={styles.input}
                value={adminUsername}
              />
            </View>
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Contraseña admin</Text>
              <TextInput
                accessibilityLabel="Contraseña admin"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
                onChangeText={setAdminPassword}
                onSubmitEditing={() => void handleAdminLogin()}
                returnKeyType="done"
                secureTextEntry
                style={styles.input}
                value={adminPassword}
              />
            </View>
            {adminError ? <Text style={styles.error}>{adminError}</Text> : null}
            <AppButton
              label="Entrar como admin"
              onPress={() => void handleAdminLogin()}
              disabled={isLoading}
              icon={<ShieldCheck size={18} color={colors.onSolid} />}
            />
          </View>
        ) : null}

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
  eyebrow: {
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
  adminPanel: {
    gap: spacing.sm,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    paddingTop: spacing.md,
  },
  fieldGroup: {
    gap: spacing.xs,
  },
  label: {
    color: colors.text,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    lineHeight: 20,
  },
  input: {
    minHeight: 48,
    borderColor: colors.controlBorder,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontFamily: fonts.body,
    fontSize: 16,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
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
