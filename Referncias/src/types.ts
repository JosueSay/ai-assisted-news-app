export type AttendanceEventType = 'entry' | 'exit';

export type ArrivalStatus = 'on_time' | 'late' | 'missing' | 'recorded';

export type VerificationMethod = 'pin' | 'device_biometric';

export type AttendancePhotoError =
  | 'not_provided'
  | 'invalid_base64'
  | 'too_large'
  | 'upload_failed'
  | 'duplicate_discarded';

export type AttendanceSettings = {
  entryEnabled: boolean;
  entryTime: string;
  exitEnabled: boolean;
  exitTime: string;
  lateToleranceMinutes: number;
  timezone: string;
};

export type AttendanceRow = {
  id: string;
  employeeId: string;
  employeeCode: string;
  employeeName: string;
  department: string | null;
  date: string;
  entryAt: string | null;
  exitAt: string | null;
  status: ArrivalStatus;
  entryPhotoPath: string | null;
  exitPhotoPath: string | null;
};

export type MonthlySummary = {
  onTime: number;
  late: number;
  missing: number;
  total: number;
};

export type MarkAttendanceInput = {
  employeeCode: string;
  pin: string;
  eventType: AttendanceEventType;
  verificationMethod: VerificationMethod;
  photoBase64?: string;
};

export type MarkAttendanceResult = {
  employeeName: string;
  eventType: AttendanceEventType;
  recordedAt: string;
  status: Exclude<ArrivalStatus, 'missing'> | 'recorded';
  duplicate: boolean;
  photoSaved: boolean;
  photoError: AttendancePhotoError | null;
};

export type AdminIdentity = {
  id: string;
  name: string;
  email: string;
};

export type EmployeeDirectoryEntry = {
  employeeCode: string;
  fullName: string;
};

export type EmployeeRow = {
  id: string;
  employeeCode: string;
  fullName: string;
  department: string | null;
  active: boolean;
  hiredOn: string;
  endedOn: string | null;
};

export type CreateEmployeeInput = {
  employeeCode: string;
  fullName: string;
  department: string;
  pin: string;
};

export type UpdateEmployeeInput = {
  id: string;
  fullName: string;
  department: string;
  active: boolean;
  endedOn?: string | null;
  pin?: string;
};
