import 'react-native-url-polyfill/auto';
import 'expo-sqlite/localStorage/install';

import { createClient } from '@supabase/supabase-js';
import {
  hasUsableSupabaseConfiguration,
  shouldConnectToSupabase,
} from './backendConfig';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL?.trim();
const supabaseKey = process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim();

export const isSupabaseConfigured = hasUsableSupabaseConfiguration(supabaseUrl, supabaseKey);

// La copia compartible nunca abre una conexión por accidente: hacen falta
// credenciales reales y EXPO_PUBLIC_DEMO_MODE=false de forma explícita.
const backendConnectionEnabled = shouldConnectToSupabase(
  supabaseUrl,
  supabaseKey,
  process.env.EXPO_PUBLIC_DEMO_MODE,
);

export const isDemoMode = !backendConnectionEnabled;

export const supabase = backendConnectionEnabled
  ? createClient(supabaseUrl as string, supabaseKey as string, {
      auth: {
        storage: localStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    })
  : null;

export function requireClient() {
  if (!supabase) {
    throw new Error(
      'La base de datos no está conectada. Configura tu propio .env y desactiva el modo demostración.',
    );
  }
  return supabase;
}
