import {
  DEMO_ARTICLES,
  FEATURED_ARTICLE_ID,
  SECONDARY_ARTICLE_IDS,
} from "../data/demoArticles";
import type { CategoryId, NewsArticle } from "../types";

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export async function fetchNewsFeed(): Promise<NewsArticle[]> {
  return [...DEMO_ARTICLES].sort(
    (first, second) =>
      new Date(second.publishedAt).getTime() - new Date(first.publishedAt).getTime(),
  );
}

export function getArticleBySlug(slug: string, articles = DEMO_ARTICLES) {
  return articles.find((article) => article.slug === slug) ?? null;
}

export function getFeaturedArticles(articles = DEMO_ARTICLES) {
  return {
    lead: articles.find((article) => article.id === FEATURED_ARTICLE_ID) ?? articles[0],
    secondary: SECONDARY_ARTICLE_IDS.map((id) =>
      articles.find((article) => article.id === id),
    ).filter((article): article is NewsArticle => Boolean(article)),
  };
}

export function getLatestArticles(articles = DEMO_ARTICLES, limit = 6) {
  return [...articles]
    .sort(
      (first, second) =>
        new Date(second.publishedAt).getTime() - new Date(first.publishedAt).getTime(),
    )
    .slice(0, limit);
}

export function getArticlesByCategory(category: CategoryId, articles = DEMO_ARTICLES) {
  return articles.filter((article) => article.category === category);
}

export function searchArticles(query: string, articles = DEMO_ARTICLES) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];

  return articles.filter((article) => {
    const searchable = normalizeText(
      `${article.title} ${article.summary} ${article.category} ${article.author}`,
    );
    return searchable.includes(normalizedQuery);
  });
}

export function getRelatedArticles(article: NewsArticle, articles = DEMO_ARTICLES) {
  return articles
    .filter((candidate) => candidate.category === article.category && candidate.id !== article.id)
    .slice(0, 3);
}
