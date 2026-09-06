import type { AttendancePhotoError } from '../types';

export const MAX_ATTENDANCE_PHOTO_BYTES = 1_900_000;

const BASE64_PATTERN = /^[A-Za-z0-9+/]*={0,2}$/;

export function getBase64Payload(value: string): string | null {
  const trimmed = value.trim();
  const commaIndex = trimmed.indexOf(',');
  const payload = trimmed.startsWith('data:')
    ? commaIndex === -1
      ? ''
      : trimmed.slice(commaIndex + 1)
    : trimmed;

  if (!payload || payload.length % 4 === 1 || !BASE64_PATTERN.test(payload)) {
    return null;
  }

  return payload;
}

export function getBase64DecodedByteLength(value: string): number | null {
  const payload = getBase64Payload(value);
  if (!payload) {
    return null;
  }

  const padding = payload.endsWith('==') ? 2 : payload.endsWith('=') ? 1 : 0;
  return Math.max(0, Math.floor((payload.length * 3) / 4) - padding);
}

const attendancePhotoErrors = new Set<AttendancePhotoError>([
  'not_provided',
  'invalid_base64',
  'too_large',
  'upload_failed',
  'duplicate_discarded',
]);

export function parseAttendancePhotoError(value: unknown): AttendancePhotoError | null {
  return typeof value === 'string' && attendancePhotoErrors.has(value as AttendancePhotoError)
    ? (value as AttendancePhotoError)
    : null;
}

export function getAttendancePhotoWarning(error: AttendancePhotoError | null): string {
  switch (error) {
    case 'not_provided':
      return 'No se pudo tomar la foto de respaldo. Revisa el permiso y espera a que la cámara esté lista.';
    case 'too_large':
      return 'La foto superó el tamaño permitido y no pudo guardarse.';
    case 'invalid_base64':
      return 'La cámara produjo una foto con un formato no válido y no pudo guardarse.';
    case 'duplicate_discarded':
      return 'El marcaje ya existía; la nueva foto no se vinculó al registro anterior.';
    case 'upload_failed':
    default:
      return 'No se pudo guardar la foto de respaldo.';
  }
}
