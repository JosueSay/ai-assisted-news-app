import { describe, expect, it } from 'vitest';

import { calculateSummary, formatClock, getClockMinutes, isValidTime, shiftMonth } from '../src/lib/date';
import type { AttendanceRow } from '../src/types';

function row(status: AttendanceRow['status']): AttendanceRow {
  return {
    id: crypto.randomUUID(),
    employeeId: crypto.randomUUID(),
    employeeCode: 'EMP-001',
    employeeName: 'Persona de prueba',
    department: null,
    date: '2026-08-20',
    entryAt: null,
    exitAt: null,
    status,
    entryPhotoPath: null,
    exitPhotoPath: null,
  };
}

describe('calculateSummary', () => {
  it('counts each attendance state', () => {
    expect(calculateSummary([row('on_time'), row('on_time'), row('late'), row('missing')])).toEqual({
      onTime: 2,
      late: 1,
      missing: 1,
      total: 4,
    });
  });

  it('excludes exit-only records from arrival totals', () => {
    expect(calculateSummary([row('recorded')])).toEqual({
      onTime: 0,
      late: 0,
      missing: 0,
      total: 0,
    });
  });
});

describe('month helpers', () => {
  it('moves across a year boundary', () => {
    expect(shiftMonth('2026-12-01', 1)).toBe('2027-01-01');
  });
});

describe('time validation', () => {
  it('accepts 24-hour HH:mm values only', () => {
    expect(isValidTime('07:30')).toBe(true);
    expect(isValidTime('23:59')).toBe(true);
    expect(isValidTime('24:00')).toBe(false);
    expect(isValidTime('7:30')).toBe(false);
  });

  it('formats and compares time in the organization timezone', () => {
    const instant = new Date('2026-08-22T13:30:00.000Z');
    expect(formatClock(instant, 'America/Guatemala')).toBe('07:30:00');
    expect(getClockMinutes(instant, 'America/Guatemala')).toBe(450);
  });
});
