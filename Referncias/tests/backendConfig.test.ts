import { describe, expect, it } from 'vitest';

import {
  hasUsableSupabaseConfiguration,
  shouldConnectToSupabase,
} from '../src/lib/backendConfig';

const exampleUrl = 'https://proyecto-de-prueba.supabase.co';
const exampleKey = 'sb_publishable_abcdefghijklmnopqrstuvwxyz';

describe('backend connection safety', () => {
  it('rejects missing values and documented placeholders', () => {
    expect(hasUsableSupabaseConfiguration(undefined, undefined)).toBe(false);
    expect(
      hasUsableSupabaseConfiguration(
        'https://TU_PROJECT_REF.supabase.co',
        'PEGA_AQUI_LA_PUBLISHABLE_KEY',
      ),
    ).toBe(false);
  });

  it('keeps a valid-looking backend disconnected while demo mode is enabled', () => {
    expect(shouldConnectToSupabase(exampleUrl, exampleKey, 'true')).toBe(false);
  });

  it('requires valid values and an explicit false flag before connecting', () => {
    expect(shouldConnectToSupabase(exampleUrl, exampleKey, undefined)).toBe(false);
    expect(shouldConnectToSupabase(exampleUrl, exampleKey, 'false')).toBe(true);
  });
});
