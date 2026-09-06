import { forwardRef } from 'react';
import {
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from 'react-native';

import { colors, radii } from '../theme';

type AppFieldProps = TextInputProps & {
  label: string;
  error?: string | null;
  hint?: string;
};

export const AppField = forwardRef<TextInput, AppFieldProps>(function AppField(
  { label, error, hint, editable = true, style, ...inputProps },
  ref,
) {
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        ref={ref}
        accessibilityLabel={label}
        editable={editable}
        placeholderTextColor={colors.inkMuted}
        selectionColor={colors.primary}
        style={[
          styles.input,
          !editable && styles.inputDisabled,
          Boolean(error) && styles.inputError,
          style,
        ]}
        {...inputProps}
      />
      {error ? <Text style={styles.error}>{error}</Text> : hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
});

const styles = StyleSheet.create({
  wrapper: {
    width: '100%',
    gap: 7,
  },
  label: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
  },
  input: {
    minHeight: 52,
    borderRadius: radii.medium,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    color: colors.ink,
    fontSize: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inputDisabled: {
    backgroundColor: colors.surfaceMuted,
    color: colors.inkMuted,
  },
  inputError: {
    borderColor: colors.danger,
  },
  hint: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 17,
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    lineHeight: 17,
  },
});

