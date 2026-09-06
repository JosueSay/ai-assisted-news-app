import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatMonth, shiftMonth } from '../lib/date';
import { colors, radii } from '../theme';

type MonthSelectorProps = {
  value: string;
  onChange: (month: string) => void;
};

export function MonthSelector({ value, onChange }: MonthSelectorProps) {
  return (
    <View style={styles.container}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Mes anterior"
        onPress={() => onChange(shiftMonth(value, -1))}
        style={({ pressed }) => [styles.arrow, pressed && styles.pressed]}
      >
        <Text style={styles.arrowText}>‹</Text>
      </Pressable>
      <Text accessibilityRole="header" style={styles.label}>
        {formatMonth(value)}
      </Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Mes siguiente"
        onPress={() => onChange(shiftMonth(value, 1))}
        style={({ pressed }) => [styles.arrow, pressed && styles.pressed]}
      >
        <Text style={styles.arrowText}>›</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    flexGrow: 1,
    flexShrink: 1,
    minWidth: 220,
    maxWidth: 340,
  },
  arrow: {
    width: 42,
    height: 42,
    borderRadius: radii.medium,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrowText: {
    color: colors.primary,
    fontSize: 30,
    lineHeight: 34,
    fontWeight: '500',
  },
  label: {
    flex: 1,
    textAlign: 'center',
    color: colors.ink,
    fontWeight: '800',
    fontSize: 17,
  },
  pressed: {
    backgroundColor: colors.primarySoft,
  },
});
