import { calculateSummary, formatDateKey, getClockMinutes, isValidTime } from '../lib/date';
import type {
  AdminIdentity,
  AttendanceRow,
  AttendanceSettings,
  CreateEmployeeInput,
  EmployeeDirectoryEntry,
  EmployeeRow,
  MarkAttendanceInput,
  MarkAttendanceResult,
  MonthlySummary,
  UpdateEmployeeInput,
} from '../types';

type DemoEmployee = {
  id: string;
  code: string;
  pin: string;
  name: string;
  department: string | null;
  active: boolean;
  hiredOn: string;
  endedOn: string | null;
};

const employees: DemoEmployee[] = [
  {
    id: 'EMP-001',
    code: 'EMP-001',
    pin: '1234',
    name: 'Ana Morales',
    department: 'Administración',
    active: true,
    hiredOn: '2026-01-01',
    endedOn: null,
  },
  {
    id: 'EMP-002',
    code: 'EMP-002',
    pin: '2345',
    name: 'Carlos Pérez',
    department: 'Docencia',
    active: true,
    hiredOn: '2026-01-01',
    endedOn: null,
  },
  {
    id: 'EMP-003',
    code: 'EMP-003',
    pin: '3456',
    name: 'Sofía López',
    department: 'Coordinación',
    active: true,
    hiredOn: '2026-01-01',
    endedOn: null,
  },
];

function toEmployeeRow(employee: DemoEmployee): EmployeeRow {
  return {
    id: employee.id,
    employeeCode: employee.code,
    fullName: employee.name,
    department: employee.department,
    active: employee.active,
    hiredOn: employee.hiredOn,
    endedOn: employee.endedOn,
  };
}

let demoSettings: AttendanceSettings = {
  entryEnabled: true,
  entryTime: '07:30',
  exitEnabled: true,
  exitTime: '16:00',
  lateToleranceMinutes: 5,
  timezone: 'America/Guatemala',
};

type DemoManualMark = {
  entryAt?: string;
  exitAt?: string;
  entryStatus?: 'on_time' | 'late' | 'recorded';
};

const manualMarks = new Map<string, DemoManualMark>();

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function localIso(year: number, monthIndex: number, day: number, time: string): string {
  const [hours = '00', minutes = '00'] = time.split(':');
  return `${year}-${pad(monthIndex + 1)}-${pad(day)}T${hours}:${minutes}:00-06:00`;
}

function buildDemoRows(month: string): AttendanceRow[] {
  const [yearValue = '2026', monthValue = '1'] = month.split('-');
  const year = Number(yearValue);
  const monthIndex = Number(monthValue) - 1;
  const start = new Date(year, monthIndex, 1, 12);
  const monthEnd = new Date(year, monthIndex + 1, 0, 12);
  const todayKey = formatDateKey(new Date(), demoSettings.timezone);
  const [todayYear = '0', todayMonth = '0', todayDay = '0'] = todayKey.split('-');
  const currentYear = Number(todayYear);
  const currentMonthIndex = Number(todayMonth) - 1;
  const currentDay = Number(todayDay);
  const isFutureMonth = start > new Date(currentYear, currentMonthIndex, 1, 12);
  const lastDay = isFutureMonth
    ? 0
    : year === currentYear && monthIndex === currentMonthIndex
      ? Math.min(currentDay, monthEnd.getDate())
      : monthEnd.getDate();
  const rows: AttendanceRow[] = [];

  for (let day = start.getDate(); day <= lastDay; day += 1) {
    const date = new Date(year, monthIndex, day, 12);
    const weekday = date.getDay();
    if (weekday === 0 || weekday === 6) {
      continue;
    }

    employees.filter((employee) => employee.active).forEach((employee, employeeIndex) => {
      const dateKey = `${year}-${pad(monthIndex + 1)}-${pad(day)}`;
      const pattern = day + employeeIndex * 2;
      const status = pattern % 11 === 0 ? 'missing' : pattern % 5 === 0 ? 'late' : 'on_time';
      const arrivalMinutes = status === 'late' ? 41 + employeeIndex : 20 + (pattern % 8);
      const entryTime = `07:${pad(arrivalMinutes)}`;
      const manual = manualMarks.get(`${employee.code}:${dateKey}`);
      const entryAt = manual?.entryAt ?? (status === 'missing' ? null : localIso(year, monthIndex, day, entryTime));
      const exitAt = manual?.exitAt ?? (status === 'missing' ? null : localIso(year, monthIndex, day, `16:${pad(pattern % 16)}`));
      const resolvedStatus = manual?.entryAt ? (manual.entryStatus ?? 'on_time') : status;

      if (dateKey === todayKey && !entryAt && !exitAt) {
        return;
      }

      rows.push({
        id: `${employee.code}-${dateKey}`,
        employeeId: employee.id,
        employeeCode: employee.code,
        employeeName: employee.name,
        department: employee.department,
        date: dateKey,
        entryAt,
        exitAt,
        status: entryAt ? resolvedStatus : exitAt ? 'recorded' : 'missing',
        entryPhotoPath: null,
        exitPhotoPath: null,
      });
    });
  }

  for (const [markKey, manual] of manualMarks) {
    const separatorIndex = markKey.indexOf(':');
    const employeeCode = markKey.slice(0, separatorIndex);
    const dateKey = markKey.slice(separatorIndex + 1);
    if (!dateKey.startsWith(`${year}-${pad(monthIndex + 1)}-`)) {
      continue;
    }
    const id = `${employeeCode}-${dateKey}`;
    if (rows.some((row) => row.id === id)) {
      continue;
    }
    const employee = employees.find((item) => item.code === employeeCode);
    if (!employee) {
      continue;
    }
    rows.push({
      id,
      employeeId: employee.id,
      employeeCode,
      employeeName: employee.name,
      department: employee.department,
      date: dateKey,
      entryAt: manual.entryAt ?? null,
      exitAt: manual.exitAt ?? null,
      status: manual.entryAt ? (manual.entryStatus ?? 'on_time') : 'recorded',
      entryPhotoPath: null,
      exitPhotoPath: null,
    });
  }

  return rows.sort((left, right) => {
    const byDate = right.date.localeCompare(left.date);
    return byDate === 0 ? left.employeeName.localeCompare(right.employeeName) : byDate;
  });
}

export async function demoGetSettings(): Promise<AttendanceSettings> {
  return { ...demoSettings };
}

export async function demoUpdateSettings(settings: AttendanceSettings): Promise<AttendanceSettings> {
  if (!isValidTime(settings.entryTime)) {
    throw new Error('La hora de entrada debe tener el formato HH:mm.');
  }
  if (!isValidTime(settings.exitTime)) {
    throw new Error('La hora de salida debe tener el formato HH:mm.');
  }
  if (
    !Number.isInteger(settings.lateToleranceMinutes) ||
    settings.lateToleranceMinutes < 0 ||
    settings.lateToleranceMinutes > 120
  ) {
    throw new Error('La tolerancia debe estar entre 0 y 120 minutos.');
  }
  demoSettings = { ...settings };
  return { ...demoSettings };
}

export async function demoSignIn(email: string, password: string): Promise<AdminIdentity> {
  await new Promise((resolve) => setTimeout(resolve, 450));

  if (email.trim().toLowerCase() !== 'admin@demo.local' || password !== 'Demo1234') {
    throw new Error('Correo o contraseña incorrectos.');
  }

  return {
    id: 'demo-admin',
    name: 'Administrador',
    email: 'admin@demo.local',
  };
}

export async function demoMarkAttendance(input: MarkAttendanceInput): Promise<MarkAttendanceResult> {
  await new Promise((resolve) => setTimeout(resolve, 650));
  const employee = employees.find(
    (item) => item.active && item.code === input.employeeCode.trim().toUpperCase(),
  );

  if (!employee || employee.pin !== input.pin) {
    throw new Error('Código de colaborador o PIN incorrecto.');
  }

  if (input.eventType === 'entry' && !demoSettings.entryEnabled) {
    throw new Error('El registro de entrada está desactivado.');
  }
  if (input.eventType === 'exit' && !demoSettings.exitEnabled) {
    throw new Error('El registro de salida está desactivado.');
  }

  const now = new Date();
  const dateKey = formatDateKey(now, demoSettings.timezone);
  const markKey = `${employee.code}:${dateKey}`;
  const current = manualMarks.get(markKey) ?? {};
  const property = input.eventType === 'entry' ? 'entryAt' : 'exitAt';
  const duplicate = Boolean(current[property]);

  const [scheduledHour = '07', scheduledMinute = '30'] = demoSettings.entryTime.split(':');
  const scheduledTotal = Number(scheduledHour) * 60 + Number(scheduledMinute) + demoSettings.lateToleranceMinutes;
  const currentTotal = getClockMinutes(now, demoSettings.timezone);
  const weekday = new Date(`${dateKey}T12:00:00`).getDay();
  const computedStatus =
    weekday === 0 || weekday === 6
      ? 'recorded'
      : currentTotal <= scheduledTotal
        ? 'on_time'
        : 'late';

  if (!duplicate) {
    manualMarks.set(markKey, {
      ...current,
      [property]: now.toISOString(),
      ...(input.eventType === 'entry' ? { entryStatus: computedStatus } : {}),
    });
  }

  return {
    employeeName: employee.name,
    eventType: input.eventType,
    recordedAt: current[property] ?? now.toISOString(),
    status:
      input.eventType === 'exit' ? 'recorded' : (current.entryStatus ?? computedStatus),
    duplicate,
    photoSaved: false,
    photoError: 'not_provided',
  };
}

export async function demoGetMonthlyAttendance(month: string): Promise<AttendanceRow[]> {
  await new Promise((resolve) => setTimeout(resolve, 250));
  return buildDemoRows(month);
}

export async function demoGetMonthlySummary(month: string): Promise<MonthlySummary> {
  return calculateSummary(await demoGetMonthlyAttendance(month));
}

export async function demoGetEmployeeDirectory(): Promise<EmployeeDirectoryEntry[]> {
  await new Promise((resolve) => setTimeout(resolve, 150));
  return employees
    .filter((employee) => employee.active)
    .map((employee) => ({ employeeCode: employee.code, fullName: employee.name }))
    .sort((left, right) => left.fullName.localeCompare(right.fullName));
}

export async function demoGetEmployees(): Promise<EmployeeRow[]> {
  await new Promise((resolve) => setTimeout(resolve, 200));
  return [...employees]
    .sort((left, right) => left.name.localeCompare(right.name))
    .map(toEmployeeRow);
}

export async function demoCreateEmployee(input: CreateEmployeeInput): Promise<EmployeeRow> {
  await new Promise((resolve) => setTimeout(resolve, 400));
  const code = input.employeeCode.trim().toUpperCase();

  if (!code || !input.fullName.trim()) {
    throw new Error('El código y el nombre son obligatorios.');
  }
  if (!/^[0-9]{4,8}$/.test(input.pin)) {
    throw new Error('El PIN debe tener entre 4 y 8 dígitos.');
  }
  if (employees.some((item) => item.code === code)) {
    throw new Error('Ya existe un colaborador con ese código.');
  }

  const employee: DemoEmployee = {
    id: code,
    code,
    pin: input.pin,
    name: input.fullName.trim(),
    department: input.department.trim() || null,
    active: true,
    hiredOn: formatDateKey(new Date(), demoSettings.timezone),
    endedOn: null,
  };
  employees.push(employee);
  return toEmployeeRow(employee);
}

export async function demoUpdateEmployee(input: UpdateEmployeeInput): Promise<EmployeeRow> {
  await new Promise((resolve) => setTimeout(resolve, 400));
  const employee = employees.find((item) => item.id === input.id);

  if (!employee) {
    throw new Error('No se encontró el colaborador.');
  }
  if (!input.fullName.trim()) {
    throw new Error('El nombre es obligatorio.');
  }
  if (input.pin && !/^[0-9]{4,8}$/.test(input.pin)) {
    throw new Error('El PIN debe tener entre 4 y 8 dígitos.');
  }

  employee.name = input.fullName.trim();
  employee.department = input.department.trim() || null;
  employee.active = input.active;
  employee.endedOn = input.active ? null : (input.endedOn ?? formatDateKey(new Date(), demoSettings.timezone));
  if (input.pin) {
    employee.pin = input.pin;
  }

  return toEmployeeRow(employee);
}
