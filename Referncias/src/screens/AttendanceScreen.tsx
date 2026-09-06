import { useEffect, useMemo, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  AppState,
  Platform,
  Pressable,
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
import { CameraCapture, type CameraCaptureHandle } from '../components/CameraCapture';
import { InlineNotice } from '../components/InlineNotice';
import { PersonSelect } from '../components/PersonSelect';
import { formatClock, formatLongDate, formatRecordedTime, getClockMinutes } from '../lib/date';
import { getAttendancePhotoWarning } from '../lib/attendancePhoto';
import { isDemoMode } from '../lib/supabase';
import { colors, radii, shadows } from '../theme';
import type {
  AttendanceEventType,
  AttendanceSettings,
  EmployeeDirectoryEntry,
  MarkAttendanceResult,
  VerificationMethod,
} from '../types';
import { getAttendanceSettings, getEmployeeDirectory, markAttendance } from '../services/attendance';
import {
  authenticateWithDeviceBiometrics,
  getBiometricCapability,
  type BiometricCapability,
} from '../services/biometrics';

type AttendanceScreenProps = {
  onOpenAdmin: () => void;
};

const personalDeviceMode = process.env.EXPO_PUBLIC_ATTENDANCE_DEVICE_MODE === 'personal';
const allowPinFallback = process.env.EXPO_PUBLIC_ALLOW_PIN_FALLBACK === 'true' || isDemoMode;

function chooseDefaultEvent(settings: AttendanceSettings): AttendanceEventType {
  if (!settings.entryEnabled && settings.exitEnabled) {
    return 'exit';
  }
  if (settings.entryEnabled && settings.exitEnabled) {
    const [exitHour = '16', exitMinute = '00'] = settings.exitTime.split(':');
    const nowMinutes = getClockMinutes(new Date(), settings.timezone);
    const exitMinutes = Number(exitHour) * 60 + Number(exitMinute) - 120;
    return nowMinutes >= exitMinutes ? 'exit' : 'entry';
  }
  return 'entry';
}

export function AttendanceScreen({ onOpenAdmin }: AttendanceScreenProps) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 760;
  const pinRef = useRef<TextInput>(null);
  const cameraRef = useRef<CameraCaptureHandle>(null);
  const hasLoadedSettings = useRef(false);
  const [now, setNow] = useState(() => new Date());
  const [employeeCode, setEmployeeCode] = useState('');
  const [pin, setPin] = useState('');
  const [eventType, setEventType] = useState<AttendanceEventType>('entry');
  const [settings, setSettings] = useState<AttendanceSettings | null>(null);
  const [directory, setDirectory] = useState<EmployeeDirectoryEntry[]>([]);
  const [loadingDirectory, setLoadingDirectory] = useState(true);
  const [biometric, setBiometric] = useState<BiometricCapability>({
    available: false,
    enrolled: false,
    label: 'biometría',
  });
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MarkAttendanceResult | null>(null);
  const [photoWarning, setPhotoWarning] = useState<string | null>(null);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      try {
        const nextSettings = await getAttendanceSettings();
        if (!active) {
          return;
        }
        const recoveredFromInitialError = !hasLoadedSettings.current;
        hasLoadedSettings.current = true;
        setSettings(nextSettings);
        if (recoveredFromInitialError) {
          setError(null);
        }
        setEventType((currentEvent) => {
          const currentStillEnabled =
            (currentEvent === 'entry' && nextSettings.entryEnabled) ||
            (currentEvent === 'exit' && nextSettings.exitEnabled);
          return currentStillEnabled ? currentEvent : chooseDefaultEvent(nextSettings);
        });
      } catch (loadError) {
        if (active && !hasLoadedSettings.current) {
          setError(loadError instanceof Error ? loadError.message : 'No se pudo cargar la configuración.');
        }
      } finally {
        if (active) {
          setLoadingSettings(false);
        }
      }
    }

    void loadSettings();
    const refreshTimer = setInterval(() => void loadSettings(), 60_000);
    const appStateSubscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        void loadSettings();
      }
    });

    return () => {
      active = false;
      clearInterval(refreshTimer);
      appStateSubscription.remove();
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDirectory() {
      try {
        const nextDirectory = await getEmployeeDirectory();
        if (active) {
          setDirectory(nextDirectory);
        }
      } catch {
        // The name picker stays with whatever it last had; the next refresh retries.
      } finally {
        if (active) {
          setLoadingDirectory(false);
        }
      }
    }

    void loadDirectory();
    const refreshTimer = setInterval(() => void loadDirectory(), 60_000);
    const appStateSubscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        void loadDirectory();
      }
    });

    return () => {
      active = false;
      clearInterval(refreshTimer);
      appStateSubscription.remove();
    };
  }, []);

  useEffect(() => {
    let active = true;
    void getBiometricCapability().then((capability) => {
      if (active) {
        setBiometric(capability);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const availableEvents = useMemo(() => {
    const events: AttendanceEventType[] = [];
    if (settings?.entryEnabled) {
      events.push('entry');
    }
    if (settings?.exitEnabled) {
      events.push('exit');
    }
    return events;
  }, [settings]);

  const canSubmit =
    !loadingSettings &&
    availableEvents.includes(eventType) &&
    employeeCode.trim().length > 0 &&
    /^\d{4,8}$/.test(pin);

  async function submitAttendance() {
    if (submitting) {
      return;
    }
    if (!canSubmit) {
      setError('Selecciona tu nombre e ingresa un PIN válido de 4 a 8 dígitos.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setPhotoWarning(null);

    try {
      let verificationMethod: VerificationMethod = 'pin';

      if (personalDeviceMode) {
        if (biometric.available && biometric.enrolled) {
          const verified = await authenticateWithDeviceBiometrics('Confirma tu marcaje');
          if (!verified) {
            throw new Error('No se confirmó la biometría. El marcaje fue cancelado.');
          }
          verificationMethod = 'device_biometric';
        } else if (!allowPinFallback) {
          throw new Error('Este dispositivo no tiene biometría segura configurada.');
        }
      }

      const photoBase64 = isDemoMode
        ? undefined
        : (await cameraRef.current?.capture()) ?? undefined;

      const nextResult = await markAttendance({
        employeeCode,
        pin,
        eventType,
        verificationMethod,
        photoBase64,
      });
      setResult(nextResult);
      setPhotoWarning(
        nextResult.photoSaved
          ? null
          : nextResult.duplicate
            ? `${getAttendancePhotoWarning('duplicate_discarded')} Para comprobar la cámara, usa un marcaje que todavía no exista hoy.`
            : `${getAttendancePhotoWarning(nextResult.photoError)} El marcaje sí quedó registrado.`,
      );
      setEmployeeCode('');
      setPin('');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'No se pudo registrar el marcaje.');
    } finally {
      setSubmitting(false);
    }
  }

  const clockPanel = (
    <View style={[styles.clockPanel, isTablet && styles.clockPanelTablet]}>
      <View style={styles.clockTop}>
        <View style={styles.clockTopLeft}>
          <View style={styles.liveDot} />
          <Text style={styles.liveLabel}>RELOJ ACTIVO</Text>
        </View>
        <CameraCapture ref={cameraRef} style={styles.cameraBox} />
      </View>
      <View style={styles.clockContent}>
        <Text adjustsFontSizeToFit numberOfLines={1} style={[styles.clock, !isTablet && styles.clockMobile]}>
          {formatClock(now, settings?.timezone)}
        </Text>
        <Text style={styles.date}>{formatLongDate(now, settings?.timezone)}</Text>
      </View>
      <View style={styles.scheduleSummary}>
        <View style={styles.scheduleItem}>
          <Text style={styles.scheduleLabel}>Entrada</Text>
          <Text style={styles.scheduleValue}>
            {settings?.entryEnabled ? settings.entryTime : 'Desactivada'}
          </Text>
        </View>
        <View style={styles.scheduleDivider} />
        <View style={styles.scheduleItem}>
          <Text style={styles.scheduleLabel}>Salida</Text>
          <Text style={styles.scheduleValue}>
            {settings?.exitEnabled ? settings.exitTime : 'Desactivada'}
          </Text>
        </View>
      </View>
    </View>
  );

  const formPanel = (
    <View style={[styles.formPanel, isTablet && styles.formPanelTablet]}>
      <View>
        <Text style={styles.eyebrow}>REGISTRO DEL PERSONAL</Text>
        <Text style={styles.title}>Marca tu asistencia</Text>
        <Text style={styles.description}>
          Identifícate y confirma si estás registrando tu entrada o tu salida.
        </Text>
      </View>

      {isDemoMode ? (
        <InlineNotice
          message="Modo demostración: elige a Ana Morales y usa el PIN 1234."
          tone="info"
        />
      ) : null}

      {error ? <InlineNotice message={error} tone="error" /> : null}

      <View style={styles.eventSection}>
        <Text style={styles.fieldLabel}>Tipo de marcaje</Text>
        <View style={styles.eventRow}>
          <EventOption
            active={eventType === 'entry'}
            disabled={!settings?.entryEnabled}
            label="Entrada"
            meta={settings?.entryEnabled ? settings.entryTime : 'No disponible'}
            onPress={() => setEventType('entry')}
          />
          <EventOption
            active={eventType === 'exit'}
            disabled={!settings?.exitEnabled}
            label="Salida"
            meta={settings?.exitEnabled ? settings.exitTime : 'No disponible'}
            onPress={() => setEventType('exit')}
          />
        </View>
      </View>

      <PersonSelect
        label="Nombre del colaborador"
        loading={loadingDirectory}
        onChange={(code) => {
          setEmployeeCode(code);
          pinRef.current?.focus();
        }}
        options={directory}
        value={employeeCode}
      />
      <AppField
        ref={pinRef}
        keyboardType="number-pad"
        label="PIN personal"
        maxLength={8}
        onChangeText={(value) => setPin(value.replace(/\D/g, ''))}
        onSubmitEditing={() => void submitAttendance()}
        placeholder="••••"
        returnKeyType="done"
        secureTextEntry
        value={pin}
      />

      {personalDeviceMode ? (
        <InlineNotice
          message={
            biometric.available && biometric.enrolled
              ? `Después del PIN se solicitará ${biometric.label} del teléfono.`
              : 'No hay biometría enrolada en este teléfono; se aplicará la política de respaldo configurada.'
          }
          tone={biometric.available && biometric.enrolled ? 'success' : 'warning'}
        />
      ) : null}

      <AppButton
        disabled={!canSubmit}
        fullWidth
        loading={submitting}
        onPress={() => void submitAttendance()}
      >
        {eventType === 'entry' ? 'Registrar entrada' : 'Registrar salida'}
      </AppButton>

      {!loadingSettings && availableEvents.length === 0 ? (
        <InlineNotice message="Los marcajes están desactivados por el administrador." tone="warning" />
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <View style={styles.header}>
          <Brand compact={width < 390} />
          <AppButton onPress={onOpenAdmin} style={styles.adminButton} variant="ghost">
            Administración
          </AppButton>
        </View>
        <ScrollView
          contentContainerStyle={[styles.scrollContent, isTablet && styles.scrollContentTablet]}
          keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.mainCard, isTablet && styles.mainCardTablet]}>
            {clockPanel}
            {formPanel}
          </View>
          <Text style={styles.footer}>Los horarios y estados se calculan con la hora segura del servidor.</Text>
        </ScrollView>
      </KeyboardAvoidingView>

      <Modal
        animationType="fade"
        transparent
        visible={Boolean(result)}
        onRequestClose={() => {
          setResult(null);
          setPhotoWarning(null);
        }}
      >
        <View style={styles.modalBackdrop}>
          <View accessibilityViewIsModal style={styles.modalCard}>
            <View style={styles.successIcon}>
              <Text style={styles.successCheck}>✓</Text>
            </View>
            <Text style={styles.modalEyebrow}>{result?.duplicate ? 'MARCAJE YA REGISTRADO' : 'MARCAJE EXITOSO'}</Text>
            <Text style={styles.modalTitle}>{result?.employeeName}</Text>
            <Text style={styles.modalMessage}>
              {result?.eventType === 'entry' ? 'Entrada' : 'Salida'} registrada a las{' '}
              {formatRecordedTime(result?.recordedAt ?? null, settings?.timezone)}.
            </Text>
            {!isDemoMode && result?.photoSaved ? (
              <InlineNotice message="Foto de respaldo guardada correctamente." tone="success" />
            ) : !isDemoMode && photoWarning ? (
              <InlineNotice message={photoWarning} tone="warning" />
            ) : null}
            <AppButton
              fullWidth
              onPress={() => {
                setResult(null);
                setPhotoWarning(null);
              }}
            >
              Listo
            </AppButton>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

type EventOptionProps = {
  label: string;
  meta: string;
  active: boolean;
  disabled: boolean;
  onPress: () => void;
};

function EventOption({ label, meta, active, disabled, onPress }: EventOptionProps) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: active, disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.eventOption,
        active && styles.eventOptionActive,
        disabled && styles.eventOptionDisabled,
        pressed && !disabled && styles.eventOptionPressed,
      ]}
    >
      <View style={[styles.radio, active && styles.radioActive]}>
        {active ? <View style={styles.radioCenter} /> : null}
      </View>
      <View style={styles.eventText}>
        <Text style={[styles.eventLabel, active && styles.eventLabelActive]}>{label}</Text>
        <Text style={styles.eventMeta}>{meta}</Text>
      </View>
    </Pressable>
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
  adminButton: {
    minHeight: 44,
    paddingHorizontal: 15,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 18,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 18,
  },
  scrollContentTablet: {
    padding: 30,
  },
  mainCard: {
    width: '100%',
    maxWidth: 1120,
    borderRadius: radii.large,
    overflow: 'hidden',
    backgroundColor: colors.surface,
    ...shadows.card,
  },
  mainCardTablet: {
    minHeight: 590,
    flexDirection: 'row',
  },
  clockPanel: {
    minHeight: 320,
    backgroundColor: colors.primary,
    padding: 28,
    justifyContent: 'space-between',
  },
  clockPanelTablet: {
    flex: 0.9,
    minWidth: 330,
    padding: 38,
  },
  clockTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 8,
  },
  clockTopLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingTop: 4,
  },
  cameraBox: {
    width: 88,
    height: 88,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.accent,
  },
  liveLabel: {
    color: '#D6E1DA',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.6,
  },
  clockContent: {
    marginVertical: 30,
  },
  clock: {
    color: colors.white,
    fontSize: 66,
    fontWeight: '300',
    fontVariant: ['tabular-nums'],
    letterSpacing: -2,
  },
  clockMobile: {
    fontSize: 50,
  },
  date: {
    color: '#D6E1DA',
    fontSize: 16,
    lineHeight: 23,
    marginTop: 8,
  },
  scheduleSummary: {
    borderTopWidth: 1,
    borderTopColor: '#315447',
    paddingTop: 20,
    flexDirection: 'row',
  },
  scheduleItem: {
    flex: 1,
  },
  scheduleDivider: {
    width: 1,
    backgroundColor: '#315447',
    marginHorizontal: 18,
  },
  scheduleLabel: {
    color: '#AFC2B7',
    fontSize: 12,
    marginBottom: 6,
  },
  scheduleValue: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '800',
  },
  formPanel: {
    padding: 26,
    gap: 20,
  },
  formPanelTablet: {
    flex: 1.1,
    paddingHorizontal: 46,
    paddingVertical: 40,
    justifyContent: 'center',
  },
  eyebrow: {
    color: colors.warning,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 7,
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: '800',
    letterSpacing: -0.7,
  },
  description: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 7,
  },
  fieldLabel: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 7,
  },
  eventSection: {
    width: '100%',
  },
  eventRow: {
    flexDirection: 'row',
    gap: 10,
  },
  eventOption: {
    flex: 1,
    minHeight: 64,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.medium,
    paddingHorizontal: 13,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: colors.white,
  },
  eventOptionActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySoft,
  },
  eventOptionDisabled: {
    opacity: 0.43,
  },
  eventOptionPressed: {
    opacity: 0.78,
  },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioActive: {
    borderColor: colors.primary,
  },
  radioCenter: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.primary,
  },
  eventText: {
    flex: 1,
  },
  eventLabel: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  eventLabelActive: {
    color: colors.primary,
  },
  eventMeta: {
    color: colors.inkMuted,
    fontSize: 11,
    marginTop: 2,
  },
  footer: {
    color: colors.inkMuted,
    fontSize: 12,
    textAlign: 'center',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    maxWidth: 410,
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    padding: 30,
    alignItems: 'center',
    gap: 13,
    ...shadows.card,
  },
  successIcon: {
    width: 66,
    height: 66,
    borderRadius: 33,
    backgroundColor: colors.successSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  successCheck: {
    color: colors.success,
    fontSize: 35,
    fontWeight: '900',
  },
  modalEyebrow: {
    color: colors.success,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  modalTitle: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: '800',
    textAlign: 'center',
  },
  modalMessage: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    textAlign: 'center',
    marginBottom: 8,
  },
});
