import * as LocalAuthentication from 'expo-local-authentication';
import { Platform } from 'react-native';

export type BiometricCapability = {
  available: boolean;
  enrolled: boolean;
  label: string;
};

function labelForTypes(types: LocalAuthentication.AuthenticationType[]): string {
  const supportsFace = types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION);
  const supportsFingerprint = types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT);

  if (supportsFace && supportsFingerprint) {
    return 'rostro o huella';
  }
  if (supportsFace) {
    return 'reconocimiento facial';
  }
  if (supportsFingerprint) {
    return 'huella digital';
  }
  return 'biometría';
}

export async function getBiometricCapability(): Promise<BiometricCapability> {
  if (Platform.OS === 'web') {
    return { available: false, enrolled: false, label: 'biometría' };
  }

  try {
    const [available, enrolled, types] = await Promise.all([
      LocalAuthentication.hasHardwareAsync(),
      LocalAuthentication.isEnrolledAsync(),
      LocalAuthentication.supportedAuthenticationTypesAsync(),
    ]);

    return {
      available,
      enrolled,
      label: labelForTypes(types),
    };
  } catch {
    return { available: false, enrolled: false, label: 'biometría' };
  }
}

export async function authenticateWithDeviceBiometrics(promptMessage: string): Promise<boolean> {
  if (Platform.OS === 'web') {
    return false;
  }

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage,
    promptSubtitle: 'Confirma tu identidad para continuar',
    cancelLabel: 'Cancelar',
    fallbackLabel: '',
    disableDeviceFallback: true,
    biometricsSecurityLevel: 'strong',
    requireConfirmation: true,
  });

  return result.success;
}

