import type { AttendanceRow, MonthlySummary } from '../types';

const spanishMonthFormatter = new Intl.DateTimeFormat('es-GT', {
  month: 'long',
  year: 'numeric',
});

const spanishShortDateFormatter = new Intl.DateTimeFormat('es-GT', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

export function toMonthKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}-01`;
}

export function monthFromKey(monthKey: string): Date {
  const [yearText, monthText] = monthKey.split('-');
  const year = Number(yearText);
  const month = Number(monthText);

  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) {
    return new Date();
  }

  return new Date(year, month - 1, 1, 12);
}

export function shiftMonth(monthKey: string, delta: number): string {
  const date = monthFromKey(monthKey);
  date.setMonth(date.getMonth() + delta);
  return toMonthKey(date);
}

export function formatMonth(monthKey: string): string {
  const label = spanishMonthFormatter.format(monthFromKey(monthKey));
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function formatLongDate(date: Date, timeZone?: string): string {
  const label = new Intl.DateTimeFormat('es-GT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone,
  }).format(date);
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function formatShortDate(isoDate: string): string {
  return spanishShortDateFormatter.format(new Date(`${isoDate}T12:00:00`));
}

export function formatClock(date: Date, timeZone?: string): string {
  return new Intl.DateTimeFormat('es-GT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone,
  }).format(date);
}

export function formatRecordedTime(isoDate: string | null, timeZone?: string): string {
  if (!isoDate) {
    return '—';
  }

  return new Intl.DateTimeFormat('es-GT', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone,
  }).format(new Date(isoDate));
}

export function getClockMinutes(date: Date, timeZone?: string): number {
  const parts = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone,
  }).formatToParts(date);
  const hour = Number(parts.find((part) => part.type === 'hour')?.value ?? 0);
  const minute = Number(parts.find((part) => part.type === 'minute')?.value ?? 0);
  return hour * 60 + minute;
}

export function calculateSummary(rows: AttendanceRow[]): MonthlySummary {
  const summary: MonthlySummary = {
    onTime: 0,
    late: 0,
    missing: 0,
    total: 0,
  };

  for (const row of rows) {
    if (row.status === 'on_time') {
      summary.onTime += 1;
    } else if (row.status === 'late') {
      summary.late += 1;
    } else if (row.status === 'missing') {
      summary.missing += 1;
    }
  }

  summary.total = summary.onTime + summary.late + summary.missing;

  return summary;
}

export function formatDateKey(date: Date, timeZone?: string): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone,
  }).formatToParts(date);
  const year = parts.find((part) => part.type === 'year')?.value ?? '0000';
  const month = parts.find((part) => part.type === 'month')?.value ?? '00';
  const day = parts.find((part) => part.type === 'day')?.value ?? '00';
  return `${year}-${month}-${day}`;
}

export function isValidTime(value: string): boolean {
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}
