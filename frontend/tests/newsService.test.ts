import { afterEach, describe, expect, it, vi } from "vitest";

import type { NewsArticle } from "../src/types";
import {
  fetchNewsFeedWithStatus,
  fetchNewsProfile,
  fetchAuthenticatedProfile,
  getArticleBySlug,
  getFeaturedArticles,
  getLatestArticles,
  recordNewsInteraction,
  searchArticles,
} from "../src/services/newsService";

const articles: NewsArticle[] = [
  {
    id: "1",
    slug: "sensores-huertos-urbanos",
    title: "Jóvenes desarrollan sensores para cuidar los huertos urbanos",
    summary: "Sensores de bajo costo para riego comunitario.",
    category: "tecnologia",
    topics: ["tecnologia"],
    geographicScope: null, verification: null, sources: [],
    aiAssistance: { summaryGenerated: false, topicsGenerated: false, imageGenerated: false, humanReviewed: false },
    author: "Redacción",
    publishedAt: "2026-10-04T07:20:00-06:00",
    body: ["Primer párrafo.", "Segundo párrafo."],
    readingMinutes: 2,
    source: "MongoDB",
    image: {
      src: null,
      type: "none", aiDisclosure: null,
      alt: "Huerto urbano",
      width: 960,
      height: 540,
      credit: "Sin imagen",
      sourceUrl: "",
      license: "Pendiente",
    },
  },
  {
    id: "2",
    slug: "bibliotecas-ruta-lectura",
    title: "Bibliotecas abren una ruta de lectura",
    summary: "Lecturas al aire libre para barrios.",
    category: "cultura",
    topics: ["cultura"],
    geographicScope: null, verification: null, sources: [],
    aiAssistance: { summaryGenerated: false, topicsGenerated: false, imageGenerated: false, humanReviewed: false },
    author: "Redacción",
    publishedAt: "2026-10-03T07:20:00-06:00",
    body: ["Contenido."],
    readingMinutes: 1,
    source: "MongoDB",
    image: {
      src: null,
      type: "none", aiDisclosure: null,
      alt: "Biblioteca",
      width: 960,
      height: 540,
      credit: "Sin imagen",
      sourceUrl: "",
      license: "Pendiente",
    },
  },
];

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("newsService", () => {
  it("resolves the server profile with a Firebase ID token", async () => {
    const profile = {
      id: "mongo-user-id",
      firebaseUid: "firebase-user-id",
      email: "reader@example.test",
      displayName: "Reader",
      photoUrl: "",
      role: "user",
    };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => profile });
    vi.stubGlobal("fetch", fetchMock);

    expect(await fetchAuthenticatedProfile("verified-id-token")).toEqual(profile);
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/auth\/me$/);
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe(
      "Bearer verified-id-token",
    );
  });

  it("fetches the feed from the configured API without local fallback data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => articles,
      })),
    );

    const result = await fetchNewsFeedWithStatus();

    expect(result.error).toBeNull();
    expect(result.articles).toHaveLength(2);
    expect(result.articles[0].slug).toBe("sensores-huertos-urbanos");
  });

  it("preserves personalized server order and sends the verified identity", async () => {
    const serverOrder = [
      { ...articles[1], feedReason: "Por tu ubicación" },
      { ...articles[0], feedReason: "Para ampliar tu cobertura" },
      { ...articles[0], id: "3" },
      { ...articles[1], id: "4" },
    ];
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      json: async () => serverOrder,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchNewsFeedWithStatus("verified-id-token");

    expect(result.articles.map((article) => article.id)).toEqual(["2", "1", "3", "4"]);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/news$/), {
      headers: { Authorization: "Bearer verified-id-token" },
    });
    expect(getLatestArticles(serverOrder, 1)[0].id).toBe("4");
  });

  it("loads the account-scoped profile with its Firebase token", async () => {
    const profile = {
      locationId: "country-id",
      locationName: "Guatemala",
      selectedTopics: ["tecnologia"],
      inferredInterests: [],
      onboardingCompleted: true,
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      json: async () => profile,
    }));
    vi.stubGlobal("fetch", fetchMock);

    expect(await fetchNewsProfile("verified-id-token")).toEqual(profile);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/profile$/), {
      headers: { Authorization: "Bearer verified-id-token" },
    });
  });

  it("retries transient interaction failures without changing the event identity", async () => {
    const fetchMock = vi.fn((_input: RequestInfo | URL, _init?: RequestInit) => Promise.resolve({ ok: true, status: 200 }))
      .mockResolvedValueOnce({ ok: false, status: 503 })
      .mockResolvedValueOnce({ ok: true, status: 200 });
    vi.stubGlobal("fetch", fetchMock);

    await recordNewsInteraction("verified-id-token", "slug-prueba", "read", {
      dwellTimeSeconds: 45,
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const request = {
      method: "POST",
      headers: {
        Authorization: "Bearer verified-id-token",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ dwellTimeSeconds: 45 }),
    };
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringMatching(/\/slug-prueba\/interactions\/read$/),
      request,
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringMatching(/\/slug-prueba\/interactions\/read$/),
      request,
    );
  });

  it("returns an empty feed when MongoDB/API cannot be read", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 })));

    const result = await fetchNewsFeedWithStatus();

    expect(result.articles).toEqual([]);
    expect(result.error).toBe("No pudimos leer noticias desde MongoDB.");
  });

  it("supports article lookup, featured selection and accent-insensitive search", () => {
    expect(getArticleBySlug("sensores-huertos-urbanos", articles)?.category).toBe(
      "tecnologia",
    );
    expect(getFeaturedArticles(articles).lead?.id).toBe("1");
    expect(searchArticles("tecnologia", articles)).toHaveLength(1);
    expect(searchArticles("bibliotecas", articles)).toHaveLength(1);
  });
});

it("filters and searches all topics instead of only the first category", async () => {
  const { getArticlesByCategory } = await import("../src/services/newsService");
  const multipleTopics = { ...articles[0], topics: ["tecnologia", "salud"] } as NewsArticle;
  expect(getArticlesByCategory("salud", [multipleTopics])).toHaveLength(1);
  expect(searchArticles("salud", [multipleTopics])).toHaveLength(1);
});

it("loads a cited article directly even when it is absent from the feed", async () => {
  const { fetchNewsArticleBySlug } = await import("../src/services/newsService");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => articles[0] });
  vi.stubGlobal("fetch", fetchMock);
  expect(await fetchNewsArticleBySlug("noticia antigua")).toEqual(articles[0]);
  expect(fetchMock.mock.calls[0][0]).toMatch(/\/news\/noticia%20antigua$/);
});

it("distinguishes a missing citation from an API failure", async () => {
  const { fetchNewsArticleBySlug } = await import("../src/services/newsService");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404 }));
  expect(await fetchNewsArticleBySlug("missing")).toBeNull();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  await expect(fetchNewsArticleBySlug("unavailable")).rejects.toThrow();
});
