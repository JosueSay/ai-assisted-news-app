import type { CategoryId, NewsArticle } from "../types";
import type {
  LocationLevel,
  NewsStatus,
  SourceType,
  UserRole,
  VerificationStatus,
} from "../generated/newsContract";

export type NewsFeedResult = {
  articles: NewsArticle[];
  error: string | null;
};

export type NewsLocation = {
  id: string;
  name: string;
  country: string;
  countryCode: string;
  level: LocationLevel;
};

export type AuthenticatedProfile = {
  id: string;
  firebaseUid: string;
  email: string;
  displayName: string;
  photoUrl: string;
  role: UserRole;
};

export type AdminNewsCreateInput = {
  title: string;
  slug: string;
  summary: string;
  content: string;
  topic: CategoryId;
  keywords: string[];
  locationId: string;
  status: NewsStatus;
  verificationStatus: VerificationStatus;
  sourceName?: string;
  sourceUrl?: string;
  sourceType?: SourceType;
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

/** Consulta el detalle aunque la noticia quede fuera de la página del feed. */
export async function fetchNewsArticleBySlug(slug: string): Promise<NewsArticle | null> {
  const response = await fetch(`${requireApiBaseUrl()}/news/${encodeURIComponent(slug)}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("No pudimos cargar la noticia.");
  return (await response.json()) as NewsArticle;
}

export async function fetchAuthenticatedProfile(idToken: string): Promise<AuthenticatedProfile> {
  const baseUrl = requireApiBaseUrl();
  const response = await fetch(`${baseUrl}/auth/me`, {
    headers: { Authorization: `Bearer ${idToken}` },
  });
  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "La sesión Firebase no es válida. Vuelve a iniciar sesión."
        : "No pudimos validar tu perfil de AI News.",
    );
  }
  return (await response.json()) as AuthenticatedProfile;
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
  return articles.filter((article) => article.topics.includes(category));
}

export function searchArticles(query: string, articles: NewsArticle[] = []) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];

  return articles.filter((article) => {
    const searchable = normalizeText(
      `${article.title} ${article.summary} ${article.topics.join(" ")} ${article.author}`,
    );
    return searchable.includes(normalizedQuery);
  });
}

export function getRelatedArticles(article: NewsArticle, articles: NewsArticle[] = []) {
  return articles
    .filter((candidate) => candidate.topics.some((topic) => article.topics.includes(topic)) && candidate.id !== article.id)
    .slice(0, 3);
}
