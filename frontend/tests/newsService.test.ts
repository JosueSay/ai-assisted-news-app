import { describe, expect, it } from "vitest";

import { fetchNewsFeed } from "../src/services/newsService";

describe("fetchNewsFeed", () => {
  it("returns a non-empty list of articles with required fields", async () => {
    const articles = await fetchNewsFeed();

    expect(articles.length).toBeGreaterThan(0);
    for (const article of articles) {
      expect(article.id).toBeTruthy();
      expect(article.title).toBeTruthy();
      expect(article.source).toBeTruthy();
      expect(new Date(article.publishedAt).toString()).not.toBe("Invalid Date");
    }
  });
});
