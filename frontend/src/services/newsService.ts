import type { CategoryId, NewsArticle } from "../types";

export type NewsFeedResult = {
  articles: NewsArticle[];
  error: string | null;
};

export type NewsLocation = {
  id: string;
  name: string;
  country: string;
  countryCode: string;
  level: "city" | "region" | "country" | "international";
};

export type AdminSession = {
  accessToken: string;
  tokenType: "Bearer";
  expiresIn: number;
  username: string;
};

export type AdminNewsCreateInput = {
  title: string;
  slug: string;
  summary: string;
  content: string;
  topic: CategoryId;
  keywords: string[];
  locationId: string;
  status: "draft" | "published";
  verificationStatus:
    | "confirmed"
    | "developing"
    | "insufficient_sources"
    | "conflicting_sources";
  sourceName?: string;
  sourceUrl?: string;
  sourceType?: "official" | "media" | "primary_source" | "witness" | "other";
  imageUrl?: string;
  imageAlt?: string;
  imageCredit?: string;
  imageRights?: string;
};

const NEWS_API_BASE_URL =
  process.env.EXPO_PUBLIC_NEWS_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8020";

function requireApiBaseUrl() {
  if (!NEWS_API_BASE_URL) {
    throw new Error("NEWS_API_BASE_URL no está configurado.");
  }
  return NEWS_API_BASE_URL;
}

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export async function fetchNewsFeed(): Promise<NewsArticle[]> {
  const result = await fetchNewsFeedWithStatus();
  return result.articles;
}

export async function fetchNewsFeedWithStatus(): Promise<NewsFeedResult> {
  try {
    const baseUrl = requireApiBaseUrl();
    const response = await fetch(`${baseUrl}/news`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const articles = (await response.json()) as NewsArticle[];
    return {
      articles: sortByPublishedAt(articles),
      error: null,
    };
  } catch {
    return {
      articles: [],
      error: "No pudimos leer noticias desde MongoDB.",
    };
  }
}

export async function loginAdmin(username: string, password: string): Promise<AdminSession> {
  const baseUrl = requireApiBaseUrl();
  const response = await fetch(`${baseUrl}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(response.status === 401 ? "Credenciales admin inválidas." : "No pudimos iniciar sesión admin.");
  }
  return (await response.json()) as AdminSession;
}

export async function fetchLocations(): Promise<NewsLocation[]> {
  const baseUrl = requireApiBaseUrl();
  const response = await fetch(`${baseUrl}/locations`);
  if (!response.ok) {
    throw new Error("No pudimos cargar ubicaciones.");
  }
  return (await response.json()) as NewsLocation[];
}

export async function createAdminNews(
  token: string,
  input: AdminNewsCreateInput,
): Promise<NewsArticle> {
  const baseUrl = requireApiBaseUrl();
  const response = await fetch(`${baseUrl}/admin/news`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    let message = "No pudimos crear la noticia.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the generic message when the server does not return JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as NewsArticle;
}

function sortByPublishedAt(articles: NewsArticle[]): NewsArticle[] {
  return [...articles].sort(
    (first, second) =>
      new Date(second.publishedAt).getTime() - new Date(first.publishedAt).getTime(),
  );
}

export function getArticleBySlug(slug: string, articles: NewsArticle[] = []) {
  return articles.find((article) => article.slug === slug) ?? null;
}

export function getFeaturedArticles(articles: NewsArticle[] = []) {
  const [lead, ...rest] = articles;
  return {
    lead,
    secondary: rest.slice(0, 2),
  };
}

export function getLatestArticles(articles: NewsArticle[] = [], limit = 6) {
  return [...articles]
    .sort(
      (first, second) =>
        new Date(second.publishedAt).getTime() - new Date(first.publishedAt).getTime(),
    )
    .slice(0, limit);
}

export function getArticlesByCategory(category: CategoryId, articles: NewsArticle[] = []) {
  return articles.filter((article) => article.category === category);
}

export function searchArticles(query: string, articles: NewsArticle[] = []) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];

  return articles.filter((article) => {
    const searchable = normalizeText(
      `${article.title} ${article.summary} ${article.category} ${article.author}`,
    );
    return searchable.includes(normalizedQuery);
  });
}

export function getRelatedArticles(article: NewsArticle, articles: NewsArticle[] = []) {
  return articles
    .filter((candidate) => candidate.category === article.category && candidate.id !== article.id)
    .slice(0, 3);
}
