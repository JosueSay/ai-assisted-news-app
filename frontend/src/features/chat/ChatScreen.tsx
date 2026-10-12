import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Bot, MapPin, Send, X } from "lucide-react-native";

import { AppButton } from "../../components/AppButton";
import {
  chatExternalUserId,
  isSessionActive,
  sendChatMessage,
  type ChatAssistantMessage,
  type ChatConfidence,
  type ChatStrategy,
} from "../../services/chatService";
import { fetchLocations, type NewsLocation } from "../../services/newsService";
import { colors, fonts, layout, radii, spacing } from "../../theme";
import type { AppUser, NewsArticle } from "../../types";

type Props = {
  user: AppUser;
  contextArticle: NewsArticle | null;
  onClearContext: () => void;
  onOpenArticle: (slug: string) => void;
};

type ChatEntry =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; message: ChatAssistantMessage };

type StoredChat = {
  userKey: string;
  sessionId: string;
  expiresAt: string;
  entries: ChatEntry[];
};

const CHAT_STORAGE_KEY = "ai-news:chat-session";
const LOCATION_STORAGE_KEY = "ai-news:chat-location";

const STRATEGY_LABELS: Record<ChatStrategy, string> = {
  database_query: "Datos de la base",
  template: "Respuesta predefinida",
  llm: "Elaborada con IA",
};

const CONFIDENCE_LABELS: Record<ChatConfidence, string> = {
  high: "Confianza alta",
  medium: "Confianza media",
  low: "Confianza baja",
};

const VERIFICATION_LABELS: Record<string, string> = {
  developing: "En desarrollo",
  insufficient_sources: "Fuentes insuficientes",
  conflicting_sources: "Fuentes contradictorias",
};

const GENERAL_SUGGESTIONS = [
  "¿Cuáles son las últimas noticias?",
  "Noticias de mi país",
  "Noticias de tecnología",
  "Resume las noticias de hoy",
];

const ARTICLE_SUGGESTIONS = [
  "Resume esta noticia",
  "Explícame esta noticia",
  "¿Qué fuentes tiene?",
];

let entryCounter = 0;
function nextEntryId() {
  entryCounter += 1;
  return `${Date.now()}-${entryCounter}`;
}

export function ChatScreen({ user, contextArticle, onClearContext, onOpenArticle }: Props) {
  const userKey = chatExternalUserId(user);
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locations, setLocations] = useState<NewsLocation[]>([]);
  const [locationId, setLocationId] = useState<string | null>(null);
  const [locationsError, setLocationsError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    AsyncStorage.getItem(CHAT_STORAGE_KEY)
      .then((raw) => {
        if (!active || !raw) return;
        const stored = JSON.parse(raw) as StoredChat;
        if (stored.userKey === userKey && isSessionActive(stored.expiresAt)) {
          setSessionId(stored.sessionId);
          setExpiresAt(stored.expiresAt);
          setEntries(stored.entries);
        }
      })
      .catch(() => undefined);
    AsyncStorage.getItem(LOCATION_STORAGE_KEY)
      .then((stored) => {
        if (active && stored) setLocationId(stored);
      })
      .catch(() => undefined);
    fetchLocations()
      .then((items) => {
        if (active) setLocations(items);
      })
      .catch(() => {
        if (active) setLocationsError("No pudimos cargar las ubicaciones.");
      });
    return () => {
      active = false;
    };
  }, [userKey]);

  const persistChat = useCallback(
    (nextSessionId: string, nextExpiresAt: string, nextEntries: ChatEntry[]) => {
      const stored: StoredChat = {
        userKey,
        sessionId: nextSessionId,
        expiresAt: nextExpiresAt,
        entries: nextEntries,
      };
      AsyncStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(stored)).catch(() => undefined);
    },
    [userKey],
  );

  const selectLocation = useCallback((nextLocationId: string) => {
    setLocationId(nextLocationId);
    AsyncStorage.setItem(LOCATION_STORAGE_KEY, nextLocationId).catch(() => undefined);
  }, []);

  const startNewConversation = useCallback(() => {
    setEntries([]);
    setSessionId(null);
    setExpiresAt(null);
    setError(null);
    AsyncStorage.removeItem(CHAT_STORAGE_KEY).catch(() => undefined);
  }, []);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || isSending) return;

      const activeSession = isSessionActive(expiresAt) ? sessionId : null;
      // Una sesión vencida empieza una conversación nueva, igual que en el servidor.
      const baseEntries = activeSession ? entries : [];
      const userEntry: ChatEntry = { id: nextEntryId(), role: "user", content: message };
      setEntries([...baseEntries, userEntry]);
      setDraft("");
      setError(null);
      setIsSending(true);
      try {
        const reply = await sendChatMessage({
          message,
          user,
          sessionId: activeSession,
          newsId: contextArticle?.id ?? null,
          locationId,
        });
        const nextEntries: ChatEntry[] = [
          ...(reply.sessionId === activeSession ? baseEntries : []),
          userEntry,
          { id: nextEntryId(), role: "assistant", message: reply.message },
        ];
        setEntries(nextEntries);
        setSessionId(reply.sessionId);
        setExpiresAt(reply.expiresAt);
        if (!locationId) setLocationId(reply.locationId);
        persistChat(reply.sessionId, reply.expiresAt, nextEntries);
      } catch (sendError) {
        setEntries(baseEntries);
        setDraft(message);
        setError(sendError instanceof Error ? sendError.message : "El asistente no pudo responder.");
      } finally {
        setIsSending(false);
      }
    },
    [contextArticle, entries, expiresAt, isSending, locationId, persistChat, sessionId, user],
  );

  const suggestions = contextArticle ? ARTICLE_SUGGESTIONS : GENERAL_SUGGESTIONS;

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <View style={styles.headerTitleRow}>
          <Bot size={24} color={colors.brand} />
          <Text style={styles.title}>Asistente de noticias</Text>
        </View>
        <Text style={styles.subtitle}>
          Responde con las noticias publicadas en AI News. La conversación se borra después de una
          hora.
        </Text>
      </View>

      <View style={styles.locationBlock}>
        <View style={styles.locationLabelRow}>
          <MapPin size={16} color={colors.textSecondary} />
          <Text style={styles.locationLabel}>Ubicación simulada</Text>
        </View>
        {locationsError ? <Text style={styles.errorText}>{locationsError}</Text> : null}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          {locations.map((location) => {
            const selected = location.id === locationId;
            return (
              <Pressable
                key={location.id}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => selectLocation(location.id)}
                style={({ pressed }) => [
                  styles.chip,
                  selected ? styles.chipSelected : null,
                  pressed ? styles.pressed : null,
                ]}
              >
                <Text style={[styles.chipLabel, selected ? styles.chipLabelSelected : null]}>
                  {location.name}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {contextArticle ? (
        <View style={styles.contextBanner}>
          <View style={styles.contextText}>
            <Text style={styles.contextKicker}>Preguntando sobre</Text>
            <Text style={styles.contextTitle} numberOfLines={2}>
              {contextArticle.title}
            </Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Dejar de preguntar sobre esta noticia"
            hitSlop={10}
            onPress={onClearContext}
            style={({ pressed }) => [styles.iconButton, pressed ? styles.pressed : null]}
          >
            <X size={18} color={colors.textSecondary} />
          </Pressable>
        </View>
      ) : null}

      <View style={styles.thread}>
        {entries.length === 0 ? (
          <View style={styles.emptyThread}>
            <Text style={styles.emptyTitle}>¿Qué quieres saber?</Text>
            <View style={styles.suggestions}>
              {suggestions.map((suggestion) => (
                <Pressable
                  key={suggestion}
                  accessibilityRole="button"
                  disabled={isSending}
                  onPress={() => void send(suggestion)}
                  style={({ pressed }) => [styles.suggestion, pressed ? styles.pressed : null]}
                >
                  <Text style={styles.suggestionLabel}>{suggestion}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        ) : (
          entries.map((entry) =>
            entry.role === "user" ? (
              <View key={entry.id} style={[styles.bubble, styles.userBubble]}>
                <Text style={styles.userText}>{entry.content}</Text>
              </View>
            ) : (
              <AssistantBubble key={entry.id} message={entry.message} onOpenArticle={onOpenArticle} />
            ),
          )
        )}
        {isSending ? (
          <View style={[styles.bubble, styles.assistantBubble, styles.typing]}>
            <ActivityIndicator color={colors.action} size="small" />
            <Text style={styles.metaText}>Consultando noticias…</Text>
          </View>
        ) : null}
      </View>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <View style={styles.composer}>
        <TextInput
          accessibilityLabel="Mensaje para el asistente"
          value={draft}
          onChangeText={setDraft}
          placeholder="Pregunta por noticias, un país o un tema"
          placeholderTextColor={colors.textSecondary}
          editable={!isSending}
          maxLength={2000}
          multiline
          onSubmitEditing={() => void send(draft)}
          style={styles.input}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Enviar mensaje"
          disabled={isSending || !draft.trim()}
          onPress={() => void send(draft)}
          style={({ pressed }) => [
            styles.sendButton,
            isSending || !draft.trim() ? styles.sendDisabled : null,
            pressed ? styles.pressed : null,
          ]}
        >
          <Send size={20} color={colors.onSolid} />
        </Pressable>
      </View>

      {entries.length > 0 ? (
        <AppButton label="Nueva conversación" variant="ghost" onPress={startNewConversation} />
      ) : null}
    </View>
  );
}

function AssistantBubble({
  message,
  onOpenArticle,
}: {
  message: ChatAssistantMessage;
  onOpenArticle: (slug: string) => void;
}) {
  return (
    <View style={[styles.bubble, styles.assistantBubble]}>
      <Text style={styles.assistantText}>{message.content}</Text>
      <View style={styles.metaRow}>
        <Text style={styles.badge}>{STRATEGY_LABELS[message.strategy]}</Text>
        {message.intent !== "unsupported" ? (
          <Text style={[styles.badge, message.confidence === "low" ? styles.badgeWarning : null]}>
            {CONFIDENCE_LABELS[message.confidence]}
          </Text>
        ) : null}
      </View>
      {message.uncertainty ? <Text style={styles.metaText}>{message.uncertainty}</Text> : null}
      {message.citedNews.length > 0 ? (
        <View style={styles.citations}>
          <Text style={styles.citationsTitle}>Noticias citadas</Text>
          {message.citedNews.map((news) => (
            <Pressable
              key={news.id}
              accessibilityRole="link"
              onPress={() => onOpenArticle(news.slug)}
              style={({ pressed }) => [pressed ? styles.pressed : null]}
            >
              <Text style={styles.citationLink}>
                {news.title}
                {VERIFICATION_LABELS[news.verificationStatus]
                  ? ` · ${VERIFICATION_LABELS[news.verificationStatus]}`
                  : ""}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    width: "100%",
    maxWidth: layout.readerWidth,
    alignSelf: "center",
    gap: spacing.md,
    paddingVertical: spacing.md,
  },
  header: {
    gap: spacing.xs,
  },
  headerTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  title: {
    fontFamily: fonts.headingBold,
    fontSize: 28,
    color: colors.ink,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 15,
    lineHeight: 22,
    color: colors.textSecondary,
  },
  locationBlock: {
    gap: spacing.xs,
  },
  locationLabelRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xxs,
  },
  locationLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.textSecondary,
  },
  chipRow: {
    gap: spacing.xs,
    paddingVertical: spacing.xxs,
  },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    backgroundColor: colors.surface,
  },
  chipSelected: {
    backgroundColor: colors.action,
    borderColor: colors.action,
  },
  chipLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.text,
  },
  chipLabelSelected: {
    color: colors.onSolid,
  },
  contextBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.sm,
    borderRadius: radii.panel,
    backgroundColor: colors.actionSoft,
  },
  contextText: {
    flex: 1,
    gap: spacing.xxs,
  },
  contextKicker: {
    fontFamily: fonts.bodyMedium,
    fontSize: 12,
    color: colors.action,
    textTransform: "uppercase",
  },
  contextTitle: {
    fontFamily: fonts.heading,
    fontSize: 17,
    color: colors.ink,
  },
  iconButton: {
    padding: spacing.xxs,
  },
  thread: {
    gap: spacing.sm,
  },
  emptyThread: {
    gap: spacing.sm,
    paddingVertical: spacing.lg,
  },
  emptyTitle: {
    fontFamily: fonts.heading,
    fontSize: 20,
    color: colors.ink,
  },
  suggestions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  suggestion: {
    borderWidth: 1,
    borderColor: colors.controlBorder,
    borderRadius: radii.control,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    backgroundColor: colors.surface,
  },
  suggestionLabel: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.text,
  },
  bubble: {
    maxWidth: "88%",
    borderRadius: radii.panel,
    padding: spacing.sm,
    gap: spacing.xs,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: colors.action,
  },
  assistantBubble: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  typing: {
    flexDirection: "row",
    alignItems: "center",
  },
  userText: {
    fontFamily: fonts.body,
    fontSize: 15,
    lineHeight: 22,
    color: colors.onSolid,
  },
  assistantText: {
    fontFamily: fonts.body,
    fontSize: 15,
    lineHeight: 22,
    color: colors.text,
  },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  badge: {
    fontFamily: fonts.bodyMedium,
    fontSize: 12,
    color: colors.textSecondary,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    overflow: "hidden",
  },
  badgeWarning: {
    color: colors.danger,
  },
  metaText: {
    fontFamily: fonts.body,
    fontSize: 13,
    lineHeight: 18,
    color: colors.textSecondary,
  },
  citations: {
    gap: spacing.xxs,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.xs,
  },
  citationsTitle: {
    fontFamily: fonts.bodyMedium,
    fontSize: 12,
    color: colors.textSecondary,
  },
  citationLink: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.action,
    textDecorationLine: "underline",
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.danger,
  },
  composer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.xs,
  },
  input: {
    flex: 1,
    minHeight: 48,
    maxHeight: 140,
    borderWidth: 1,
    borderColor: colors.controlBorder,
    borderRadius: radii.control,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.text,
    backgroundColor: colors.surface,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: radii.control,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.action,
  },
  sendDisabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.75,
  },
});
