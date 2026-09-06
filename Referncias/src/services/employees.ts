import { isDemoMode, requireClient } from '../lib/supabase';
import type { CreateEmployeeInput, EmployeeRow, UpdateEmployeeInput } from '../types';
import {
  demoCreateEmployee,
  demoGetEmployees,
  demoUpdateEmployee,
} from './demoData';

type EmployeeRpcRow = {
  id: string;
  employee_code: string;
  full_name: string;
  department: string | null;
  active: boolean;
  hired_on: string;
  ended_on: string | null;
};

function mapEmployee(row: EmployeeRpcRow): EmployeeRow {
  return {
    id: row.id,
    employeeCode: row.employee_code,
    fullName: row.full_name,
    department: row.department,
    active: row.active,
    hiredOn: row.hired_on,
    endedOn: row.ended_on,
  };
}

function firstValue<T>(value: T | T[] | null): T | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }
  return value;
}

export async function getEmployees(): Promise<EmployeeRow[]> {
  if (isDemoMode) {
    return demoGetEmployees();
  }

  const client = requireClient();
  const { data, error } = await client.rpc('get_employees');
  if (error) {
    throw new Error(error.message);
  }

  return ((data ?? []) as EmployeeRpcRow[]).map(mapEmployee);
}

export async function createEmployee(input: CreateEmployeeInput): Promise<EmployeeRow> {
  if (isDemoMode) {
    return demoCreateEmployee(input);
  }

  const client = requireClient();
  const { data, error } = await client.rpc('create_employee', {
    p_employee_code: input.employeeCode.trim().toUpperCase(),
    p_full_name: input.fullName.trim(),
    p_department: input.department.trim(),
    p_pin: input.pin,
  });

  if (error) {
    throw new Error(error.message);
  }

  const row = firstValue(data as EmployeeRpcRow | EmployeeRpcRow[] | null);
  if (!row) {
    throw new Error('No se pudo registrar el colaborador.');
  }

  return mapEmployee(row);
}

export async function updateEmployee(input: UpdateEmployeeInput): Promise<EmployeeRow> {
  if (isDemoMode) {
    return demoUpdateEmployee(input);
  }

  const client = requireClient();
  const { data, error } = await client.rpc('update_employee', {
    p_employee_id: input.id,
    p_full_name: input.fullName.trim(),
    p_department: input.department.trim(),
    p_active: input.active,
    p_ended_on: input.endedOn ?? null,
    p_pin: input.pin || null,
  });

  if (error) {
    throw new Error(error.message);
  }

  const row = firstValue(data as EmployeeRpcRow | EmployeeRpcRow[] | null);
  if (!row) {
    throw new Error('No se pudo actualizar el colaborador.');
  }

  return mapEmployee(row);
}
