import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';

import type { AdminIdentity } from './src/types';
import { AdminDashboardScreen } from './src/screens/AdminDashboardScreen';
import { AdminLoginScreen } from './src/screens/AdminLoginScreen';
import { AttendanceScreen } from './src/screens/AttendanceScreen';
import { signOutAdmin } from './src/services/attendance';

type Route = 'attendance' | 'admin-login' | 'admin-dashboard';

export default function App() {
  const [route, setRoute] = useState<Route>('attendance');
  const [admin, setAdmin] = useState<AdminIdentity | null>(null);

  async function signOut() {
    setAdmin(null);
    setRoute('attendance');

    try {
      await signOutAdmin();
    } catch {
      // The panel is already locked locally. A later login replaces a stale remote session.
    }
  }

  return (
    <>
      <StatusBar style="dark" />
      {route === 'attendance' ? (
        <AttendanceScreen
          onOpenAdmin={() => setRoute('admin-login')}
        />
      ) : null}
      {route === 'admin-login' ? (
        <AdminLoginScreen
          onAuthenticated={(identity) => {
            setAdmin(identity);
            setRoute('admin-dashboard');
          }}
          onBack={() => setRoute('attendance')}
        />
      ) : null}
      {route === 'admin-dashboard' && admin ? (
        <AdminDashboardScreen
          admin={admin}
          onLock={() => void signOut()}
        />
      ) : null}
    </>
  );
}
