# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Staff attendance mobile app for Colegio Cristiano Fuente del Éxito (Guatemala), built with Expo, React Native, and TypeScript. It ships disconnected and runs on local demo data by default; the Supabase implementation remains as a template for a new owner-provided backend. Ships as an Android APK via EAS Build. UI copy, comments in SQL, and docs are written in Spanish; code identifiers are English.

## Commands

```bash
npm install
npm start              # expo start
npm run android        # expo start --android
npm run web            # expo start --web
npm run typecheck      # tsc --noEmit
npm test               # vitest run
npx vitest run tests/date.test.ts   # run a single test file
npm run build:web      # expo export --platform web
npm run build:apk      # eas build --platform android --profile preview
npx expo-doctor
```

Supabase (requires `npx supabase@latest login` and `link --project-ref ...` first):

```bash
npx supabase@latest db push
npx supabase@latest db reset               # local reset + applies supabase/seed.sql
npx supabase@latest functions deploy register-attendance --no-verify-jwt
```

Local dev without Supabase needs no `.env`; use demo credentials `EMP-001`/PIN `1234` and admin `admin@demo.local`/`Demo1234`. Copy `.env.example` only to customize settings, keeping `EXPO_PUBLIC_DEMO_MODE=true`.

## Architecture

**Client (Expo/React Native, `App.tsx` + `src/`)** is a simple three-route state machine (no navigation library): `attendance` → `admin-login` → `admin-dashboard`, switched via local `useState` in `App.tsx`.

- `src/services/attendance.ts` is the main data-access layer. Every function branches on `isDemoMode` (from `src/lib/supabase.ts`, driven by `EXPO_PUBLIC_DEMO_MODE`): demo mode calls `src/services/demoData.ts` (in-memory fixtures), otherwise it calls Supabase RPCs (`get_public_attendance_settings`, `update_attendance_settings`, `get_monthly_attendance`, `get_active_employee_directory`) or invokes the `register-attendance` Edge Function. `src/services/employees.ts` is a second, parallel service module with the same demo/RPC branching pattern for employee CRUD (`get_employees`, `create_employee`, `update_employee`). Screens never call Supabase directly — they go through one of these service modules.
- The client **never writes attendance rows directly**. All marking goes through the `register-attendance` Edge Function (`supabase/functions/register-attendance/index.ts`), so the APK only needs the publishable key, not table write access.
- `src/lib/supabase.ts` treats `EXPO_PUBLIC_SUPABASE_URL`/`EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` placeholders as unconfigured. It creates a client only when both values are real **and** `EXPO_PUBLIC_DEMO_MODE=false`; otherwise demo mode is forced and `supabase` is `null`.
- `src/lib/date.ts` centralizes date/timezone math and monthly summary calculation (`calculateSummary`) — used by both the real and demo code paths so the UI's notion of on-time/late/missing stays consistent.
- Two device modes (`EXPO_PUBLIC_ATTENDANCE_DEVICE_MODE`): `kiosk` (shared tablet, identity via employee code + PIN only) and `personal` (assigned phone, adds a **local-only** device biometric check via `src/services/biometrics.ts`/`expo-local-authentication` after the PIN). Biometrics never identify *which* employee on a shared device — Android doesn't expose that — so `personal` mode is a second local factor, not remote biometric identity. Do not conflate this with server-side identity verification; see `docs/BIOMETRIA.md` for the full rationale and any future plan to add real 1:1 facial verification.
- `EXPO_PUBLIC_ALLOW_PIN_FALLBACK` (checked in `AttendanceScreen.tsx`, always effectively `true` in demo mode) lets a mark succeed on PIN alone when device biometrics are unavailable/unenrolled; `EXPO_PUBLIC_REQUIRE_ADMIN_BIOMETRIC` (checked in `AdminLoginScreen.tsx`) adds an optional device-biometric second factor after admin email/password login. Both are local-only checks, same caveat as above.

**Backend (`supabase/`)**:

- `supabase/migrations/` is applied in filename order and is the source of truth for business rules — read it before changing attendance/settings/employee behavior, not the TypeScript types. `202608220001_initial_attendance.sql` has the whole base schema: tables, RLS policies, and the core SQL functions (`get_public_attendance_settings`, `update_attendance_settings`, `get_monthly_attendance`, attendance-marking logic). `202608230001_employee_management.sql` adds admin-only employee CRUD (`get_employees`, `create_employee`, `update_employee`), each writing to `private.audit_log` with `pin_hash` stripped from the logged payload. `202608230002_public_employee_directory.sql` adds `get_active_employee_directory`, a public (`anon`) RPC exposing only active employees' code + name, used to populate the marking screen's `PersonSelect` picker without exposing PINs or inactive staff.
- `supabase/functions/register-attendance/index.ts` is the only write path for attendance events. It authenticates PIN with `pgcrypto`/bcrypt server-side, computes status using `clock_timestamp()` in the `America/Guatemala` timezone (phone clock is never trusted), and enforces one entry + one exit per employee per day (retries return the existing mark, not an error).
- Rate limiting: 5 failed attempts from the same origin temporarily blocks that flow, plus a second cumulative limit keyed by employee code to prevent bypass by rotating origin.
- RLS scopes admin access to their own organization only; employee CRUD functions independently re-check `profiles.role = 'admin'` inside the function body (`security definer`) rather than relying on RLS alone.
- Absences are derived, not stored directly: a working day with entry enabled and no arrival counts as missing, except the current day with zero marks (skipped) — but an existing exit with no entry does count as missing when entry was required. Weekend/off-schedule marks display but never count toward absences or the punctuality summary.
- Schedule changes are versioned with an audit entry; the operational on/off switch takes effect immediately, but a new absence rule only applies starting the next day, to avoid retroactively judging the current day.

## Security constraints (do not relax without explicit instruction)

- Never put `service_role`, any Supabase secret key, or `OPENAI_API_KEY` into `EXPO_PUBLIC_*` variables — those ship inside the client bundle. Only the publishable key belongs there.
- `.env`, `.mcp.json`, and `supabase/.temp/` are local-only and gitignored. Never commit service links or generated project metadata. Environment variables for real builds must be set via `eas-cli env:set` per environment (`preview`, `production` — see `eas.json` profiles).
- PINs are stored only as bcrypt hashes (`pgcrypto`), never plaintext.
- If facial recognition is ever added: no stored attendance photos, encrypted biometric templates, explicit consent, and liveness detection are required (see `docs/BIOMETRIA.md`).

## Testing

Vitest (`tests/*.test.ts`) covers pure logic only: `src/lib/date.ts` (timezone/summary math) and `src/services/demoData.ts` (demo-mode behavior). There is no test coverage for Supabase RPCs/Edge Function or React components — verify those manually via demo mode or against a real Supabase project.
