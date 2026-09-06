import { StyleSheet, Text, View } from 'react-native';

import { colors, radii } from '../theme';

type NoticeTone = 'info' | 'success' | 'warning' | 'error';

type InlineNoticeProps = {
  message: string;
  tone?: NoticeTone;
};

const tones = {
  info: { background: colors.primarySoft, foreground: colors.primary, icon: 'i' },
  success: { background: colors.successSoft, foreground: colors.success, icon: '✓' },
  warning: { background: colors.warningSoft, foreground: colors.warning, icon: '!' },
  error: { background: colors.dangerSoft, foreground: colors.danger, icon: '!' },
} as const;

export function InlineNotice({ message, tone = 'info' }: InlineNoticeProps) {
  const palette = tones[tone];

  return (
    <View
      accessibilityLiveRegion="polite"
      accessibilityRole={tone === 'error' ? 'alert' : undefined}
      style={[styles.notice, { backgroundColor: palette.background }]}
    >
      <View style={[styles.icon, { borderColor: palette.foreground }]}>
        <Text style={[styles.iconText, { color: palette.foreground }]}>{palette.icon}</Text>
      </View>
      <Text style={[styles.message, { color: palette.foreground }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: {
    width: '100%',
    borderRadius: radii.medium,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  icon: {
    width: 20,
    height: 20,
    borderWidth: 1.5,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  iconText: {
    fontSize: 12,
    fontWeight: '900',
  },
  message: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
});
