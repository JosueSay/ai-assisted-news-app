import { calculateSummary } from '../lib/date';
import { parseAttendancePhotoError } from '../lib/attendancePhoto';
import { isDemoMode, requireClient, supabase } from '../lib/supabase';
import type {
  AdminIdentity,
  AttendanceEventType,
  AttendanceRow,
  AttendanceSettings,
  EmployeeDirectoryEntry,
  MarkAttendanceInput,
  MarkAttendanceResult,
  MonthlySummary,
} from '../types';
import {
  demoGetEmployeeDirectory,
  demoGetMonthlyAttendance,
  demoGetSettings,
  demoMarkAttendance,
  demoSignIn,
  demoUpdateSettings,
} from './demoData';

type PublicSettingsRow = {
  entry_enabled: boolean;
  entry_time: string;
  exit_enabled: boolean;
  exit_time: string;
  late_tolerance_minutes: number;
  timezone: string;
};

type MonthlyAttendanceRow = {
  employee_id: string;
  employee_code: string;
  employee_name: string;
  department: string | null;
  attendance_date: string;
  entry_at: string | null;
  exit_at: string | null;
  arrival_status: AttendanceRow['status'];
  entry_photo_path: string | null;
  exit_photo_path: string | null;
};

function firstValue<T>(value: T | T[] | null): T | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }
  return value;
}

function mapSettings(row: PublicSettingsRow): AttendanceSettings {
  return {
    entryEnabled: row.entry_enabled,
    entryTime: row.entry_time.slice(0, 5),
    exitEnabled: row.exit_enabled,
    exitTime: row.exit_time.slice(0, 5),
    lateToleranceMinutes: row.late_tolerance_minutes,
    timezone: row.timezone,
  };
}

async function getFunctionErrorMessage(error: unknown): Promise<string> {
  const context = (error as { context?: Response } | null)?.context;
  if (context) {
    try {
      const body = (await context.clone().json()) as { error?: unknown };
      if (typeof body.error === 'string' && body.error.trim()) {
        return body.error;
      }
    } catch {
      // Fall back to the SDK message below when the response is not JSON.
    }
  }

  return error instanceof Error ? error.message : 'No se pudo registrar el marcaje.';
}

export async function getAttendanceSettings(): Promise<AttendanceSettings> {
  if (isDemoMode) {
    return demoGetSettings();
  }

  const client = requireClient();
  const { data, error } = await client.rpc('get_public_attendance_settings');
  if (error) {
    throw new Error(error.message);
  }

  const row = firstValue(data as PublicSettingsRow | PublicSettingsRow[] | null);
  if (!row) {
    throw new Error('No se encontró la configuración de asistencia.');
  }

  return mapSettings(row);
}

type EmployeeDirectoryRow = {
  employee_code: string;
  full_name: string;
};

export async function getEmployeeDirectory(): Promise<EmployeeDirectoryEntry[]> {
  if (isDemoMode) {
    return demoGetEmployeeDirectory();
  }

  const client = requireClient();
  const { data, error } = await client.rpc('get_active_employee_directory');
  if (error) {
    throw new Error(error.message);
  }

  return ((data ?? []) as EmployeeDirectoryRow[]).map((row) => ({
    employeeCode: row.employee_code,
    fullName: row.full_name,
  }));
}

export async function updateAttendanceSettings(
  settings: AttendanceSettings,
): Promise<AttendanceSettings> {
  if (isDemoMode) {
    return demoUpdateSettings(settings);
  }

  const client = requireClient();
  const { data, error } = await client.rpc('update_attendance_settings', {
    p_entry_enabled: settings.entryEnabled,
    p_entry_time: settings.entryTime,
    p_exit_enabled: settings.exitEnabled,
    p_exit_time: settings.exitTime,
    p_late_tolerance_minutes: settings.lateToleranceMinutes,
  });

  if (error) {
    throw new Error(error.message);
  }

  const row = firstValue(data as PublicSettingsRow | PublicSettingsRow[] | null);
  return row ? mapSettings(row) : settings;
}

export async function markAttendance(input: MarkAttendanceInput): Promise<MarkAttendanceResult> {
  if (isDemoMode) {
    return demoMarkAttendance(input);
  }

  const client = requireClient();
  const { data, error } = await client.functions.invoke('register-attendance', {
    body: {
      employeeCode: input.employeeCode.trim().toUpperCase(),
      pin: input.pin,
      eventType: input.eventType,
      photoBase64: input.photoBase64,
    },
  });

  if (error) {
    throw new Error(await getFunctionErrorMessage(error));
  }

  const result = firstValue(
    data as
      | {
          employee_name: string;
          event_type: MarkAttendanceResult['eventType'];
          recorded_at: string;
          attendance_status: MarkAttendanceResult['status'];
          duplicate: boolean;
          photo_saved?: boolean;
          photo_error?: unknown;
        }
      | null,
  );

  if (!result) {
    throw new Error('El servidor no devolvió la confirmación del marcaje.');
  }

  const photoSaved = result.photo_saved === true;
  const photoError = photoSaved
    ? null
    : parseAttendancePhotoError(result.photo_error)
      ?? (input.photoBase64 ? 'upload_failed' : 'not_provided');

  return {
    employeeName: result.employee_name,
    eventType: result.event_type,
    recordedAt: result.recorded_at,
    status: result.attendance_status,
    duplicate: result.duplicate,
    photoSaved,
    photoError,
  };
}

export async function signInAdmin(email: string, password: string): Promise<AdminIdentity> {
  if (isDemoMode) {
    return demoSignIn(email, password);
  }

  const client = requireClient();
  const { data, error } = await client.auth.signInWithPassword({
    email: email.trim(),
    password,
  });

  if (error || !data.user) {
    throw new Error(error?.message ?? 'No se pudo iniciar sesión.');
  }

  const { data: profile, error: profileError } = await client
    .from('profiles')
    .select('full_name, role')
    .eq('id', data.user.id)
    .single();

  if (profileError || profile?.role !== 'admin') {
    await client.auth.signOut();
    throw new Error('La cuenta no tiene permisos de administrador.');
  }

  return {
    id: data.user.id,
    name: profile.full_name || data.user.email || 'Administrador',
    email: data.user.email ?? email.trim(),
  };
}

export async function signOutAdmin(): Promise<void> {
  if (!isDemoMode && supabase) {
    await supabase.auth.signOut();
  }
}

export async function getMonthlyAttendance(month: string): Promise<AttendanceRow[]> {
  if (isDemoMode) {
    return demoGetMonthlyAttendance(month);
  }

  const client = requireClient();
  const pageSize = 500;
  const allRows: MonthlyAttendanceRow[] = [];

  for (let offset = 0; ; offset += pageSize) {
    const { data, error } = await client.rpc('get_monthly_attendance', {
      p_month: month,
      p_limit: pageSize,
      p_offset: offset,
    });

    if (error) {
      throw new Error(error.message);
    }

    const page = (data ?? []) as MonthlyAttendanceRow[];
    allRows.push(...page);
    if (page.length < pageSize) {
      break;
    }
  }

  const uniqueRows = [...new Map(
    allRows.map((row) => [`${row.employee_id}:${row.attendance_date}`, row] as const),
  ).values()];

  return uniqueRows.map((row) => ({
    id: `${row.employee_id}-${row.attendance_date}`,
    employeeId: row.employee_id,
    employeeCode: row.employee_code,
    employeeName: row.employee_name,
    department: row.department,
    date: row.attendance_date,
    entryAt: row.entry_at,
    exitAt: row.exit_at,
    status: row.arrival_status,
    entryPhotoPath: row.entry_photo_path,
    exitPhotoPath: row.exit_photo_path,
  }));
}

export async function getMonthlySummary(month: string): Promise<MonthlySummary> {
  return calculateSummary(await getMonthlyAttendance(month));
}

export async function getAttendancePhotoUrl(photoPath: string): Promise<string> {
  const client = requireClient();
  const { data, error } = await client.storage
    .from('attendance-photos')
    .createSignedUrl(photoPath, 60);

  if (error || !data?.signedUrl) {
    throw new Error(error?.message ?? 'No se pudo obtener la foto.');
  }

  return data.signedUrl;
}

export async function deleteAttendancePhoto(
  employeeId: string,
  date: string,
  eventType: AttendanceEventType,
  photoPath: string,
): Promise<void> {
  const client = requireClient();
  await client.storage.from('attendance-photos').remove([photoPath]);

  const { error } = await client.rpc('clear_attendance_photo', {
    p_employee_id: employeeId,
    p_attendance_date: date,
    p_event_type: eventType,
  });

  if (error) {
    throw new Error(error.message);
  }
}
