import { afterEach, describe, expect, it, vi } from "vitest";

import type { AppUser } from "../src/types";
import {
  chatExternalUserId,
  isSessionActive,
  sendChatMessage,
} from "../src/services/chatService";

const guest: AppUser = {
  id: "0b6f6c0e-1111-4c1e-9a55-2d1f0f7f9a10",
  name: "Invitado",
  email: "invitado@local.news",
  isGuest: true,
  role: "user",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("chatService", () => {
  it("builds provisional external ids for each kind of user", () => {
    expect(chatExternalUserId(guest)).toBe("guest:0b6f6c0e-1111-4c1e-9a55-2d1f0f7f9a10");
    expect(
      chatExternalUserId({ id: "1234", name: "Ana", email: "ana@example.com", isGuest: false }),
    ).toBe("google:1234");
    expect(
      chatExternalUserId({
        id: "admin:admin",
        name: "Admin admin",
        email: "admin@local.admin",
        isGuest: false,
        role: "admin",
      }),
    ).toBe("admin:admin");
  });

  it("treats expired or missing sessions as inactive", () => {
    const now = new Date("2026-10-11T12:00:00Z");
    expect(isSessionActive("2026-10-11T12:30:00Z", now)).toBe(true);
    expect(isSessionActive("2026-10-11T11:59:59Z", now)).toBe(false);
    expect(isSessionActive(null, now)).toBe(false);
  });

  it("posts the message with session, article and user context", async () => {
    const reply = {
      sessionId: "670000000000000000000301",
      expiresAt: "2026-10-11T13:00:00Z",
      locationId: "670000000000000000000201",
      message: {
        content: "Estas son las noticias más recientes:",
        strategy: "database_query",
        intent: "recent_news",
        confidence: "high",
        uncertainty: null,
        aiUsed: false,
        citedNews: [],
        createdAt: "2026-10-11T12:00:00Z",
      },
    };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => reply });
    vi.stubGlobal("fetch", fetchMock);

    const result = await sendChatMessage({
      message: "últimas noticias",
      user: guest,
      sessionId: "670000000000000000000301",
      newsId: "670000000000000000000101",
    });

    expect(result).toEqual(reply);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/chat$/);
    expect(JSON.parse(init.body)).toEqual({
      message: "últimas noticias",
      sessionId: "670000000000000000000301",
      newsId: "670000000000000000000101",
      locationId: null,
      user: {
        id: "guest:0b6f6c0e-1111-4c1e-9a55-2d1f0f7f9a10",
        displayName: "Invitado",
        email: "invitado@local.news",
        photoUrl: "",
      },
    });
  });

  it("surfaces the API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "La noticia no existe o no está publicada." }),
      }),
    );

    await expect(sendChatMessage({ message: "explica", user: guest })).rejects.toThrow(
      "La noticia no existe o no está publicada.",
    );
  });
});

it("sends the admin Bearer token to reuse the API author identity", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetchMock);
  await sendChatMessage({ message: "noticias", user: {
    ...guest, id: "admin:admin", role: "admin", isGuest: false, adminToken: "fixture-token",
  } });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer fixture-token");
});
