// @vitest-environment happy-dom
import * as React from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";

import { AndroidDownload } from "../src/components/AndroidDownload.web";
import { AndroidDownload as NativeDownload } from "../src/components/AndroidDownload";

afterEach(() => vi.unstubAllEnvs());

it("offers the supplied Android build as a keyboard accessible web link without requiring login", async () => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  const root = createRoot(container);
  try {
    await act(async () => root.render(React.createElement(AndroidDownload)));
    const link = container.querySelector("a");
    expect(link?.textContent).toBe("Descargar para Android");
    expect(link?.href).toBe("https://expo.dev/accounts/donmathiuz/projects/ai-assisted-news-app/builds/33425211-31ac-4a45-bda4-e33dcbcbe6fc");
    expect(link?.tabIndex).toBe(0);
    expect(container.textContent).toContain("Expo");
    await act(async () => root.render(React.createElement(NativeDownload)));
    expect(container.childElementCount).toBe(0);
  } finally {
    await act(async () => root.unmount());
    vi.unstubAllGlobals();
  }
});

it("uses the APK download injected by the release pipeline", async () => {
  vi.stubEnv("EXPO_PUBLIC_ANDROID_DOWNLOAD_URL", "https://expo.dev/artifacts/eas/new-release.apk");
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  const root = createRoot(container);
  try {
    await act(async () => root.render(React.createElement(AndroidDownload)));
    expect(container.querySelector("a")?.href).toBe("https://expo.dev/artifacts/eas/new-release.apk");
    expect(container.textContent).toContain("Descarga el APK");
  } finally {
    await act(async () => root.unmount());
    vi.unstubAllGlobals();
  }
});
