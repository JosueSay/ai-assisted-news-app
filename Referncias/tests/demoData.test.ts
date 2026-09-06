import { afterAll, describe, expect, it } from 'vitest';

import { formatDateKey, toMonthKey } from '../src/lib/date';
import {
  demoGetMonthlyAttendance,
  demoGetSettings,
  demoMarkAttendance,
  demoUpdateSettings,
} from '../src/services/demoData';

const originalSettings = await demoGetSettings();

afterAll(async () => {
  await demoUpdateSettings(originalSettings);
});

describe('demo data parity', () => {
  it('does not fabricate attendance for a future month', async () => {
    const future = new Date();
    future.setFullYear(future.getFullYear() + 2);
    expect(await demoGetMonthlyAttendance(toMonthKey(future))).toEqual([]);
  });

  it('validates stored times even when their event is disabled', async () => {
    await expect(
      demoUpdateSettings({
        ...originalSettings,
        entryEnabled: false,
        entryTime: '99:99',
      }),
    ).rejects.toThrow('HH:mm');
  });

  it('enforces disabled marks in the data service', async () => {
    await demoUpdateSettings({ ...originalSettings, entryEnabled: false });
    await expect(
      demoMarkAttendance({
        employeeCode: 'EMP-002',
        pin: '2345',
        eventType: 'entry',
        verificationMethod: 'pin',
      }),
    ).rejects.toThrow('desactivado');
    await demoUpdateSettings(originalSettings);
  });

  it('keeps a real mark visible even on a non-standard workday', async () => {
    await demoMarkAttendance({
      employeeCode: 'EMP-003',
      pin: '3456',
      eventType: 'entry',
      verificationMethod: 'pin',
    });

    const today = formatDateKey(new Date(), originalSettings.timezone);
    const rows = await demoGetMonthlyAttendance(`${today.slice(0, 7)}-01`);
    expect(rows.some((row) => row.employeeCode === 'EMP-003' && row.date === today)).toBe(true);
  });
});

