import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from "react-native";
import { Bot, Clock3, MapPin, MessageCircle, Plus, Send, X } from "lucide-react-native";

import {
  isSessionActive,
  sendChatMessage,
  type ChatAssistantMessage,
  type ChatConfidence,
  type ChatStrategy,
} from "../../services/chatService";
import {
  fetchLocations,
  fetchNewsProfile,
  updateNewsProfile,
  type NewsLocation,
  type NewsProfile,
} from "../../services/newsService";
import { getCurrentFirebaseIdToken } from "../../services/firebaseClient";
import { colors, fonts, layout, radii, spacing } from "../../theme";
import type { AppUser, NewsArticle } from "../../types";
import {
  articleOpeningPrompt,
  CHAT_HISTORY_STORAGE_KEY,
  conversationTitle,
  LEGACY_CHAT_STORAGE_KEY,
  readConversations,
  type ChatConversation,
  type ChatEntry,
} from "./chatHistory";

type Props = {
  user: AppUser;
  contextArticle: NewsArticle | null;
  onClearContext: () => void;
  onOpenArticle: (slug: string) => void;
  onProfileChanged: (profile: NewsProfile) => void;
};

type ActiveConversation = Omit<ChatConversation, "sessionId" | "expiresAt"> & {
  sessionId: string | null;
  expiresAt: string | null;
};

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

export function ChatScreen({
  user,
  contextArticle,
  onClearContext,
  onOpenArticle,
  onProfileChanged,
}: Props) {
  const userKey = user.id;
  const { width } = useWindowDimensions();
  const isMobile = width < 768;
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<ActiveConversation | null>(null);
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locations, setLocations] = useState<NewsLocation[]>([]);
  const [locationId, setLocationId] = useState<string | null>(null);
  const [locationsError, setLocationsError] = useState<string | null>(null);
  const [isSavingLocation, setIsSavingLocation] = useState(false);
  const [newsProfile, setNewsProfile] = useState<NewsProfile | null>(null);
  const messageScroll = useRef<ScrollView>(null);
  const lastContextArticleId = useRef<string | null>(null);
  const sending = useRef(false);
  const entries = activeConversation?.entries ?? [];

  useEffect(() => {
    let active = true;
    setConversations([]);
    setActiveConversation(null);
    setIsHistoryLoaded(false);
    Promise.all([
      AsyncStorage.getItem(CHAT_HISTORY_STORAGE_KEY),
      AsyncStorage.getItem(LEGACY_CHAT_STORAGE_KEY),
    ])
      .then(([raw, legacyRaw]) => {
        if (!active) return;
        const restored = readConversations(raw, legacyRaw, userKey);
        setConversations(restored);
        setActiveConversation(restored[0] ?? null);
        setIsHistoryLoaded(true);
        if (!raw && restored.length > 0) {
          AsyncStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(restored)).catch(() => undefined);
        }
      })
      .catch(() => {
        if (active) setIsHistoryLoaded(true);
      });
    void Promise.all([
      fetchLocations(),
      getCurrentFirebaseIdToken().then(fetchNewsProfile),
    ])
      .then(([items, profile]) => {
        if (!active) return;
        setLocations(items);
        setNewsProfile(profile);
        setLocationId(profile.locationId);
      })
      .catch(() => {
        if (active) setLocationsError("No pudimos cargar tu ubicación y preferencias.");
      });
    return () => {
      active = false;
    };
  }, [userKey]);

  const persistChat = useCallback(
    (conversation: ChatConversation) => {
      const now = Date.now();
      const next = [
        conversation,
        ...conversations.filter(
          (item) => item.id !== conversation.id && Date.parse(item.expiresAt) > now,
        ),
      ].sort((left, right) => Date.parse(right.updatedAt) - Date.parse(left.updatedAt));
      setConversations(next);
      AsyncStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(next)).catch(() => undefined);
    },
    [conversations],
  );

  const selectLocation = useCallback(async (nextLocationId: string) => {
    if (!newsProfile || nextLocationId === locationId || isSavingLocation) return;
    setIsSavingLocation(true);
    setLocationsError(null);
    try {
      const token = await getCurrentFirebaseIdToken();
      const updated = await updateNewsProfile(
        token,
        nextLocationId,
        newsProfile.selectedTopics,
      );
      setNewsProfile(updated);
      setLocationId(updated.locationId);
      onProfileChanged(updated);
    } catch {
      setLocationsError("No pudimos guardar la ubicación. Intenta de nuevo.");
    } finally {
      setIsSavingLocation(false);
    }
  }, [isSavingLocation, locationId, newsProfile, onProfileChanged]);

  const startNewConversation = useCallback(() => {
    setActiveConversation({
      id: `draft-${nextEntryId()}`,
      userKey,
      sessionId: null,
      expiresAt: null,
      title: "Nueva conversación",
      updatedAt: new Date().toISOString(),
      entries: [],
    });
    setIsHistoryOpen(false);
    setDraft("");
    setError(null);
  }, [userKey]);

  const send = useCallback(
    async (text: string, conversationOverride?: ActiveConversation) => {
      const message = text.trim();
      if (!isHistoryLoaded || !message || sending.current) return;

      const target: ActiveConversation = conversationOverride ?? activeConversation ?? {
        id: `draft-${nextEntryId()}`,
        userKey,
        sessionId: null,
        expiresAt: null,
        title: "Nueva conversación",
        updatedAt: new Date().toISOString(),
        entries: [],
      };
      const activeSession = isSessionActive(target.expiresAt) ? target.sessionId : null;
      // Una sesión vencida empieza una conversación nueva, igual que en el servidor.
      const baseEntries = activeSession ? target.entries : [];
      const userEntry: ChatEntry = { id: nextEntryId(), role: "user", content: message };
      setActiveConversation({ ...target, entries: [...baseEntries, userEntry] });
      setDraft("");
      setError(null);
      sending.current = true;
      setIsSending(true);
      try {
        const reply = await sendChatMessage({
          message,
          sessionId: activeSession,
          newsId: baseEntries.length === 0 ? target.contextArticleId ?? null : null,
          locationId,
        });
        const nextEntries: ChatEntry[] = [
          ...(reply.sessionId === activeSession ? baseEntries : []),
          userEntry,
          { id: nextEntryId(), role: "assistant", message: reply.message },
        ];
        const saved: ChatConversation = {
          id: activeSession ? target.id : reply.sessionId,
          userKey,
          sessionId: reply.sessionId,
          expiresAt: reply.expiresAt,
          title: conversationTitle(nextEntries, target.contextTitle),
          updatedAt: reply.message.createdAt,
          entries: nextEntries,
          contextArticleId: target.contextArticleId,
          contextTitle: target.contextTitle,
        };
        setActiveConversation(saved);
        if (!locationId) setLocationId(reply.locationId);
        persistChat(saved);
      } catch (sendError) {
        setActiveConversation({ ...target, entries: baseEntries });
        setDraft(message);
        setError(sendError instanceof Error ? sendError.message : "El asistente no pudo responder.");
      } finally {
        sending.current = false;
        setIsSending(false);
      }
    },
    [activeConversation, isHistoryLoaded, locationId, persistChat, user, userKey],
  );

  useEffect(() => {
    if (!isHistoryLoaded) return;
    if (!contextArticle) {
      lastContextArticleId.current = null;
      return;
    }
    if (lastContextArticleId.current === contextArticle.id) return;
    lastContextArticleId.current = contextArticle.id;
    const contextualConversation: ActiveConversation = {
      id: `draft-${nextEntryId()}`,
      userKey,
      sessionId: null,
      expiresAt: null,
      title: contextArticle.title,
      updatedAt: new Date().toISOString(),
      entries: [],
      contextArticleId: contextArticle.id,
      contextTitle: contextArticle.title,
    };
    setActiveConversation(contextualConversation);
    setIsHistoryOpen(false);
    void send(articleOpeningPrompt(contextArticle.title), contextualConversation);
  }, [contextArticle, isHistoryLoaded, send, userKey]);

  useEffect(() => {
    requestAnimationFrame(() => messageScroll.current?.scrollToEnd({ animated: true }));
  }, [activeConversation?.id, entries.length, isSending]);

  const selectConversation = useCallback((conversation: ChatConversation) => {
    setActiveConversation(conversation);
    setIsHistoryOpen(false);
    setDraft("");
    setError(null);
  }, []);

  const hasArticleContext = Boolean(activeConversation?.contextArticleId);
  const suggestions = hasArticleContext ? ARTICLE_SUGGESTIONS : GENERAL_SUGGESTIONS;

  return (
    <View style={[styles.screen, isMobile ? styles.screenMobile : null]}>
      {!isMobile || isHistoryOpen ? (
        <View style={[styles.historyPanel, isMobile ? styles.mobileHistoryPanel : null]}>
          <View style={styles.historyHeader}>
            <View>
              <Text style={styles.historyTitle}>Conversaciones</Text>
              <Text style={styles.historySubtitle}>Disponibles durante una hora</Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Iniciar nueva conversación"
              disabled={!isHistoryLoaded || isSending}
              onPress={startNewConversation}
              style={({ pressed }) => [styles.newChatButton, pressed ? styles.pressed : null]}
            >
              <Plus size={18} color={colors.action} />
              <Text style={styles.newChatLabel}>Nueva</Text>
            </Pressable>
          </View>
          <ScrollView
            style={styles.historyList}
            contentContainerStyle={styles.historyListContent}
            keyboardShouldPersistTaps="handled"
          >
            {conversations.length === 0 ? (
              <Text style={styles.historyEmpty}>Tus conversaciones recientes aparecerán aquí.</Text>
            ) : conversations.map((conversation) => (
              <Pressable
                key={conversation.id}
                accessibilityRole="button"
                accessibilityState={{ selected: activeConversation?.id === conversation.id }}
                disabled={isSending}
                onPress={() => selectConversation(conversation)}
                style={({ pressed }) => [
                  styles.conversationItem,
                  activeConversation?.id === conversation.id ? styles.conversationItemSelected : null,
                  pressed ? styles.pressed : null,
                ]}
              >
                <MessageCircle size={16} color={colors.action} />
                <View style={styles.conversationText}>
                  <Text style={styles.conversationTitle} numberOfLines={2}>{conversation.title}</Text>
                  <View style={styles.conversationDateRow}>
                    <Clock3 size={12} color={colors.textSecondary} />
                    <Text style={styles.conversationDate}>
                      {new Date(conversation.updatedAt).toLocaleString("es", {
                        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
                      })}
                    </Text>
                  </View>
                </View>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      ) : null}

      <View style={styles.chatPanel}>
        <View style={styles.header}>
          <View style={styles.headerTitleRow}>
            <Bot size={24} color={colors.brand} />
            <View style={styles.headerCopy}>
              <Text style={styles.title}>Asistente de noticias</Text>
              {!isMobile ? (
                <Text style={styles.subtitle}>Respuestas basadas en noticias publicadas.</Text>
              ) : null}
            </View>
          </View>
          {isMobile ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={isHistoryOpen ? "Ocultar conversaciones" : "Mostrar conversaciones"}
              accessibilityState={{ expanded: isHistoryOpen }}
              onPress={() => setIsHistoryOpen((open) => !open)}
              style={({ pressed }) => [styles.mobileHistoryButton, pressed ? styles.pressed : null]}
            >
              <MessageCircle size={18} color={colors.action} />
              <Text style={styles.mobileHistoryLabel}>Historial ({conversations.length})</Text>
            </Pressable>
          ) : null}
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
                  disabled={isSavingLocation || !newsProfile}
                  onPress={() => void selectLocation(location.id)}
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

        {activeConversation?.contextTitle ? (
          <View style={styles.contextBanner}>
            <View style={styles.contextText}>
              <Text style={styles.contextKicker}>Conversación sobre</Text>
              <Text style={styles.contextTitle} numberOfLines={2}>
                {activeConversation.contextTitle}
              </Text>
            </View>
            {contextArticle?.id === activeConversation.contextArticleId ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Quitar contexto de la noticia"
                hitSlop={10}
                onPress={onClearContext}
                style={({ pressed }) => [styles.iconButton, pressed ? styles.pressed : null]}
              >
                <X size={18} color={colors.textSecondary} />
              </Pressable>
            ) : null}
          </View>
        ) : null}

        <ScrollView
          ref={messageScroll}
          style={styles.thread}
          contentContainerStyle={styles.threadContent}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() => messageScroll.current?.scrollToEnd({ animated: true })}
        >
          {entries.length === 0 ? (
            <View style={styles.emptyThread}>
              <Text style={styles.emptyTitle}>¿Qué quieres saber?</Text>
              <Text style={styles.emptyDescription}>
                Pregunta sobre noticias, temas o una noticia concreta.
              </Text>
              <View style={styles.suggestions}>
                {suggestions.map((suggestion) => (
                  <Pressable
                    key={suggestion}
                    accessibilityRole="button"
                    disabled={!isHistoryLoaded || isSending}
                    onPress={() => void send(suggestion)}
                    style={({ pressed }) => [styles.suggestion, pressed ? styles.pressed : null]}
                  >
                    <Text style={styles.suggestionLabel}>{suggestion}</Text>
                  </Pressable>
                ))}
              </View>
            </View>
          ) : entries.map((entry) =>
            entry.role === "user" ? (
              <View key={entry.id} style={[styles.bubble, styles.userBubble]}>
                <Text style={styles.userText}>{entry.content}</Text>
              </View>
            ) : (
              <AssistantBubble key={entry.id} message={entry.message} onOpenArticle={onOpenArticle} />
            ),
          )}
          {isSending ? (
            <View style={[styles.bubble, styles.assistantBubble, styles.typing]}>
              <ActivityIndicator color={colors.action} size="small" />
              <Text style={styles.metaText}>Consultando noticias…</Text>
            </View>
          ) : null}
        </ScrollView>

        {error ? <Text accessibilityRole="alert" style={styles.errorText}>{error}</Text> : null}

        <View style={styles.composer}>
          <TextInput
            accessibilityLabel="Mensaje para el asistente"
            value={draft}
            onChangeText={setDraft}
            placeholder="Escribe tu mensaje… (Enter para enviar)"
            placeholderTextColor={colors.textSecondary}
            editable={isHistoryLoaded && !isSending}
            maxLength={2000}
            multiline
            submitBehavior="submit"
            returnKeyType="send"
            onSubmitEditing={() => void send(draft)}
            style={styles.input}
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Enviar mensaje"
            disabled={!isHistoryLoaded || isSending || !draft.trim()}
            onPress={() => void send(draft)}
            style={({ pressed }) => [
              styles.sendButton,
              !isHistoryLoaded || isSending || !draft.trim() ? styles.sendDisabled : null,
              pressed ? styles.pressed : null,
            ]}
          >
            <Send size={20} color={colors.onSolid} />
          </Pressable>
        </View>
      </View>
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
    maxWidth: layout.maxContentWidth,
    alignSelf: "center",
    flex: 1,
    minHeight: 0,
    flexDirection: "row",
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  screenMobile: {
    flexDirection: "column",
  },
  historyPanel: {
    width: 280,
    minHeight: 0,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.panel,
    backgroundColor: colors.surface,
    overflow: "hidden",
  },
  mobileHistoryPanel: {
    width: "100%",
    height: 220,
    maxHeight: 220,
    flexShrink: 0,
  },
  historyHeader: {
    minHeight: 76,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  historyTitle: {
    fontFamily: fonts.headingBold,
    fontSize: 17,
    color: colors.ink,
  },
  historySubtitle: {
    marginTop: 2,
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.textSecondary,
  },
  newChatButton: {
    minHeight: 44,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xxs,
    paddingHorizontal: spacing.xs,
    borderRadius: radii.control,
    backgroundColor: colors.actionSoft,
  },
  newChatLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.action,
  },
  historyList: {
    flex: 1,
    minHeight: 0,
  },
  historyListContent: {
    gap: spacing.xxs,
    padding: spacing.xs,
  },
  historyEmpty: {
    padding: spacing.sm,
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.textSecondary,
  },
  conversationItem: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.xs,
    padding: spacing.xs,
    borderRadius: radii.control,
  },
  conversationItemSelected: {
    backgroundColor: colors.actionSoft,
  },
  conversationText: {
    flex: 1,
    minWidth: 0,
    gap: spacing.xxs,
  },
  conversationTitle: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    lineHeight: 19,
    color: colors.ink,
  },
  conversationDateRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xxs,
  },
  conversationDate: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.textSecondary,
  },
  chatPanel: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    gap: spacing.sm,
  },
  headerCopy: {
    flex: 1,
    minWidth: 0,
  },
  mobileHistoryButton: {
    minHeight: 44,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xxs,
    paddingHorizontal: spacing.xs,
    borderRadius: radii.control,
    backgroundColor: colors.actionSoft,
  },
  mobileHistoryLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.action,
  },
  header: {
    minHeight: 54,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.xs,
  },
  headerTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  title: {
    fontFamily: fonts.headingBold,
    fontSize: 24,
    color: colors.ink,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    lineHeight: 18,
    color: colors.textSecondary,
  },
  locationBlock: {
    gap: spacing.xxs,
    flexShrink: 0,
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
    flex: 1,
    minHeight: 0,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.panel,
    backgroundColor: colors.background,
  },
  threadContent: {
    flexGrow: 1,
    gap: spacing.sm,
    padding: spacing.md,
  },
  emptyThread: {
    gap: spacing.sm,
    paddingVertical: spacing.lg,
    alignItems: "flex-start",
  },
  emptyDescription: {
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.textSecondary,
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
    flexShrink: 0,
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
    fontSize: 16,
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
