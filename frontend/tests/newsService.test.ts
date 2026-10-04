import { describe, expect, it } from "vitest";

import { CATEGORIES } from "../src/types";
import {
  fetchNewsFeed,
  getArticleBySlug,
  searchArticles,
} from "../src/services/newsService";

describe("fetchNewsFeed", () => {
  it("returns the editorial demo dataset with required fields", async () => {
    const articles = await fetchNewsFeed();

    expect(articles).toHaveLength(20);
    for (const category of CATEGORIES) {
      expect(articles.filter((article) => article.category === category.id)).toHaveLength(4);
    }
    for (const article of articles) {
      expect(article.id).toBeTruthy();
      expect(article.slug).toBeTruthy();
      expect(article.title).toBeTruthy();
      expect(article.summary).toBeTruthy();
      expect(article.author).toBeTruthy();
      expect(article.body.length).toBeGreaterThanOrEqual(4);
      expect(new Date(article.publishedAt).toString()).not.toBe("Invalid Date");
      expect(article.isDemo).toBe(true);
    }
  });

  it("supports article lookup and accent-insensitive local search", async () => {
    const articles = await fetchNewsFeed();
    const article = getArticleBySlug("sensores-huertos-urbanos", articles);

    expect(article?.category).toBe("tecnologia");
    expect(searchArticles("tecnologia", articles).length).toBeGreaterThan(0);
    expect(searchArticles("bibliotecas", articles).length).toBeGreaterThan(0);
  });
});
