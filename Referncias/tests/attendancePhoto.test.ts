import { describe, expect, it } from 'vitest';

import {
  getAttendancePhotoWarning,
  getBase64DecodedByteLength,
  getBase64Payload,
  parseAttendancePhotoError,
} from '../src/lib/attendancePhoto';
import {
  decodeBase64Photo,
  shouldKeepUploadedPhoto,
} from '../supabase/functions/_shared/attendance-photo';

function encodeBytes(bytes: number[]): string {
  return btoa(String.fromCharCode(...bytes));
}

describe('attendance photo base64 helpers', () => {
  it('calculates decoded sizes for raw values and data URIs', () => {
    expect(getBase64DecodedByteLength('YQ==')).toBe(1);
    expect(getBase64DecodedByteLength('YWI=')).toBe(2);
    expect(getBase64DecodedByteLength('YWJj')).toBe(3);
    expect(getBase64DecodedByteLength('data:image/jpeg;base64,YWJj')).toBe(3);
  });

  it('rejects malformed payloads before sending them', () => {
    expect(getBase64Payload('')).toBeNull();
    expect(getBase64Payload('%%%')).toBeNull();
    expect(getBase64Payload('data:image/jpeg;base64,%%%')).toBeNull();
  });
});

describe('Edge Function photo decoder', () => {
  const jpegBytes = [0xff, 0xd8, 0xff, 0xe0, 0x00, 0x01, 0xff, 0xd9];
  const jpegBase64 = encodeBytes(jpegBytes);

  it('accepts JPEG bytes as raw base64 or a JPEG data URI', () => {
    const rawResult = decodeBase64Photo(jpegBase64, jpegBytes.length);
    const uriResult = decodeBase64Photo(
      `data:image/jpeg;base64,${jpegBase64}`,
      jpegBytes.length,
    );

    expect(rawResult.ok).toBe(true);
    expect(uriResult.ok).toBe(true);
    if (rawResult.ok) {
      expect(Array.from(rawResult.bytes)).toEqual(jpegBytes);
    }
  });

  it('rejects a JPEG that exceeds the configured byte limit before decoding it', () => {
    expect(decodeBase64Photo(jpegBase64, jpegBytes.length - 1)).toEqual({
      ok: false,
      error: 'too_large',
      decodedBytes: jpegBytes.length,
    });
  });

  it('rejects invalid base64, non-JPEG bytes, and non-JPEG data URIs', () => {
    expect(decodeBase64Photo('%%%')).toEqual({ ok: false, error: 'invalid_base64' });
    expect(decodeBase64Photo(encodeBytes([1, 2, 3]))).toEqual({
      ok: false,
      error: 'invalid_base64',
    });
    expect(decodeBase64Photo(`data:image/png;base64,${jpegBase64}`)).toEqual({
      ok: false,
      error: 'invalid_base64',
    });
  });
});

describe('attendance photo response messages', () => {
  it('accepts only known server error codes', () => {
    expect(parseAttendancePhotoError('too_large')).toBe('too_large');
    expect(parseAttendancePhotoError('anything_else')).toBeNull();
    expect(parseAttendancePhotoError(null)).toBeNull();
  });

  it('provides a useful fallback warning', () => {
    expect(getAttendancePhotoWarning(null)).toContain('guardar la foto');
  });
});

describe('uploaded photo retention', () => {
  it('keeps only a successfully uploaded photo linked to a new attendance record', () => {
    expect(shouldKeepUploadedPhoto(true, { ok: true, duplicate: false })).toBe(true);
    expect(shouldKeepUploadedPhoto(false, { ok: true, duplicate: false })).toBe(false);
    expect(shouldKeepUploadedPhoto(true, { ok: true, duplicate: true })).toBe(false);
    expect(shouldKeepUploadedPhoto(true, { ok: false, duplicate: false })).toBe(false);
    expect(shouldKeepUploadedPhoto(true, null)).toBe(false);
  });
});
