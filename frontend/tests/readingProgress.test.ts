import { describe, expect, it } from "vitest";

import {
  activeReadingSeconds,
  articleVisibleFraction,
  reachedReadThreshold,
  shortArticleReadComplete,
} from "../src/features/news/readingProgress";

describe("reading progress", () => {
  it("counts active seconds and stops accumulating while paused", () => {
    expect(activeReadingSeconds(4, 1_000, 5_500)).toBe(8);
    expect(activeReadingSeconds(8, null, 60_000)).toBe(8);
  });

  it("records progress when 90 percent of the body is visible or passed", () => {
    expect(articleVisibleFraction(0, 500, 100, 300)).toBe(1);
    expect(reachedReadThreshold(0, 500, 100, 300)).toBe(true);
    expect(reachedReadThreshold(0, 500, 400, 300)).toBe(false);
    expect(reachedReadThreshold(200, 500, 400, 300)).toBe(true);
  });

  it("requires five active visible seconds when the whole short article fits", () => {
    expect(shortArticleReadComplete(1, 0)).toBe(false);
    expect(shortArticleReadComplete(1, 4)).toBe(false);
    expect(shortArticleReadComplete(1, 5)).toBe(true);
    expect(shortArticleReadComplete(0.8, 10)).toBe(false);
  });
});
