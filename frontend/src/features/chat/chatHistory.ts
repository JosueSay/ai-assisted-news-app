import type { ChatAssistantMessage } from "../../services/chatService";

export type ChatEntry =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; message: ChatAssistantMessage };

export type ChatConversation = {
  id: string;
  userKey: string;
  sessionId: string;
  expiresAt: string;
  title: string;
  updatedAt: string;
  entries: ChatEntry[];
  contextArticleId?: string | null;
  contextTitle?: string | null;
};

export const CHAT_HISTORY_STORAGE_KEY = "ai-news:chat-conversations";
export const LEGACY_CHAT_STORAGE_KEY = "ai-news:chat-session";

export function articleOpeningPrompt(title: string): string {
  return `Explícame esta noticia: ${title.trim()}`;
}

export function conversationTitle(entries: ChatEntry[], contextTitle?: string | null): string {
  const title = contextTitle?.trim() || entries.find((entry) => entry.role === "user")?.content;
  if (!title) return "Nueva conversación";
  return title.length > 52 ? `${title.slice(0, 49).trimEnd()}…` : title;
}

export function readConversations(
  raw: string | null,
  legacyRaw: string | null,
  userKey: string,
  now: Date = new Date(),
): ChatConversation[] {
  const current = parseJson(raw);
  if (Array.isArray(current)) {
    return current
      .filter((item): item is ChatConversation => isConversation(item))
      .filter((item) => item.userKey === userKey && isSessionActive(item.expiresAt, now))
      .sort((left, right) => Date.parse(right.updatedAt) - Date.parse(left.updatedAt));
  }

  const legacy = parseJson(legacyRaw);
  if (
    !isRecord(legacy)
    || legacy.userKey !== userKey
    || typeof legacy.sessionId !== "string"
    || typeof legacy.expiresAt !== "string"
    || !Array.isArray(legacy.entries)
    || legacy.entries.length === 0
    || !isSessionActive(legacy.expiresAt, now)
  ) {
    return [];
  }

  const entries = legacy.entries.filter(isChatEntry);
  if (entries.length === 0) return [];
  const lastEntry = entries[entries.length - 1];
  const updatedAt = lastEntry.role === "assistant" ? lastEntry.message.createdAt : legacy.expiresAt;
  return [{
    id: legacy.sessionId,
    userKey,
    sessionId: legacy.sessionId,
    expiresAt: legacy.expiresAt,
    title: conversationTitle(entries),
    updatedAt,
    entries,
  }];
}

function isSessionActive(expiresAt: string, now: Date): boolean {
  return Date.parse(expiresAt) > now.getTime();
}

function parseJson(raw: string | null): unknown {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isConversation(value: unknown): value is ChatConversation {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.userKey === "string"
    && typeof value.sessionId === "string"
    && typeof value.expiresAt === "string"
    && typeof value.title === "string"
    && typeof value.updatedAt === "string"
    && Array.isArray(value.entries)
    && value.entries.every(isChatEntry);
}

function isChatEntry(value: unknown): value is ChatEntry {
  if (!isRecord(value) || typeof value.id !== "string") return false;
  if (value.role === "user") return typeof value.content === "string";
  return value.role === "assistant"
    && isRecord(value.message)
    && typeof value.message.content === "string"
    && typeof value.message.createdAt === "string";
}
