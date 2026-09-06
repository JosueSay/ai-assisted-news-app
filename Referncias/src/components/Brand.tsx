import { StyleSheet, Text, View } from 'react-native';

import { colors, radii } from '../theme';

type BrandProps = {
  compact?: boolean;
  inverted?: boolean;
};

export function Brand({ compact = false, inverted = false }: BrandProps) {
  return (
    <View style={styles.row}>
      <View style={[styles.mark, inverted && styles.markInverted]}>
        <Text style={[styles.check, inverted && styles.checkInverted]}>✓</Text>
      </View>
      {!compact ? (
        <View>
          <Text style={[styles.name, inverted && styles.textInverted]}>Fuente del Éxito</Text>
          <Text style={[styles.subtitle, inverted && styles.subtitleInverted]}>Control de asistencia</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  mark: {
    width: 42,
    height: 42,
    borderRadius: radii.medium,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markInverted: {
    backgroundColor: colors.accent,
  },
  check: {
    color: colors.white,
    fontSize: 25,
    fontWeight: '900',
    marginTop: -2,
  },
  checkInverted: {
    color: colors.primary,
  },
  name: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.1,
  },
  textInverted: {
    color: colors.white,
  },
  subtitle: {
    color: colors.inkMuted,
    fontSize: 12,
    marginTop: 2,
  },
  subtitleInverted: {
    color: '#C9D8CF',
  },
});

