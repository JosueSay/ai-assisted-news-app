// @vitest-environment happy-dom

import * as React from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { NewsArticle } from "../src/types";

type LayoutEvent = { nativeEvent: { layout: { y: number; height: number } } };
const native = vi.hoisted(() => ({
  layouts: new Set<(event: LayoutEvent) => void>(),
  width: 1200,
  os: "web",
  keyboard: new Map<string, () => void>(),
}));

// Keep React's real effects and state; replace native rendering and external I/O.
vi.mock("react-native", async () => {
  const React = await import("react");
  type Props = {
    children?: React.ReactNode;
    onPress?: () => void;
    onLayout?: (event: LayoutEvent) => void;
    accessibilityLabel?: string;
    disabled?: boolean;
    ref?: React.Ref<unknown>;
  };
  function View({ children, onLayout }: Props) {
    React.useEffect(() => {
      if (onLayout) native.layouts.add(onLayout);
      return () => { if (onLayout) native.layouts.delete(onLayout); };
    }, [onLayout]);
    return React.createElement("div", null, children);
  }
  function ScrollView(props: Props) {
    React.useImperativeHandle(props.ref, () => ({ scrollTo() {} }));
    return React.createElement(View, props);
  }
  return {
    View,
    ScrollView,
    KeyboardAvoidingView: View,
    Text: ({ children }: Props) => React.createElement("span", null, children),
    Pressable: ({ children, onPress, accessibilityLabel, disabled }: Props) =>
      React.createElement("button", { onClick: onPress, "aria-label": accessibilityLabel, disabled }, children),
    TextInput: () => null,
    ActivityIndicator: () => null,
    AppState: { currentState: "active", addEventListener: () => ({ remove() {} }) },
    Keyboard: { addListener: (event: string, callback: () => void) => {
      native.keyboard.set(event, callback);
      return { remove: () => native.keyboard.delete(event) };
    } },
    Platform: { get OS() { return native.os; } },
    StyleSheet: { create: (styles: unknown) => styles },
    useWindowDimensions: () => ({ width: native.width, height: 800 }),
  };
});
vi.mock("react-native-safe-area-context", async () => ({
  SafeAreaView: (await import("react-native")).View,
}));
vi.mock("lucide-react-native", () => Object.fromEntries(
  ["ArrowLeft", "Bookmark", "BookmarkCheck", "FilePlus", "Home", "LogOut", "MessageCircle", "Search", "X"]
    .map((name) => [name, () => null]),
));
vi.mock("@react-native-async-storage/async-storage", () => ({
  default: { getItem: async () => null, setItem: async () => undefined },
}));
vi.mock("../src/components/ArticleImage", () => ({ ArticleImage: () => null }));
vi.mock("../src/features/chat/ChatScreen", () => ({
  ChatScreen: ({ isKeyboardVisible }: { isKeyboardVisible?: boolean }) =>
    React.createElement("section", { "data-testid": "chat", "data-keyboard": String(Boolean(isKeyboardVisible)) }),
}));
vi.mock("../src/services/firebaseClient", () => ({
  getCurrentFirebaseIdToken: async () => "verified-test-token",
}));

import { NewsFeedScreen } from "../src/features/news/NewsFeedScreen";

const first: NewsArticle = {
  id: "1", slug: "first", title: "Primera noticia", summary: "Resumen",
  category: "tecnologia", topics: ["tecnologia"], geographicScope: null,
  verification: null, sources: [],
  aiAssistance: { summaryGenerated: false, topicsGenerated: false, imageGenerated: false, humanReviewed: false },
  author: "Redacción", publishedAt: "2026-10-20T12:00:00Z", body: ["Contenido."],
  readingMinutes: 1, source: "Prueba",
  image: { src: null, type: "none", aiDisclosure: null, alt: "", width: 960, height: 540, credit: "", sourceUrl: "", license: "" },
};
const second = { ...first, id: "2", slug: "second", title: "Segunda noticia" };
let serverFeed: NewsArticle[];
let root: Root;
let container: HTMLDivElement;
let finishExit: () => void;
let finishRead: () => void;
let exitGate: Promise<void>;
let readGate: Promise<void>;
let feedRequests: number;
let readRequests: number;
let exitDuration: number | undefined;
let exitStatus: number;

beforeEach(() => {
  native.width = 1200;
  native.os = "web";
  native.keyboard.clear();
  vi.useFakeTimers();
  vi.stubGlobal("React", React);
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  window.history.replaceState(null, "", "#/inicio");
  serverFeed = [first, second];
  feedRequests = 0;
  readRequests = 0;
  exitDuration = undefined;
  exitStatus = 200;
  exitGate = new Promise((resolve) => { finishExit = resolve; });
  readGate = new Promise((resolve) => { finishRead = resolve; });
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const path = new URL(input).pathname;
    if (path === "/news") {
      feedRequests += 1;
      return { ok: true, json: async () => [...serverFeed] };
    }
    if (path === "/profile") return { ok: true, json: async () => ({
      locationId: "country", locationName: "Guatemala", selectedTopics: [],
      inferredInterests: [], onboardingCompleted: true,
    }) };
    if (path === "/locations") return { ok: true, json: async () => [] };
    if (path.endsWith("/opened")) {
      const payload = JSON.parse(String(init?.body));
      if (payload.dwellTimeSeconds !== undefined) {
        exitDuration = payload.dwellTimeSeconds;
        await exitGate;
        return { ok: exitStatus === 200, status: exitStatus };
      }
      return { ok: true };
    }
    if (path.endsWith("/read")) {
      readRequests += 1;
      await readGate;
      return { ok: true };
    }
    if (path === "/news/first") return { ok: true, json: async () => first };
    throw new Error(`Unexpected request: ${path}`);
  }));
  container = document.createElement("div");
  document.body.append(container);
  root = createRoot(container);
});

afterEach(async () => {
  await act(async () => { root.unmount(); });
  finishRead();
  finishExit();
  container.remove();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

async function render() {
  await act(async () => {
    root.render(React.createElement(NewsFeedScreen, {
      user: { id: "reader", name: "Reader", email: "reader@example.test", isGuest: false, role: "user" },
      onSignOut() {},
    }));
  });
}

async function press(label: string) {
  const button = [...container.querySelectorAll("button")].find((item) =>
    item.getAttribute("aria-label") === label || item.textContent === label);
  expect(button, label).toBeDefined();
  await act(async () => { button!.click(); });
}

async function reachReadThreshold() {
  await act(async () => {
    for (const onLayout of native.layouts) {
      onLayout({ nativeEvent: { layout: { y: 0, height: 300 } } });
    }
    await vi.advanceTimersByTimeAsync(6000);
  });
  expect(readRequests).toBe(1);
}

function leadTitle() {
  return container.querySelector('button[aria-label^="Abrir noticia:"]')?.getAttribute("aria-label");
}

describe("feed after reading", () => {
  it("waits for final dwell time before showing the updated ranking on return", async () => {
    await render();
    await press("Abrir noticia: Primera noticia");
    await act(async () => { await vi.advanceTimersByTimeAsync(35000); });
    await press("Inicio");

    expect(exitDuration).toBe(35);
    expect(feedRequests).toBe(1);
    serverFeed = [second, first];
    await act(async () => { finishExit(); });

    expect(feedRequests).toBe(2);
    expect(leadTitle()).toBe("Abrir noticia: Segunda noticia");
  });

  it("keeps the article open after read succeeds and refreshes on browser back", async () => {
    await render();
    await press("Abrir noticia: Primera noticia");
    await act(async () => { finishRead(); });
    await reachReadThreshold();

    expect(feedRequests).toBe(1);
    expect(container.textContent).toContain("Contenido.");
    await act(async () => {
      window.history.replaceState(null, "", "#/inicio");
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(feedRequests).toBe(1);
    serverFeed = [second, first];
    await act(async () => { finishExit(); });

    expect(feedRequests).toBe(2);
    expect(leadTitle()).toBe("Abrir noticia: Segunda noticia");
  });

  it("refreshes again when an in-flight read finishes after returning home", async () => {
    await render();
    await press("Abrir noticia: Primera noticia");
    await reachReadThreshold();
    await act(async () => { finishExit(); });
    await press("Inicio");
    const requestsBeforeRead = feedRequests;
    serverFeed = [second, first];
    await act(async () => { finishRead(); });

    expect(feedRequests).toBeGreaterThan(requestsBeforeRead);
    expect(leadTitle()).toBe("Abrir noticia: Segunda noticia");
  });

  it("still refreshes a completed read if sending the final dwell time fails", async () => {
    await render();
    await press("Abrir noticia: Primera noticia");
    await act(async () => { finishRead(); });
    await reachReadThreshold();
    exitStatus = 503;
    await press("Inicio");
    serverFeed = [second, first];
    await act(async () => { finishExit(); });

    expect(feedRequests).toBe(2);
    expect(leadTitle()).toBe("Abrir noticia: Segunda noticia");
  });

  it("loads an initial article link even when the article is outside the feed", async () => {
    window.history.replaceState(null, "", "#/noticia/first");
    serverFeed = [second];

    await render();

    expect(feedRequests).toBe(1);
    expect(container.textContent).toContain("Contenido.");
  });
});

describe("mobile assistant navigation", () => {
  it("opens the assistant first in the Android app and hides navigation while typing", async () => {
    native.os = "android";
    native.width = 390;
    await render();
    expect(container.querySelector('[data-testid="chat"]')).not.toBeNull();
    expect([...container.querySelectorAll("button")].some(button => button.textContent === "Guardados")).toBe(true);
    await act(async () => { native.keyboard.get("keyboardDidShow")?.(); });
    expect(container.querySelector('[data-testid="chat"]')?.getAttribute("data-keyboard")).toBe("true");
    expect([...container.querySelectorAll("button")].some(button => button.textContent === "Guardados")).toBe(false);
    await act(async () => { native.keyboard.get("keyboardDidHide")?.(); });
    expect([...container.querySelectorAll("button")].some(button => button.textContent === "Guardados")).toBe(true);
    await press("Inicio");
    expect(leadTitle()).toBe("Abrir noticia: Primera noticia");
    await press("Asistente");
    expect(container.querySelector('[data-testid="chat"]')).not.toBeNull();
  });
  it("opens the assistant on mobile web without an explicit route", async () => {
    native.width = 390;
    window.history.replaceState(null, "", "/");
    await render();
    expect(container.querySelector('[data-testid="chat"]')).not.toBeNull();
  });
  it("keeps the desktop home page and explicit mobile links", async () => {
    window.history.replaceState(null, "", "/");
    await render();
    expect(leadTitle()).toBe("Abrir noticia: Primera noticia");
    native.width = 390;
    await act(async () => {
      window.history.replaceState(null, "", "#/noticia/first");
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(container.textContent).toContain("Contenido.");
  });
});
