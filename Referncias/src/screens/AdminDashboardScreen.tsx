import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Modal,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';

import { AppButton } from '../components/AppButton';
import { AppField } from '../components/AppField';
import { Brand } from '../components/Brand';
import { InlineNotice } from '../components/InlineNotice';
import { MonthSelector } from '../components/MonthSelector';
import { StatusBadge } from '../components/StatusBadge';
import {
  calculateSummary,
  formatDateKey,
  formatRecordedTime,
  formatShortDate,
  isValidTime,
  toMonthKey,
} from '../lib/date';
import { colors, radii, shadows } from '../theme';
import type {
  AdminIdentity,
  AttendanceEventType,
  AttendanceRow,
  AttendanceSettings,
  EmployeeRow,
} from '../types';
import {
  deleteAttendancePhoto,
  getAttendancePhotoUrl,
  getAttendanceSettings,
  getMonthlyAttendance,
  updateAttendanceSettings,
} from '../services/attendance';
import { createEmployee, getEmployees, updateEmployee } from '../services/employees';

type AdminModule = 'attendance' | 'summary' | 'schedule' | 'personal';

type AdminDashboardScreenProps = {
  admin: AdminIdentity;
  onLock: () => void;
};

const modules: Array<{ key: AdminModule; label: string; caption: string; icon: string }> = [
  { key: 'attendance', label: 'Asistencia', caption: 'Detalle mensual', icon: '≡' },
  { key: 'summary', label: 'Consolidado', caption: 'Puntualidad y faltas', icon: 'Σ' },
  { key: 'schedule', label: 'Horarios', caption: 'Entrada y salida', icon: '◷' },
  { key: 'personal', label: 'Personal', caption: 'Registrar colaboradores', icon: '⊕' },
];

export function AdminDashboardScreen({
  admin,
  onLock,
}: AdminDashboardScreenProps) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 880;
  const [activeModule, setActiveModule] = useState<AdminModule>('attendance');
  const [month, setMonth] = useState(() => toMonthKey(new Date()));
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [settings, setSettings] = useState<AttendanceSettings | null>(null);
  const [loadingRows, setLoadingRows] = useState(true);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const rowRequestId = useRef(0);
  const hasInitializedOrganizationMonth = useRef(false);

  async function loadRows(targetMonth = month) {
    const requestId = rowRequestId.current + 1;
    rowRequestId.current = requestId;
    setLoadingRows(true);
    setDataError(null);
    setRows([]);
    try {
      const nextRows = await getMonthlyAttendance(targetMonth);
      if (requestId === rowRequestId.current) {
        setRows(nextRows);
      }
    } catch (error) {
      if (requestId === rowRequestId.current) {
        setDataError(error instanceof Error ? error.message : 'No se pudo cargar la asistencia.');
      }
    } finally {
      if (requestId === rowRequestId.current) {
        setLoadingRows(false);
      }
    }
  }

  useEffect(() => {
    void loadRows(month);
  }, [month]);

  async function loadSettings() {
    setSettingsError(null);
    setLoadingSettings(true);
    try {
      const nextSettings = await getAttendanceSettings();
      setSettings(nextSettings);
      if (!hasInitializedOrganizationMonth.current) {
        hasInitializedOrganizationMonth.current = true;
        setMonth(`${formatDateKey(new Date(), nextSettings.timezone).slice(0, 7)}-01`);
      }
    } catch (error) {
      setSettingsError(error instanceof Error ? error.message : 'No se pudo cargar el horario.');
    } finally {
      setLoadingSettings(false);
    }
  }

  useEffect(() => {
    void loadSettings();
  }, []);

  const navigation = (
    <View style={[styles.navigation, isTablet && styles.navigationTablet]}>
      {isTablet ? <Brand inverted /> : null}
      <View style={[styles.navItems, !isTablet && styles.navItemsMobile]}>
        {modules.map((item) => (
          <Pressable
            accessibilityRole="tab"
            accessibilityState={{ selected: activeModule === item.key }}
            key={item.key}
            onPress={() => setActiveModule(item.key)}
            style={({ pressed }) => [
              styles.navItem,
              !isTablet && styles.navItemMobile,
              activeModule === item.key && styles.navItemActive,
              pressed && styles.navItemPressed,
            ]}
          >
            <View style={[styles.navIcon, activeModule === item.key && styles.navIconActive]}>
              <Text style={[styles.navIconText, activeModule === item.key && styles.navIconTextActive]}>
                {item.icon}
              </Text>
            </View>
            <View style={!isTablet && styles.navTextMobile}>
              <Text
                style={[
                  styles.navLabel,
                  isTablet && styles.navLabelTablet,
                  activeModule === item.key && styles.navLabelActive,
                ]}
              >
                {item.label}
              </Text>
              {isTablet ? <Text style={styles.navCaption}>{item.caption}</Text> : null}
            </View>
          </Pressable>
        ))}
      </View>
      {isTablet ? (
        <View style={styles.sidebarBottom}>
          <Text numberOfLines={1} style={styles.sidebarName}>{admin.name}</Text>
          <Text numberOfLines={1} style={styles.sidebarEmail}>{admin.email}</Text>
          <AppButton onPress={onLock} variant="secondary" style={styles.sidebarButton}>
            Bloquear y volver
          </AppButton>
        </View>
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={[styles.shell, isTablet && styles.shellTablet]}>
        {isTablet ? navigation : null}
        <View style={styles.contentShell}>
          <View style={styles.topbar}>
            {!isTablet ? <Brand compact={width < 520} /> : null}
            <View style={styles.topbarActions}>
              {!isTablet ? (
                <AppButton onPress={onLock} style={styles.topbarButton} variant="danger">
                  Bloquear
                </AppButton>
              ) : (
                <View>
                  <Text style={styles.welcome}>Bienvenido, {admin.name}</Text>
                  <Text style={styles.secureSession}>Sesión administrativa segura</Text>
                </View>
              )}
            </View>
          </View>
          {!isTablet ? navigation : null}

          <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
            {dataError && activeModule !== 'schedule' ? (
              <InlineNotice message={dataError} tone="error" />
            ) : null}

            {activeModule === 'attendance' ? (
              <AttendanceModule
                loading={loadingRows}
                month={month}
                onMonthChange={setMonth}
                onRefresh={() => void loadRows()}
                rows={rows}
                timezone={settings?.timezone}
              />
            ) : null}

            {activeModule === 'summary' ? (
              <SummaryModule
                loading={loadingRows}
                month={month}
                onMonthChange={setMonth}
                rows={rows}
              />
            ) : null}

            {activeModule === 'schedule' ? (
              <ScheduleModule
                loadError={settingsError}
                loading={loadingSettings}
                onSaved={setSettings}
                onRetry={() => void loadSettings()}
                settings={settings}
              />
            ) : null}

            {activeModule === 'personal' ? <PersonalModule /> : null}
          </ScrollView>
        </View>
      </View>
    </SafeAreaView>
  );
}

type AttendanceModuleProps = {
  month: string;
  rows: AttendanceRow[];
  loading: boolean;
  onMonthChange: (month: string) => void;
  onRefresh: () => void;
  timezone?: string;
};

function AttendanceModule({
  month,
  rows,
  loading,
  onMonthChange,
  onRefresh,
  timezone,
}: AttendanceModuleProps) {
  const { width } = useWindowDimensions();
  const showTable = width >= 760;
  const pageSize = 75;
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const visibleRows = rows.slice(page * pageSize, (page + 1) * pageSize);
  const [viewingPhoto, setViewingPhoto] = useState<{
    employeeId: string;
    date: string;
    eventType: AttendanceEventType;
    photoPath: string;
    employeeName: string;
  } | null>(null);

  useEffect(() => {
    setPage(0);
  }, [month]);

  useEffect(() => {
    setPage((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  return (
    <View style={styles.module}>
      <ModuleHeading
        eyebrow="CONTROL MENSUAL"
        title="Registro de asistencia"
        description="Entradas, salidas y estado de puntualidad por colaborador."
      />
      <View style={styles.toolbar}>
        <MonthSelector onChange={onMonthChange} value={month} />
        <AppButton onPress={onRefresh} style={styles.refreshButton} variant="ghost">
          Actualizar
        </AppButton>
      </View>

      {loading ? (
        <LoadingBlock label="Cargando registros…" />
      ) : rows.length === 0 ? (
        <EmptyState message="No hay días de asistencia para este mes." />
      ) : showTable ? (
        <View style={styles.tableCard}>
          <View style={styles.tableHeader}>
            <Text style={[styles.tableHeaderText, styles.employeeColumn]}>Colaborador</Text>
            <Text style={[styles.tableHeaderText, styles.dateColumn]}>Fecha</Text>
            <Text style={[styles.tableHeaderText, styles.timeColumn]}>Entrada</Text>
            <Text style={[styles.tableHeaderText, styles.timeColumn]}>Salida</Text>
            <Text style={[styles.tableHeaderText, styles.statusColumn]}>Estado</Text>
          </View>
          {visibleRows.map((row) => (
            <View key={row.id} style={styles.tableRow}>
              <View style={styles.employeeColumn}>
                <Text numberOfLines={1} style={styles.employeeName}>{row.employeeName}</Text>
                <Text numberOfLines={1} style={styles.employeeMeta}>
                  {row.employeeCode}{row.department ? ` · ${row.department}` : ''}
                </Text>
              </View>
              <Text style={[styles.cellText, styles.dateColumn]}>{formatShortDate(row.date)}</Text>
              <View style={styles.timeColumn}>
                <Text style={styles.cellStrong}>{formatRecordedTime(row.entryAt, timezone)}</Text>
                {row.entryPhotoPath ? (
                  <PhotoButton
                    onPress={() =>
                      setViewingPhoto({
                        employeeId: row.employeeId,
                        date: row.date,
                        eventType: 'entry',
                        photoPath: row.entryPhotoPath as string,
                        employeeName: row.employeeName,
                      })
                    }
                  />
                ) : null}
              </View>
              <View style={styles.timeColumn}>
                <Text style={styles.cellStrong}>{formatRecordedTime(row.exitAt, timezone)}</Text>
                {row.exitPhotoPath ? (
                  <PhotoButton
                    onPress={() =>
                      setViewingPhoto({
                        employeeId: row.employeeId,
                        date: row.date,
                        eventType: 'exit',
                        photoPath: row.exitPhotoPath as string,
                        employeeName: row.employeeName,
                      })
                    }
                  />
                ) : null}
              </View>
              <View style={styles.statusColumn}>
                <StatusBadge status={row.status} />
              </View>
            </View>
          ))}
        </View>
      ) : (
        <View style={styles.mobileList}>
          {visibleRows.map((row) => (
            <View key={row.id} style={styles.mobileRecord}>
              <View style={styles.mobileRecordTop}>
                <View style={styles.mobileRecordIdentity}>
                  <Text style={styles.employeeName}>{row.employeeName}</Text>
                  <Text style={styles.employeeMeta}>{row.employeeCode} · {formatShortDate(row.date)}</Text>
                </View>
                <StatusBadge status={row.status} />
              </View>
              <View style={styles.mobileTimes}>
                <TimeValue
                  label="Entrada"
                  onViewPhoto={
                    row.entryPhotoPath
                      ? () =>
                          setViewingPhoto({
                            employeeId: row.employeeId,
                            date: row.date,
                            eventType: 'entry',
                            photoPath: row.entryPhotoPath as string,
                            employeeName: row.employeeName,
                          })
                      : undefined
                  }
                  value={formatRecordedTime(row.entryAt, timezone)}
                />
                <TimeValue
                  label="Salida"
                  onViewPhoto={
                    row.exitPhotoPath
                      ? () =>
                          setViewingPhoto({
                            employeeId: row.employeeId,
                            date: row.date,
                            eventType: 'exit',
                            photoPath: row.exitPhotoPath as string,
                            employeeName: row.employeeName,
                          })
                      : undefined
                  }
                  value={formatRecordedTime(row.exitAt, timezone)}
                />
              </View>
            </View>
          ))}
        </View>
      )}

      <PhotoViewerModal
        info={viewingPhoto}
        onClose={() => setViewingPhoto(null)}
        onDeleted={() => {
          setViewingPhoto(null);
          onRefresh();
        }}
      />

      {!loading && rows.length > pageSize ? (
        <View style={styles.paginationBar}>
          <Text style={styles.paginationLabel}>
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, rows.length)} de {rows.length}
          </Text>
          <View style={styles.paginationActions}>
            <AppButton
              disabled={page === 0}
              onPress={() => setPage((current) => Math.max(0, current - 1))}
              style={styles.paginationButton}
              variant="ghost"
            >
              Anterior
            </AppButton>
            <Text style={styles.pageNumber}>{page + 1} / {pageCount}</Text>
            <AppButton
              disabled={page >= pageCount - 1}
              onPress={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
              style={styles.paginationButton}
              variant="ghost"
            >
              Siguiente
            </AppButton>
          </View>
        </View>
      ) : null}
    </View>
  );
}

type SummaryModuleProps = {
  month: string;
  rows: AttendanceRow[];
  loading: boolean;
  onMonthChange: (month: string) => void;
};

function SummaryModule({ month, rows, loading, onMonthChange }: SummaryModuleProps) {
  const summary = useMemo(() => calculateSummary(rows), [rows]);
  const byEmployee = useMemo(() => {
    const aggregates = new Map<
      string,
      { code: string; name: string; onTime: number; late: number; missing: number; total: number }
    >();

    for (const row of rows) {
      const current = aggregates.get(row.employeeCode) ?? {
        code: row.employeeCode,
        name: row.employeeName,
        onTime: 0,
        late: 0,
        missing: 0,
        total: 0,
      };
      current.total += 1;
      if (row.status === 'on_time') current.onTime += 1;
      if (row.status === 'late') current.late += 1;
      if (row.status === 'missing') current.missing += 1;
      aggregates.set(row.employeeCode, current);
    }

    return [...aggregates.values()].sort((left, right) => left.name.localeCompare(right.name));
  }, [rows]);

  const evaluated = summary.onTime + summary.late + summary.missing;
  const punctuality = evaluated > 0 ? Math.round((summary.onTime / evaluated) * 100) : 0;

  return (
    <View style={styles.module}>
      <ModuleHeading
        eyebrow="CONSOLIDADO"
        title="Resumen de puntualidad"
        description="Totales de llegadas a tiempo, llegadas tarde y faltas del mes."
      />
      <View style={styles.toolbar}>
        <MonthSelector onChange={onMonthChange} value={month} />
      </View>

      {loading ? (
        <LoadingBlock label="Calculando consolidado…" />
      ) : (
        <>
          <View style={styles.summaryGrid}>
            <SummaryCard label="A tiempo" value={summary.onTime} tone="success" />
            <SummaryCard label="Tarde" value={summary.late} tone="warning" />
            <SummaryCard label="Falta" value={summary.missing} tone="danger" />
            <SummaryCard label="Puntualidad" suffix="%" value={punctuality} tone="primary" />
          </View>

          <View style={styles.breakdownCard}>
            <View style={styles.breakdownHeader}>
              <View>
                <Text style={styles.cardTitle}>Detalle por colaborador</Text>
                <Text style={styles.cardDescription}>Días laborables ya evaluados en el período.</Text>
              </View>
              <Text style={styles.evaluatedLabel}>{evaluated} registros</Text>
            </View>
            {byEmployee.length === 0 ? (
              <EmptyState message="No hay información consolidada para este mes." />
            ) : (
              byEmployee.map((employee) => (
                <View key={employee.code} style={styles.employeeSummaryRow}>
                  <View style={styles.summaryIdentity}>
                    <View style={styles.avatar}>
                      <Text style={styles.avatarText}>{initials(employee.name)}</Text>
                    </View>
                    <View>
                      <Text style={styles.employeeName}>{employee.name}</Text>
                      <Text style={styles.employeeMeta}>{employee.code}</Text>
                    </View>
                  </View>
                  <View style={styles.employeeMetrics}>
                    <MiniMetric label="A tiempo" tone="success" value={employee.onTime} />
                    <MiniMetric label="Tarde" tone="warning" value={employee.late} />
                    <MiniMetric label="Falta" tone="danger" value={employee.missing} />
                  </View>
                </View>
              ))
            )}
          </View>
        </>
      )}
    </View>
  );
}

type ScheduleModuleProps = {
  settings: AttendanceSettings | null;
  loading: boolean;
  loadError: string | null;
  onSaved: (settings: AttendanceSettings) => void;
  onRetry: () => void;
};

function ScheduleModule({ settings, loading, loadError, onSaved, onRetry }: ScheduleModuleProps) {
  const [draft, setDraft] = useState<AttendanceSettings | null>(settings);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  function changeDraft(patch: Partial<AttendanceSettings>) {
    if (!draft) return;
    setSaved(false);
    setError(null);
    setDraft({ ...draft, ...patch });
  }

  async function save() {
    if (!draft || saving) return;
    if (!isValidTime(draft.entryTime)) {
      setError('La hora de entrada debe tener el formato HH:mm.');
      return;
    }
    if (!isValidTime(draft.exitTime)) {
      setError('La hora de salida debe tener el formato HH:mm.');
      return;
    }
    if (
      !Number.isInteger(draft.lateToleranceMinutes) ||
      draft.lateToleranceMinutes < 0 ||
      draft.lateToleranceMinutes > 120
    ) {
      setError('La tolerancia debe ser un número entre 0 y 120 minutos.');
      return;
    }

    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await updateAttendanceSettings(draft);
      setDraft(updated);
      onSaved(updated);
      setSaved(true);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'No se pudo guardar el horario.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={styles.module}>
      <ModuleHeading
        eyebrow="CONFIGURACIÓN"
        title="Horarios de marcaje"
        description="Activa cada marcaje y define la hora que utilizará el servidor para calcular la puntualidad."
      />

      {loading ? (
        <LoadingBlock label="Cargando configuración…" />
      ) : !draft ? (
        <View style={styles.loadErrorCard}>
          <InlineNotice
            message={loadError ?? 'No se encontró una configuración de horarios.'}
            tone="error"
          />
          <AppButton onPress={onRetry} variant="ghost">
            Reintentar
          </AppButton>
        </View>
      ) : (
        <View style={styles.settingsLayout}>
          <View style={styles.settingsCard}>
            {error ? <InlineNotice message={error} tone="error" /> : null}
            {saved ? (
              <InlineNotice
                message="El horario operativo ya cambió. La nueva regla de faltas se aplicará desde mañana."
                tone="success"
              />
            ) : null}

            <ScheduleToggle
              description="Permite al personal registrar la llegada y calcula si fue a tiempo o tarde."
              enabled={draft.entryEnabled}
              label="Hora de entrada"
              onEnabledChange={(entryEnabled) => changeDraft({ entryEnabled })}
              onTimeChange={(entryTime) => changeDraft({ entryTime })}
              time={draft.entryTime}
            />
            <View style={styles.settingsDivider} />
            <ScheduleToggle
              description="Permite registrar el final de la jornada."
              enabled={draft.exitEnabled}
              label="Hora de salida"
              onEnabledChange={(exitEnabled) => changeDraft({ exitEnabled })}
              onTimeChange={(exitTime) => changeDraft({ exitTime })}
              time={draft.exitTime}
            />
            <View style={styles.settingsDivider} />
            <View style={styles.toleranceRow}>
              <View style={styles.settingCopy}>
                <Text style={styles.settingTitle}>Tolerancia de llegada</Text>
                <Text style={styles.settingDescription}>
                  Minutos adicionales antes de clasificar una entrada como tarde.
                </Text>
              </View>
              <View style={styles.minutesInputWrap}>
                <TextInput
                  accessibilityLabel="Minutos de tolerancia"
                  keyboardType="number-pad"
                  maxLength={3}
                  onChangeText={(value) =>
                    changeDraft({ lateToleranceMinutes: Number(value.replace(/\D/g, '') || 0) })
                  }
                  style={styles.minutesInput}
                  value={String(draft.lateToleranceMinutes)}
                />
                <Text style={styles.minutesLabel}>min</Text>
              </View>
            </View>

            <AppButton fullWidth loading={saving} onPress={() => void save()}>
              Guardar configuración
            </AppButton>
          </View>

          <View style={styles.previewCard}>
            <Text style={styles.previewEyebrow}>VISTA PREVIA</Text>
            <Text style={styles.previewTitle}>Jornada configurada</Text>
            <View style={styles.timeline}>
              <TimelinePoint
                active={draft.entryEnabled}
                label="Entrada"
                time={draft.entryTime}
              />
              <View style={styles.timelineLine} />
              <TimelinePoint active={draft.exitEnabled} label="Salida" time={draft.exitTime} />
            </View>
            <InlineNotice
              message={`Zona horaria: ${draft.timezone}. Las marcas usan la hora de Supabase, no la del teléfono.`}
              tone="info"
            />
          </View>
        </View>
      )}
    </View>
  );
}

type EmployeeDraft = {
  employeeCode: string;
  fullName: string;
  department: string;
  pin: string;
  active: boolean;
};

const emptyDraft: EmployeeDraft = {
  employeeCode: '',
  fullName: '',
  department: '',
  pin: '',
  active: true,
};

function PersonalModule() {
  const { width } = useWindowDimensions();
  const showTable = width >= 760;
  const [employees, setEmployees] = useState<EmployeeRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<'closed' | 'create' | string>('closed');
  const [draft, setDraft] = useState<EmployeeDraft>(emptyDraft);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function loadEmployees() {
    setLoading(true);
    setLoadError(null);
    try {
      setEmployees(await getEmployees());
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'No se pudo cargar el personal.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadEmployees();
  }, []);

  function openCreateForm() {
    setDraft(emptyDraft);
    setFormError(null);
    setFormMode('create');
  }

  function openEditForm(employee: EmployeeRow) {
    setDraft({
      employeeCode: employee.employeeCode,
      fullName: employee.fullName,
      department: employee.department ?? '',
      pin: '',
      active: employee.active,
    });
    setFormError(null);
    setFormMode(employee.id);
  }

  function closeForm() {
    setFormMode('closed');
    setFormError(null);
  }

  async function submitCreate() {
    if (saving) return;
    if (!draft.employeeCode.trim() || !draft.fullName.trim()) {
      setFormError('El código y el nombre son obligatorios.');
      return;
    }
    if (!/^[0-9]{4,8}$/.test(draft.pin)) {
      setFormError('El PIN debe tener entre 4 y 8 dígitos.');
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      const created = await createEmployee({
        employeeCode: draft.employeeCode,
        fullName: draft.fullName,
        department: draft.department,
        pin: draft.pin,
      });
      setEmployees((current) => [...current, created].sort((left, right) => left.fullName.localeCompare(right.fullName)));
      closeForm();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'No se pudo registrar el colaborador.');
    } finally {
      setSaving(false);
    }
  }

  async function submitEdit(employeeId: string) {
    if (saving) return;
    if (!draft.fullName.trim()) {
      setFormError('El nombre es obligatorio.');
      return;
    }
    if (draft.pin && !/^[0-9]{4,8}$/.test(draft.pin)) {
      setFormError('El PIN debe tener entre 4 y 8 dígitos.');
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      const updated = await updateEmployee({
        id: employeeId,
        fullName: draft.fullName,
        department: draft.department,
        active: draft.active,
        pin: draft.pin || undefined,
      });
      setEmployees((current) =>
        current
          .map((employee) => (employee.id === employeeId ? updated : employee))
          .sort((left, right) => left.fullName.localeCompare(right.fullName)),
      );
      closeForm();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'No se pudo actualizar el colaborador.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={styles.module}>
      <ModuleHeading
        eyebrow="PERSONAL"
        title="Colaboradores"
        description="Registra al personal, su código y PIN de marcaje. El PIN nunca se guarda en texto plano."
      />

      <View style={styles.toolbar}>
        <Text style={styles.paginationLabel}>
          {loading ? 'Cargando…' : `${employees.length} colaborador${employees.length === 1 ? '' : 'es'}`}
        </Text>
        <AppButton onPress={openCreateForm} style={styles.refreshButton} variant="primary">
          Agregar colaborador
        </AppButton>
      </View>

      {formMode === 'create' ? (
        <View style={styles.settingsCard}>
          {formError ? <InlineNotice message={formError} tone="error" /> : null}
          <AppField
            autoCapitalize="characters"
            label="Código"
            onChangeText={(value) => setDraft((current) => ({ ...current, employeeCode: value }))}
            placeholder="EMP-004"
            value={draft.employeeCode}
          />
          <AppField
            label="Nombre completo"
            onChangeText={(value) => setDraft((current) => ({ ...current, fullName: value }))}
            placeholder="Nombre y apellido"
            value={draft.fullName}
          />
          <AppField
            label="Departamento"
            onChangeText={(value) => setDraft((current) => ({ ...current, department: value }))}
            placeholder="Opcional"
            value={draft.department}
          />
          <AppField
            hint="Entre 4 y 8 dígitos. Se guarda cifrado, nunca en texto plano."
            keyboardType="number-pad"
            label="PIN"
            maxLength={8}
            onChangeText={(value) => setDraft((current) => ({ ...current, pin: value.replace(/\D/g, '') }))}
            secureTextEntry
            value={draft.pin}
          />
          <View style={styles.formActions}>
            <AppButton onPress={closeForm} variant="ghost">
              Cancelar
            </AppButton>
            <AppButton loading={saving} onPress={() => void submitCreate()}>
              Guardar colaborador
            </AppButton>
          </View>
        </View>
      ) : null}

      {loading ? (
        <LoadingBlock label="Cargando personal…" />
      ) : loadError ? (
        <View style={styles.loadErrorCard}>
          <InlineNotice message={loadError} tone="error" />
          <AppButton onPress={() => void loadEmployees()} variant="ghost">
            Reintentar
          </AppButton>
        </View>
      ) : employees.length === 0 ? (
        <EmptyState message="Todavía no hay colaboradores registrados." />
      ) : (
        <View style={styles.tableCard}>
          {showTable ? (
            <View style={styles.tableHeader}>
              <Text style={[styles.tableHeaderText, styles.employeeColumn]}>Colaborador</Text>
              <Text style={[styles.tableHeaderText, styles.dateColumn]}>Departamento</Text>
              <Text style={[styles.tableHeaderText, styles.timeColumn]}>Estado</Text>
              <Text style={[styles.tableHeaderText, styles.statusColumn]}>Acción</Text>
            </View>
          ) : null}

          {employees.map((employee) => (
            <View key={employee.id}>
              <View style={[styles.tableRow, !showTable && styles.mobileEmployeeRow]}>
                <View style={styles.employeeColumn}>
                  <Text numberOfLines={1} style={styles.employeeName}>{employee.fullName}</Text>
                  <Text numberOfLines={1} style={styles.employeeMeta}>{employee.employeeCode}</Text>
                </View>
                <Text style={[styles.cellText, styles.dateColumn]}>{employee.department ?? '—'}</Text>
                <View style={styles.timeColumn}>
                  <View
                    style={[
                      styles.employeeStatusBadge,
                      { backgroundColor: employee.active ? colors.successSoft : colors.dangerSoft },
                    ]}
                  >
                    <Text
                      style={[
                        styles.employeeStatusText,
                        { color: employee.active ? colors.success : colors.danger },
                      ]}
                    >
                      {employee.active ? 'Activo' : 'Inactivo'}
                    </Text>
                  </View>
                </View>
                <View style={styles.statusColumn}>
                  <AppButton
                    onPress={() => (formMode === employee.id ? closeForm() : openEditForm(employee))}
                    style={styles.editButton}
                    variant="ghost"
                  >
                    {formMode === employee.id ? 'Cerrar' : 'Editar'}
                  </AppButton>
                </View>
              </View>

              {formMode === employee.id ? (
                <View style={styles.editPanel}>
                  {formError ? <InlineNotice message={formError} tone="error" /> : null}
                  <AppField
                    label="Nombre completo"
                    onChangeText={(value) => setDraft((current) => ({ ...current, fullName: value }))}
                    value={draft.fullName}
                  />
                  <AppField
                    label="Departamento"
                    onChangeText={(value) => setDraft((current) => ({ ...current, department: value }))}
                    placeholder="Opcional"
                    value={draft.department}
                  />
                  <AppField
                    hint="Déjalo vacío para conservar el PIN actual."
                    keyboardType="number-pad"
                    label="Nuevo PIN (opcional)"
                    maxLength={8}
                    onChangeText={(value) => setDraft((current) => ({ ...current, pin: value.replace(/\D/g, '') }))}
                    secureTextEntry
                    value={draft.pin}
                  />
                  <View style={styles.switchTitleRow}>
                    <Text style={styles.settingTitle}>Colaborador activo</Text>
                    <Switch
                      onValueChange={(active) => setDraft((current) => ({ ...current, active }))}
                      thumbColor={colors.white}
                      trackColor={{ false: colors.border, true: colors.success }}
                      value={draft.active}
                    />
                  </View>
                  <View style={styles.formActions}>
                    <AppButton onPress={closeForm} variant="ghost">
                      Cancelar
                    </AppButton>
                    <AppButton loading={saving} onPress={() => void submitEdit(employee.id)}>
                      Guardar cambios
                    </AppButton>
                  </View>
                </View>
              ) : null}
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function ModuleHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <View style={styles.moduleHeading}>
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text style={styles.moduleTitle}>{title}</Text>
      <Text style={styles.moduleDescription}>{description}</Text>
    </View>
  );
}

function LoadingBlock({ label }: { label: string }) {
  return (
    <View style={styles.loadingBlock}>
      <ActivityIndicator color={colors.primary} size="large" />
      <Text style={styles.loadingLabel}>{label}</Text>
    </View>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <View style={styles.emptyState}>
      <Text style={styles.emptyMark}>—</Text>
      <Text style={styles.emptyText}>{message}</Text>
    </View>
  );
}

function TimeValue({
  label,
  value,
  onViewPhoto,
}: {
  label: string;
  value: string;
  onViewPhoto?: () => void;
}) {
  return (
    <View>
      <Text style={styles.timeLabel}>{label}</Text>
      <Text style={styles.timeValue}>{value}</Text>
      {onViewPhoto ? <PhotoButton onPress={onViewPhoto} /> : null}
    </View>
  );
}

function PhotoButton({ onPress }: { onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" hitSlop={6} onPress={onPress} style={styles.photoButton}>
      <Text style={styles.photoButtonIcon}>◎</Text>
      <Text style={styles.photoButtonText}>Ver foto</Text>
    </Pressable>
  );
}

type PhotoViewerInfo = {
  employeeId: string;
  date: string;
  eventType: AttendanceEventType;
  photoPath: string;
  employeeName: string;
};

function PhotoViewerModal({
  info,
  onClose,
  onDeleted,
}: {
  info: PhotoViewerInfo | null;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!info) {
      setPhotoUrl(null);
      setError(null);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    getAttendancePhotoUrl(info.photoPath)
      .then((url) => {
        if (active) setPhotoUrl(url);
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'No se pudo cargar la foto.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [info]);

  async function handleDelete() {
    if (!info || deleting) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteAttendancePhoto(info.employeeId, info.date, info.eventType, info.photoPath);
      onDeleted();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'No se pudo eliminar la foto.');
      setDeleting(false);
    }
  }

  return (
    <Modal animationType="fade" transparent visible={Boolean(info)} onRequestClose={onClose}>
      <View style={styles.photoModalBackdrop}>
        <View style={styles.photoModalCard}>
          <Text style={styles.photoModalTitle}>{info?.employeeName}</Text>
          <Text style={styles.photoModalSubtitle}>
            {info ? `${info.eventType === 'entry' ? 'Entrada' : 'Salida'} · ${formatShortDate(info.date)}` : ''}
          </Text>

          {error ? <InlineNotice message={error} tone="error" /> : null}

          <View style={styles.photoPreviewBox}>
            {loading ? (
              <ActivityIndicator color={colors.primary} />
            ) : photoUrl ? (
              <Image resizeMode="cover" source={{ uri: photoUrl }} style={styles.photoPreviewImage} />
            ) : null}
          </View>

          <View style={styles.formActions}>
            <AppButton onPress={onClose} variant="ghost">
              Cerrar
            </AppButton>
            <AppButton loading={deleting} onPress={() => void handleDelete()} variant="danger">
              Eliminar foto
            </AppButton>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const summaryTones = {
  success: { background: colors.successSoft, foreground: colors.success },
  warning: { background: colors.warningSoft, foreground: colors.warning },
  danger: { background: colors.dangerSoft, foreground: colors.danger },
  primary: { background: colors.primarySoft, foreground: colors.primary },
} as const;

function SummaryCard({
  label,
  value,
  suffix = '',
  tone,
}: {
  label: string;
  value: number;
  suffix?: string;
  tone: keyof typeof summaryTones;
}) {
  const palette = summaryTones[tone];
  return (
    <View style={[styles.summaryCard, { backgroundColor: palette.background }]}>
      <Text style={[styles.summaryValue, { color: palette.foreground }]}>{value}{suffix}</Text>
      <Text style={[styles.summaryLabel, { color: palette.foreground }]}>{label}</Text>
    </View>
  );
}

function MiniMetric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'success' | 'warning' | 'danger';
}) {
  const palette = summaryTones[tone];
  return (
    <View style={styles.miniMetric}>
      <Text style={[styles.miniMetricValue, { color: palette.foreground }]}>{value}</Text>
      <Text style={styles.miniMetricLabel}>{label}</Text>
    </View>
  );
}

function ScheduleToggle({
  label,
  description,
  enabled,
  time,
  onEnabledChange,
  onTimeChange,
}: {
  label: string;
  description: string;
  enabled: boolean;
  time: string;
  onEnabledChange: (enabled: boolean) => void;
  onTimeChange: (time: string) => void;
}) {
  return (
    <View style={styles.scheduleToggle}>
      <View style={styles.settingCopy}>
        <View style={styles.switchTitleRow}>
          <Text style={styles.settingTitle}>{label}</Text>
          <Switch
            accessibilityLabel={`Activar ${label.toLowerCase()}`}
            onValueChange={onEnabledChange}
            thumbColor={colors.white}
            trackColor={{ false: colors.border, true: colors.success }}
            value={enabled}
          />
        </View>
        <Text style={styles.settingDescription}>{description}</Text>
      </View>
      <AppField
        editable={enabled}
        hint={enabled ? 'Formato de 24 horas, HH:mm' : 'Activa este horario para poder editarlo.'}
        keyboardType="numbers-and-punctuation"
        label="Hora"
        maxLength={5}
        onChangeText={onTimeChange}
        placeholder="07:30"
        style={styles.timeInput}
        value={time}
      />
    </View>
  );
}

function TimelinePoint({ active, label, time }: { active: boolean; label: string; time: string }) {
  return (
    <View style={styles.timelinePoint}>
      <View style={[styles.timelineDot, !active && styles.timelineDotDisabled]} />
      <View>
        <Text style={styles.timelineLabel}>{label}</Text>
        <Text style={[styles.timelineTime, !active && styles.timelineTimeDisabled]}>
          {active ? time : 'Desactivada'}
        </Text>
      </View>
    </View>
  );
}

function initials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  shell: {
    flex: 1,
  },
  shellTablet: {
    flexDirection: 'row',
  },
  navigation: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  navigationTablet: {
    width: 250,
    backgroundColor: colors.primary,
    borderBottomWidth: 0,
    padding: 24,
    justifyContent: 'space-between',
  },
  navItems: {
    gap: 8,
    marginTop: 48,
  },
  navItemsMobile: {
    flexDirection: 'row',
    marginTop: 0,
    paddingHorizontal: 10,
    paddingVertical: 9,
    gap: 5,
  },
  navItem: {
    minHeight: 64,
    borderRadius: radii.medium,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
  },
  navItemMobile: {
    flex: 1,
    minHeight: 52,
    justifyContent: 'center',
    paddingHorizontal: 4,
    gap: 7,
  },
  navItemActive: {
    backgroundColor: '#254C3E',
  },
  navItemPressed: {
    opacity: 0.74,
  },
  navIcon: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: '#315447',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navIconActive: {
    backgroundColor: colors.accent,
  },
  navIconText: {
    color: '#D6E1DA',
    fontSize: 18,
    fontWeight: '800',
  },
  navIconTextActive: {
    color: colors.primary,
  },
  navTextMobile: {
    flexShrink: 1,
  },
  navLabel: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  navLabelTablet: {
    color: '#D6E1DA',
  },
  navLabelActive: {
    color: colors.white,
  },
  navCaption: {
    color: '#AFC2B7',
    fontSize: 11,
    marginTop: 3,
  },
  sidebarBottom: {
    borderTopWidth: 1,
    borderTopColor: '#315447',
    paddingTop: 18,
  },
  sidebarName: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '800',
  },
  sidebarEmail: {
    color: '#AFC2B7',
    fontSize: 11,
    marginTop: 3,
    marginBottom: 14,
  },
  sidebarButton: {
    minHeight: 42,
    borderColor: '#557064',
  },
  contentShell: {
    flex: 1,
    minWidth: 0,
  },
  topbar: {
    minHeight: 78,
    paddingHorizontal: 22,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  topbarActions: {
    marginLeft: 'auto',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  topbarButton: {
    minHeight: 42,
    paddingHorizontal: 12,
  },
  welcome: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '800',
    textAlign: 'right',
  },
  secureSession: {
    color: colors.inkMuted,
    fontSize: 11,
    textAlign: 'right',
    marginTop: 2,
  },
  content: {
    padding: 20,
    paddingBottom: 48,
    gap: 16,
  },
  module: {
    width: '100%',
    maxWidth: 1180,
    alignSelf: 'center',
    gap: 20,
  },
  moduleHeading: {
    marginBottom: 2,
  },
  eyebrow: {
    color: colors.warning,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 7,
  },
  moduleTitle: {
    color: colors.ink,
    fontSize: 29,
    fontWeight: '800',
    letterSpacing: -0.6,
  },
  moduleDescription: {
    color: colors.inkMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 6,
  },
  toolbar: {
    minHeight: 62,
    borderRadius: radii.medium,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 10,
  },
  refreshButton: {
    minHeight: 42,
  },
  loadingBlock: {
    minHeight: 220,
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
  },
  loadingLabel: {
    color: colors.inkMuted,
    fontSize: 14,
  },
  loadErrorCard: {
    minHeight: 180,
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    padding: 22,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  emptyState: {
    minHeight: 180,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyMark: {
    color: colors.border,
    fontSize: 40,
    fontWeight: '300',
  },
  emptyText: {
    color: colors.inkMuted,
    fontSize: 14,
    textAlign: 'center',
    marginTop: 6,
  },
  tableCard: {
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    ...shadows.card,
  },
  tableHeader: {
    minHeight: 44,
    paddingHorizontal: 17,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  tableHeaderText: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.7,
    textTransform: 'uppercase',
  },
  tableRow: {
    minHeight: 68,
    paddingHorizontal: 17,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  employeeColumn: {
    flex: 2.1,
    minWidth: 150,
  },
  dateColumn: {
    flex: 1.25,
    minWidth: 105,
  },
  timeColumn: {
    flex: 0.8,
    minWidth: 70,
  },
  statusColumn: {
    flex: 1,
    minWidth: 92,
  },
  employeeName: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  employeeMeta: {
    color: colors.inkMuted,
    fontSize: 11,
    marginTop: 3,
  },
  cellText: {
    color: colors.inkMuted,
    fontSize: 13,
  },
  cellStrong: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  mobileList: {
    gap: 10,
  },
  mobileRecord: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.medium,
    padding: 16,
    gap: 14,
  },
  mobileRecordTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 10,
  },
  mobileRecordIdentity: {
    flex: 1,
  },
  mobileTimes: {
    flexDirection: 'row',
    gap: 42,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 12,
  },
  paginationBar: {
    minHeight: 58,
    borderRadius: radii.medium,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 10,
  },
  paginationLabel: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  paginationActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  paginationButton: {
    minHeight: 38,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },
  pageNumber: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: '800',
    minWidth: 46,
    textAlign: 'center',
  },
  timeLabel: {
    color: colors.inkMuted,
    fontSize: 11,
  },
  timeValue: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '800',
    fontVariant: ['tabular-nums'],
    marginTop: 3,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  summaryCard: {
    flexGrow: 1,
    flexBasis: 165,
    minHeight: 128,
    borderRadius: radii.large,
    padding: 20,
    justifyContent: 'center',
  },
  summaryValue: {
    fontSize: 38,
    fontWeight: '800',
    letterSpacing: -1,
    fontVariant: ['tabular-nums'],
  },
  summaryLabel: {
    fontSize: 13,
    fontWeight: '800',
    marginTop: 5,
  },
  breakdownCard: {
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    ...shadows.card,
  },
  breakdownHeader: {
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '800',
  },
  cardDescription: {
    color: colors.inkMuted,
    fontSize: 12,
    marginTop: 4,
  },
  evaluatedLabel: {
    color: colors.primary,
    backgroundColor: colors.primarySoft,
    borderRadius: radii.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 11,
    fontWeight: '800',
  },
  employeeSummaryRow: {
    minHeight: 82,
    paddingHorizontal: 20,
    paddingVertical: 13,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 15,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    flexWrap: 'wrap',
  },
  summaryIdentity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    minWidth: 180,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.primarySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '900',
  },
  employeeMetrics: {
    flexDirection: 'row',
    gap: 20,
  },
  miniMetric: {
    minWidth: 48,
    alignItems: 'center',
  },
  miniMetricValue: {
    fontSize: 18,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
  },
  miniMetricLabel: {
    color: colors.inkMuted,
    fontSize: 10,
    marginTop: 2,
  },
  settingsLayout: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
    gap: 16,
  },
  settingsCard: {
    flex: 2,
    flexBasis: 470,
    backgroundColor: colors.surface,
    borderRadius: radii.large,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 22,
    gap: 20,
    ...shadows.card,
  },
  previewCard: {
    flex: 1,
    flexBasis: 260,
    backgroundColor: colors.primary,
    borderRadius: radii.large,
    padding: 24,
    gap: 20,
  },
  settingsDivider: {
    height: 1,
    backgroundColor: colors.border,
  },
  scheduleToggle: {
    gap: 14,
  },
  settingCopy: {
    flex: 1,
  },
  switchTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 14,
  },
  settingTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
  },
  settingDescription: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 5,
  },
  timeInput: {
    fontVariant: ['tabular-nums'],
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  toleranceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 18,
  },
  minutesInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.medium,
    backgroundColor: colors.white,
    paddingRight: 12,
  },
  minutesInput: {
    width: 58,
    minHeight: 48,
    color: colors.ink,
    fontSize: 17,
    fontWeight: '800',
    textAlign: 'center',
  },
  minutesLabel: {
    color: colors.inkMuted,
    fontSize: 12,
  },
  previewEyebrow: {
    color: colors.accent,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  previewTitle: {
    color: colors.white,
    fontSize: 23,
    fontWeight: '800',
    marginTop: -12,
  },
  timeline: {
    paddingVertical: 10,
  },
  timelinePoint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  timelineDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.accent,
    borderWidth: 3,
    borderColor: '#49685D',
  },
  timelineDotDisabled: {
    backgroundColor: colors.inkMuted,
  },
  timelineLine: {
    width: 2,
    height: 50,
    backgroundColor: '#49685D',
    marginLeft: 6,
  },
  timelineLabel: {
    color: '#AFC2B7',
    fontSize: 11,
  },
  timelineTime: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '800',
    marginTop: 2,
  },
  timelineTimeDisabled: {
    color: '#8FA79A',
    fontSize: 14,
  },
  formActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
  },
  editButton: {
    minHeight: 38,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  editPanel: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surfaceMuted,
    padding: 18,
    gap: 16,
  },
  mobileEmployeeRow: {
    flexWrap: 'wrap',
    gap: 10,
  },
  employeeStatusBadge: {
    alignSelf: 'flex-start',
    borderRadius: radii.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  employeeStatusText: {
    fontSize: 12,
    fontWeight: '800',
  },
  photoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  photoButtonIcon: {
    color: colors.primary,
    fontSize: 12,
  },
  photoButtonText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: '800',
  },
  photoModalBackdrop: {
    flex: 1,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  photoModalCard: {
    width: '100%',
    maxWidth: 380,
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    padding: 22,
    gap: 14,
    ...shadows.card,
  },
  photoModalTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: '800',
  },
  photoModalSubtitle: {
    color: colors.inkMuted,
    fontSize: 12,
    marginTop: -10,
  },
  photoPreviewBox: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: radii.medium,
    backgroundColor: colors.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  photoPreviewImage: {
    width: '100%',
    height: '100%',
  },
});
