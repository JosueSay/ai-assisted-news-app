import { afterEach, describe, expect, it, vi } from "vitest";

import {
  isSessionActive,
  sendChatMessage,
} from "../src/services/chatService";

vi.mock("../src/services/firebaseClient", () => ({
  getCurrentFirebaseIdToken: vi.fn(async () => "verified-firebase-id-token"),
}));

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("chatService", () => {
  it("treats expired or missing sessions as inactive", () => {
    const now = new Date("2026-10-11T12:00:00Z");
    expect(isSessionActive("2026-10-11T12:30:00Z", now)).toBe(true);
    expect(isSessionActive("2026-10-11T11:59:59Z", now)).toBe(false);
    expect(isSessionActive(null, now)).toBe(false);
  });

  it("posts only chat context and authenticates with the current Firebase ID token", async () => {
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
      message: "Explícame esta noticia: Mercado digital en Guatemala",
      sessionId: "670000000000000000000301",
      newsId: "670000000000000000000101",
    });

    expect(result).toEqual(reply);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/chat$/);
    expect(JSON.parse(init.body)).toEqual({
      message: "Explícame esta noticia: Mercado digital en Guatemala",
      sessionId: "670000000000000000000301",
      newsId: "670000000000000000000101",
      locationId: null,
    });
    expect(init.headers.Authorization).toBe("Bearer verified-firebase-id-token");
  });

  it("surfaces the API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "La noticia no existe o no está publicada." }),
      }),
    );

    await expect(sendChatMessage({ message: "explica" })).rejects.toThrow(
      "La noticia no existe o no está publicada.",
    );
  });
});

it("does not send a client-supplied role or identity to the chat API", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetchMock);
  await sendChatMessage({ message: "noticias" });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer verified-firebase-id-token");
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).not.toHaveProperty("user");
});
