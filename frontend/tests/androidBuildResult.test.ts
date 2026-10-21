import { describe, expect, it } from "vitest";
import { readApkBuildUrl } from "../scripts/android-build-result.cjs";

const build = {
  status: "FINISHED", platform: "ANDROID", buildProfile: "apk", distribution: "INTERNAL",
  app: { id: "test-eas-project" },
  artifacts: { buildUrl: "https://expo.dev/artifacts/eas/test-release.apk" },
};
describe("publish only a finished APK from the linked EAS project", () => {
  it("returns the direct download for the completed Android build", () => {
    expect(readApkBuildUrl([build], "test-eas-project")).toBe(build.artifacts.buildUrl);
  });
  it.each([
    [], [build, build], [{ ...build, status: "ERRORED" }],
    [{ ...build, platform: "IOS" }], [{ ...build, app: { id: "another-project" } }],
    [{ ...build, buildProfile: "development" }],
    [{ ...build, artifacts: {} }],
    [{ ...build, artifacts: { buildUrl: "https://expo.dev/artifacts/eas/test.aab" } }],
    [{ ...build, artifacts: { buildUrl: "https://attacker.invalid/test.apk" } }],
    [{ ...build, artifacts: { buildUrl: "https://expo.dev/artifacts/eas/test.apk\nEVIL=1" } }],
  ].map(result => ({ result })))("rejects incomplete or mismatched results: %j", ({ result }) => {
    expect(() => readApkBuildUrl(result, "test-eas-project")).toThrow();
  });
});
