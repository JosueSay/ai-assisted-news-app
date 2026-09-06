import type { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { colors, radii } from '../theme';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type AppButtonProps = {
  children: ReactNode;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
  accessibilityLabel?: string;
};

const variantStyles = {
  primary: {
    button: { backgroundColor: colors.primary, borderColor: colors.primary },
    text: { color: colors.white },
  },
  secondary: {
    button: { backgroundColor: colors.primarySoft, borderColor: colors.primarySoft },
    text: { color: colors.primary },
  },
  ghost: {
    button: { backgroundColor: 'transparent', borderColor: colors.border },
    text: { color: colors.ink },
  },
  danger: {
    button: { backgroundColor: colors.dangerSoft, borderColor: colors.dangerSoft },
    text: { color: colors.danger },
  },
} satisfies Record<ButtonVariant, { button: ViewStyle; text: { color: string } }>;

export function AppButton({
  children,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  accessibilityLabel,
}: AppButtonProps) {
  const palette = variantStyles[variant];
  const isDisabled = disabled || loading;
  const resolvedAccessibilityLabel =
    accessibilityLabel ?? (typeof children === 'string' ? children : undefined);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={resolvedAccessibilityLabel}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      disabled={isDisabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        palette.button,
        fullWidth && styles.fullWidth,
        pressed && !isDisabled && styles.pressed,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={palette.text.color} />
      ) : (
        <Text style={[styles.text, palette.text]}>{children}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 50,
    borderRadius: radii.medium,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  fullWidth: {
    width: '100%',
  },
  text: {
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.1,
  },
  pressed: {
    opacity: 0.82,
    transform: [{ scale: 0.99 }],
  },
  disabled: {
    opacity: 0.48,
  },
});
