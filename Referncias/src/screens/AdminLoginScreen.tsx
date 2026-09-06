import { useEffect, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';

import { AppButton } from '../components/AppButton';
import { AppField } from '../components/AppField';
import { Brand } from '../components/Brand';
import { InlineNotice } from '../components/InlineNotice';
import { isDemoMode } from '../lib/supabase';
import { colors, radii, shadows } from '../theme';
import type { AdminIdentity } from '../types';
import { signInAdmin, signOutAdmin } from '../services/attendance';
import {
  authenticateWithDeviceBiometrics,
  getBiometricCapability,
} from '../services/biometrics';

type AdminLoginScreenProps = {
  onBack: () => void;
  onAuthenticated: (admin: AdminIdentity) => void;
};

const requireAdminBiometric = process.env.EXPO_PUBLIC_REQUIRE_ADMIN_BIOMETRIC === 'true';

export function AdminLoginScreen({ onBack, onAuthenticated }: AdminLoginScreenProps) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 760;
  const passwordRef = useRef<TextInput>(null);
  const mounted = useRef(true);
  const [email, setEmail] = useState(isDemoMode ? 'admin@demo.local' : '');
  const [password, setPassword] = useState(isDemoMode ? 'Demo1234' : '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      mounted.current = false;
    };
  }, []);

  async function submit() {
    if (loading) {
      return;
    }
    if (!email.trim() || !password) {
      setError('Ingresa tu correo y contraseña.');
      return;
    }

    setLoading(true);
    setError(null);

    let hasServerSession = false;
    try {
      const admin = await signInAdmin(email, password);
      hasServerSession = true;

      if (requireAdminBiometric) {
        const capability = await getBiometricCapability();
        if (!capability.available || !capability.enrolled) {
          throw new Error('Este dispositivo no tiene biometría segura configurada.');
        }
        const verified = await authenticateWithDeviceBiometrics('Acceso administrativo');
        if (!verified) {
          throw new Error('No se confirmó la biometría.');
        }
      }

      if (mounted.current) {
        onAuthenticated(admin);
      }
    } catch (loginError) {
      if (hasServerSession) {
        await signOutAdmin();
      }
      if (mounted.current) {
        setError(loginError instanceof Error ? loginError.message : 'No se pudo iniciar sesión.');
      }
    } finally {
      if (mounted.current) {
        setLoading(false);
      }
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <View style={styles.header}>
          <Brand compact={width < 390} />
          <AppButton disabled={loading} onPress={onBack} style={styles.backButton} variant="ghost">
            Volver al marcaje
          </AppButton>
        </View>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.shell, isTablet && styles.shellTablet]}>
            {isTablet ? (
              <View style={styles.contextPanel}>
                <Brand inverted />
                <View>
                  <Text style={styles.contextEyebrow}>ÁREA PROTEGIDA</Text>
                  <Text style={styles.contextTitle}>Información clara para decisiones a tiempo.</Text>
                  <Text style={styles.contextText}>
                    Consulta registros mensuales, revisa el consolidado y configura los horarios de marcaje desde un solo lugar.
                  </Text>
                </View>
                <Text style={styles.contextFootnote}>Acceso exclusivo para administradores autorizados.</Text>
              </View>
            ) : null}

            <View style={styles.formPanel}>
              <View>
                <Text style={styles.eyebrow}>PANEL ADMINISTRATIVO</Text>
                <Text style={styles.title}>Inicia sesión</Text>
                <Text style={styles.description}>
                  Usa la cuenta administrativa creada en Supabase.
                </Text>
              </View>

              {isDemoMode ? (
                <InlineNotice
                  message="La demostración ya incluye admin@demo.local / Demo1234."
                  tone="info"
                />
              ) : null}

              {error ? <InlineNotice message={error} tone="error" /> : null}

              <AppField
                autoCapitalize="none"
                autoComplete="email"
                autoCorrect={false}
                keyboardType="email-address"
                label="Correo electrónico"
                onChangeText={setEmail}
                onSubmitEditing={() => passwordRef.current?.focus()}
                placeholder="administracion@colegio.edu.gt"
                returnKeyType="next"
                value={email}
              />
              <AppField
                ref={passwordRef}
                autoComplete="current-password"
                label="Contraseña"
                onChangeText={setPassword}
                onSubmitEditing={() => void submit()}
                placeholder="Tu contraseña"
                returnKeyType="done"
                secureTextEntry
                value={password}
              />
              <AppButton fullWidth loading={loading} onPress={() => void submit()}>
                Entrar al panel
              </AppButton>
              {requireAdminBiometric ? (
                <Text style={styles.biometricNote}>
                  Después de la contraseña se solicitará la biometría segura del dispositivo.
                </Text>
              ) : null}
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  header: {
    minHeight: 78,
    paddingHorizontal: 22,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  backButton: {
    minHeight: 44,
    paddingHorizontal: 15,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  shell: {
    width: '100%',
    maxWidth: 940,
    backgroundColor: colors.surface,
    borderRadius: radii.large,
    overflow: 'hidden',
    ...shadows.card,
  },
  shellTablet: {
    minHeight: 560,
    flexDirection: 'row',
  },
  contextPanel: {
    flex: 0.9,
    backgroundColor: colors.primary,
    padding: 38,
    justifyContent: 'space-between',
  },
  contextEyebrow: {
    color: colors.accent,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  contextTitle: {
    color: colors.white,
    fontSize: 34,
    lineHeight: 41,
    fontWeight: '800',
    letterSpacing: -0.8,
  },
  contextText: {
    color: '#C9D8CF',
    fontSize: 14,
    lineHeight: 22,
    marginTop: 18,
  },
  contextFootnote: {
    color: '#AFC2B7',
    fontSize: 12,
  },
  formPanel: {
    flex: 1,
    padding: 30,
    justifyContent: 'center',
    gap: 22,
  },
  eyebrow: {
    color: colors.warning,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.4,
    marginBottom: 7,
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: '800',
    letterSpacing: -0.6,
  },
  description: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 7,
  },
  biometricNote: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
});
