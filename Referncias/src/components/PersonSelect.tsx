import { useMemo, useState } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { colors, radii, shadows } from '../theme';
import type { EmployeeDirectoryEntry } from '../types';

type PersonSelectProps = {
  label: string;
  value: string;
  options: EmployeeDirectoryEntry[];
  onChange: (employeeCode: string) => void;
  loading?: boolean;
  placeholder?: string;
};

export function PersonSelect({
  label,
  value,
  options,
  onChange,
  loading = false,
  placeholder = 'Selecciona tu nombre',
}: PersonSelectProps) {
  const [visible, setVisible] = useState(false);
  const [query, setQuery] = useState('');

  const selected = options.find((option) => option.employeeCode === value);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return options;
    }
    return options.filter((option) => option.fullName.toLowerCase().includes(normalized));
  }, [options, query]);

  function open() {
    setQuery('');
    setVisible(true);
  }

  function select(employeeCode: string) {
    onChange(employeeCode);
    setVisible(false);
  }

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <Pressable
        accessibilityLabel={label}
        accessibilityRole="button"
        disabled={loading}
        onPress={open}
        style={({ pressed }) => [styles.field, pressed && styles.fieldPressed]}
      >
        <Text style={[styles.fieldText, !selected && styles.fieldPlaceholder]} numberOfLines={1}>
          {loading ? 'Cargando personal…' : (selected?.fullName ?? placeholder)}
        </Text>
        <Text style={styles.chevron}>▾</Text>
      </Pressable>

      <Modal animationType="fade" onRequestClose={() => setVisible(false)} transparent visible={visible}>
        <Pressable onPress={() => setVisible(false)} style={styles.backdrop}>
          <Pressable onPress={(event) => event.stopPropagation()} style={styles.sheet}>
            <Text style={styles.sheetTitle}>{label}</Text>
            <TextInput
              accessibilityLabel="Buscar por nombre"
              autoFocus
              onChangeText={setQuery}
              placeholder="Buscar nombre…"
              placeholderTextColor={colors.inkMuted}
              style={styles.search}
              value={query}
            />
            <ScrollView keyboardShouldPersistTaps="handled" style={styles.list}>
              {filtered.length === 0 ? (
                <Text style={styles.emptyText}>No hay coincidencias.</Text>
              ) : (
                filtered.map((option) => (
                  <Pressable
                    accessibilityRole="menuitem"
                    key={option.employeeCode}
                    onPress={() => select(option.employeeCode)}
                    style={({ pressed }) => [
                      styles.option,
                      option.employeeCode === value && styles.optionActive,
                      pressed && styles.optionPressed,
                    ]}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        option.employeeCode === value && styles.optionTextActive,
                      ]}
                    >
                      {option.fullName}
                    </Text>
                  </Pressable>
                ))
              )}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    width: '100%',
    gap: 7,
  },
  label: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
  },
  field: {
    minHeight: 52,
    borderRadius: radii.medium,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  fieldPressed: {
    opacity: 0.82,
  },
  fieldText: {
    flex: 1,
    color: colors.ink,
    fontSize: 16,
  },
  fieldPlaceholder: {
    color: colors.inkMuted,
  },
  chevron: {
    color: colors.inkMuted,
    fontSize: 14,
  },
  backdrop: {
    flex: 1,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  sheet: {
    width: '100%',
    maxWidth: 440,
    maxHeight: '76%',
    borderRadius: radii.large,
    backgroundColor: colors.surface,
    padding: 22,
    gap: 14,
    ...shadows.card,
  },
  sheetTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '800',
  },
  search: {
    minHeight: 46,
    borderRadius: radii.medium,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    color: colors.ink,
    paddingHorizontal: 14,
    fontSize: 15,
  },
  list: {
    flexGrow: 0,
  },
  emptyText: {
    color: colors.inkMuted,
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
  option: {
    minHeight: 52,
    borderRadius: radii.medium,
    paddingHorizontal: 14,
    justifyContent: 'center',
  },
  optionActive: {
    backgroundColor: colors.primarySoft,
  },
  optionPressed: {
    opacity: 0.78,
  },
  optionText: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '600',
  },
  optionTextActive: {
    color: colors.primary,
    fontWeight: '800',
  },
});
