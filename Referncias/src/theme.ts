export const colors = {
  background: '#F4F1E8',
  surface: '#FFFEFA',
  surfaceMuted: '#ECE8DC',
  ink: '#17231D',
  inkMuted: '#667168',
  primary: '#12372A',
  primarySoft: '#DDE9DF',
  accent: '#D9A441',
  accentSoft: '#F7EBCF',
  success: '#1F6843',
  successSoft: '#DDF1E6',
  warning: '#85500E',
  warningSoft: '#FAE8CC',
  danger: '#A63D40',
  dangerSoft: '#F8DDDE',
  border: '#D9D5C9',
  white: '#FFFFFF',
  overlay: 'rgba(18, 55, 42, 0.52)',
} as const;

export const radii = {
  small: 10,
  medium: 16,
  large: 24,
  pill: 999,
} as const;

export const shadows = {
  card: {
    shadowColor: '#0B241A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 3,
  },
} as const;
