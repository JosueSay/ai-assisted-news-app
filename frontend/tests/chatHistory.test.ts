import { describe, expect, it } from "vitest";

import {
  articleOpeningPrompt,
  conversationTitle,
  readConversations,
  type ChatConversation,
} from "../src/features/chat/chatHistory";

const now = new Date("2026-10-17T12:00:00Z");

describe("chat history", () => {
  it("opens a contextual chat with an explicit article title", () => {
    expect(articleOpeningPrompt("Mercado digital en Guatemala")).toBe(
      "Explícame esta noticia: Mercado digital en Guatemala",
    );
  });

  it("titles conversations from their article or first user message", () => {
    expect(conversationTitle([], "Mercado digital en Guatemala")).toBe(
      "Mercado digital en Guatemala",
    );
    expect(
      conversationTitle([{ id: "1", role: "user", content: "Noticias de Japón" }]),
    ).toBe("Noticias de Japón");
  });

  it("restores only the current user's unexpired conversations", () => {
    const valid: ChatConversation = {
      id: "local-1",
      userKey: "guest:ana",
      sessionId: "session-1",
      expiresAt: "2026-10-17T12:30:00Z",
      title: "Noticias de Japón",
      updatedAt: "2026-10-17T11:30:00Z",
      entries: [{ id: "entry-1", role: "user", content: "Noticias de Japón" }],
    };
    const expired = { ...valid, id: "expired", expiresAt: "2026-10-17T11:59:59Z" };
    const otherUser = { ...valid, id: "other-user", userKey: "guest:alguien" };

    expect(
      readConversations(JSON.stringify([valid, expired, otherUser]), null, "guest:ana", now),
    ).toEqual([valid]);
  });

  it("migrates the existing single-session storage format", () => {
    const legacy = {
      userKey: "guest:ana",
      sessionId: "session-1",
      expiresAt: "2026-10-17T12:30:00Z",
      entries: [{ id: "entry-1", role: "user", content: "Noticias de Japón" }],
    };

    expect(readConversations(null, JSON.stringify(legacy), "guest:ana", now)).toMatchObject([
      {
        id: "session-1",
        sessionId: "session-1",
        title: "Noticias de Japón",
        userKey: "guest:ana",
      },
    ]);
  });
});
