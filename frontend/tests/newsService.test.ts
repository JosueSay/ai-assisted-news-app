import { afterEach, describe, expect, it, vi } from "vitest";

import type { NewsArticle } from "../src/types";
import {
  fetchNewsFeedWithStatus,
  getArticleBySlug,
  getFeaturedArticles,
  searchArticles,
} from "../src/services/newsService";

const articles: NewsArticle[] = [
  {
    id: "1",
    slug: "sensores-huertos-urbanos",
    title: "Jóvenes desarrollan sensores para cuidar los huertos urbanos",
    summary: "Sensores de bajo costo para riego comunitario.",
    category: "tecnologia",
    author: "Redacción",
    publishedAt: "2026-10-04T07:20:00-06:00",
    body: ["Primer párrafo.", "Segundo párrafo."],
    readingMinutes: 2,
    source: "MongoDB",
    image: {
      src: null,
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
    author: "Redacción",
    publishedAt: "2026-10-03T07:20:00-06:00",
    body: ["Contenido."],
    readingMinutes: 1,
    source: "MongoDB",
    image: {
      src: null,
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
