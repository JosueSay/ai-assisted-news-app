import { describe, expect, it } from "vitest";
import { checkDeployConfig } from "../scripts/check-deploy-config.cjs";
const environment = {
  EXPO_PUBLIC_FIREBASE_API_KEY: "public-fixture",
  EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN: "news-test.firebaseapp.com",
  EXPO_PUBLIC_FIREBASE_PROJECT_ID: "news-test",
  EXPO_PUBLIC_FIREBASE_APP_ID: "public-app-fixture",
  EXPO_PUBLIC_NEWS_API_BASE_URL: "https://news-api.example.test",
  EXPO_PUBLIC_ASSISTANT_API_BASE_URL: "https://news-chat.example.test",
};

describe("Hosting build configuration", () => {
  it("accepts a matching Firebase project and deployed HTTPS APIs", () => {
    expect(checkDeployConfig(environment, "news-test")).toEqual([]);
  });
  it("rejects missing Firebase settings and a mismatched Hosting project", () => {
    const errors = checkDeployConfig({ ...environment, EXPO_PUBLIC_FIREBASE_API_KEY: "" }, "other-project");
    expect(errors.join(" ")).toContain("EXPO_PUBLIC_FIREBASE_API_KEY");
    expect(errors.join(" ")).toContain("NEWS_FIREBASE_PROJECT_ID");
  });
  it.each(["http://news.example.test", "https://localhost:8020", "https://127.0.0.1", "https://[::1]", "invalid", "https://user:pass@example.test", "https://example.test?token=fixture"])(
    "rejects unsuitable API URLs without including their values: %s", (url) => {
      const errors = checkDeployConfig({ ...environment, EXPO_PUBLIC_NEWS_API_BASE_URL: url }, "news-test");
      expect(errors).toHaveLength(1);
      expect(errors[0]).toContain("EXPO_PUBLIC_NEWS_API_BASE_URL");
      expect(errors[0]).not.toContain(url);
    },
  );
});
