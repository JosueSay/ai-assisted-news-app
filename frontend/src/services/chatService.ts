import type { AppUser } from "../types";

import type { ResponseStrategy, ResponseIntent, ConfidenceLevel, VerificationStatus }
  from "../generated/newsContract";

export type ChatStrategy = ResponseStrategy;
export type ChatIntent = ResponseIntent;
export type ChatConfidence = ConfidenceLevel;

export type ChatCitedNews = {
  id: string;
  slug: string;
  title: string;
  verificationStatus: VerificationStatus;
};

export type ChatAssistantMessage = {
  content: string;
  strategy: ChatStrategy;
  intent: ChatIntent;
  confidence: ChatConfidence;
  uncertainty: string | null;
  aiUsed: boolean;
  citedNews: ChatCitedNews[];
  createdAt: string;
};

export type ChatReply = {
  sessionId: string;
  expiresAt: string;
  locationId: string;
  message: ChatAssistantMessage;
};

export type ChatSendInput = {
  message: string;
  user: AppUser;
  sessionId?: string | null;
  newsId?: string | null;
  locationId?: string | null;
};

// Chatbot del assistant (backend/assistant) en modo news.
const ASSISTANT_API_BASE_URL =
  process.env.EXPO_PUBLIC_ASSISTANT_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8010";

/**
 * Identificador externo provisional que la API guarda en users.firebaseUid
 * mientras Firebase Authentication no esté implementado.
 */
export function chatExternalUserId(user: AppUser): string {
  if (user.role === "admin") return user.id;
  return `${user.isGuest ? "guest" : "google"}:${user.id}`;
}

/** Una sesión vence en el servidor a la hora; se descarta antes de reenviarla. */
export function isSessionActive(expiresAt: string | null, now: Date = new Date()): boolean {
  if (!expiresAt) return false;
  return new Date(expiresAt).getTime() > now.getTime();
}

export async function sendChatMessage(input: ChatSendInput): Promise<ChatReply> {
  const response = await fetch(`${ASSISTANT_API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(input.user.adminToken ? { Authorization: `Bearer ${input.user.adminToken}` } : {}),
    },
    body: JSON.stringify({
      message: input.message,
      sessionId: input.sessionId ?? null,
      newsId: input.newsId ?? null,
      locationId: input.locationId ?? null,
      user: {
        id: chatExternalUserId(input.user),
        displayName: input.user.name,
        email: input.user.email,
        photoUrl: input.user.photoUrl ?? "",
      },
    }),
  });
  if (!response.ok) {
    let message = "El asistente no pudo responder. Intenta de nuevo.";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Se conserva el mensaje genérico cuando el servidor no devuelve JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as ChatReply;
}
