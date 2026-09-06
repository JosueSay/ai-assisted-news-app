import { StyleSheet, Text, View } from 'react-native';

import { colors, radii } from '../theme';
import type { ArrivalStatus } from '../types';

const statusContent = {
  on_time: {
    label: 'A tiempo',
    background: colors.successSoft,
    foreground: colors.success,
  },
  late: {
    label: 'Tarde',
    background: colors.warningSoft,
    foreground: colors.warning,
  },
  missing: {
    label: 'Falta',
    background: colors.dangerSoft,
    foreground: colors.danger,
  },
  recorded: {
    label: 'Registrado',
    background: colors.primarySoft,
    foreground: colors.primary,
  },
} as const;

export function StatusBadge({ status }: { status: ArrivalStatus }) {
  const content = statusContent[status];

  return (
    <View style={[styles.badge, { backgroundColor: content.background }]}>
      <View style={[styles.dot, { backgroundColor: content.foreground }]} />
      <Text style={[styles.label, { color: content.foreground }]}>{content.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderRadius: radii.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    fontSize: 12,
    fontWeight: '800',
  },
});
