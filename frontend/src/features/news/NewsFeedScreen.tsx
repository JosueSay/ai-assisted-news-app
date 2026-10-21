import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AppState,
  ActivityIndicator,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  type KeyboardTypeOptions,
  useWindowDimensions,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  FilePlus,
  Home,
  LogOut,
  MessageCircle,
  Search,
  X,
} from "lucide-react-native";

import { ArticleCard } from "../../components/ArticleCard";
import { ArticleImage } from "../../components/ArticleImage";
import { AppButton } from "../../components/AppButton";
import { ChatScreen } from "../chat/ChatScreen";
import {
  CATEGORIES,
  getCategoryLabel,
  type AppUser,
  type CategoryId,
  type NewsArticle,
} from "../../types";
import {
  createAdminNews,
  fetchNewsFeedWithStatus,
  fetchNewsArticleBySlug,
  fetchLocations,
  fetchNewsProfile,
  getArticleBySlug,
  getArticlesByCategory,
  getFeaturedArticles,
  getLatestArticles,
  getRelatedArticles,
  searchArticles,
  recordNewsInteraction,
  updateNewsProfile,
  type AdminNewsCreateInput,
  type NewsLocation,
  type NewsProfile,
} from "../../services/newsService";
import { getCurrentFirebaseIdToken } from "../../services/firebaseClient";
import {
  activeReadingSeconds as calculateActiveReadingSeconds,
  articleVisibleFraction,
  shortArticleReadComplete,
} from "./readingProgress";
import { colors, fonts, layout, radii, shadows, spacing } from "../../theme";

type Props = {
  user: AppUser;
  onSignOut: () => void;
};

type NewsRoute =
  | { name: "home" }
  | { name: "saved" }
  | { name: "adminCreate" }
  | { name: "chat"; slug?: string }
  | { name: "category"; category: CategoryId }
  | { name: "article"; slug: string };

const SAVED_STORAGE_KEY = "ai-news:saved-articles";
const DEFAULT_ADMIN_FORM = {
  title: "",
  slug: "",
  summary: "",
  content: "",
  topic: "actualidad" as CategoryId,
  keywords: "",
  locationId: "",
  status: "published" as AdminNewsCreateInput["status"],
  verificationStatus: "confirmed" as AdminNewsCreateInput["verificationStatus"],
  sourceType: "other" as NonNullable<AdminNewsCreateInput["sourceType"]>,
  sourceName: "",
  sourceUrl: "",
  imageUrl: "",
  imageAlt: "",
  imageCredit: "",
  imageRights: "",
};

type AdminFormState = typeof DEFAULT_ADMIN_FORM;

function isCategoryId(value: string): value is CategoryId {
  return CATEGORIES.some((category) => category.id === value);
}

function serializeRoute(route: NewsRoute) {
  switch (route.name) {
    case "home":
      return "#/inicio";
    case "saved":
      return "#/guardados";
    case "adminCreate":
      return "#/admin/nueva";
    case "chat":
      return route.slug ? `#/asistente/${route.slug}` : "#/asistente";
    case "category":
      return `#/seccion/${route.category}`;
    case "article":
      return `#/noticia/${route.slug}`;
  }
}

function parseRouteFromHash(hash: string, mobileDefault = false): NewsRoute {
  const cleanHash = hash.replace(/^#\/?/, "");
  if (!cleanHash) return { name: mobileDefault ? "chat" : "home" };
  if (cleanHash === "inicio") return { name: "home" };
  if (cleanHash === "secciones") return { name: "home" };
  if (cleanHash === "guardados") return { name: "saved" };
  if (cleanHash === "admin" || cleanHash === "admin/nueva") return { name: "adminCreate" };
  if (cleanHash.startsWith("buscar")) return { name: "home" };
  if (cleanHash === "asistente") return { name: "chat" };
  if (cleanHash.startsWith("asistente/")) {
    return { name: "chat", slug: cleanHash.replace("asistente/", "") };
  }
  if (cleanHash.startsWith("seccion/")) {
    const category = cleanHash.replace("seccion/", "");
    return isCategoryId(category) ? { name: "category", category } : { name: "home" };
  }
  if (cleanHash.startsWith("noticia/")) {
    return { name: "article", slug: cleanHash.replace("noticia/", "") };
  }
  return { name: "home" };
}

function getInitialRoute(isMobile: boolean): NewsRoute {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    return parseRouteFromHash(window.location.hash, isMobile);
  }
  return { name: "chat" };
}

function formatLongDate(value: string) {
  return new Date(value).toLocaleDateString("es-GT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function routeTitle(route: NewsRoute, article: NewsArticle | null) {
  if (route.name === "article" && article) return article.title;
  if (route.name === "category") return getCategoryLabel(route.category);
  if (route.name === "saved") return "Guardados";
  if (route.name === "adminCreate") return "Nueva noticia";
  if (route.name === "chat") return "Asistente";
  return "Inicio";
}

export function NewsFeedScreen({ user, onSignOut }: Props) {
  const { width } = useWindowDimensions();
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1024;
  const isDesktop = width >= 1024;

  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [rankedArticleIds, setRankedArticleIds] = useState<string[]>([]);
  const [feedRefreshKey, setFeedRefreshKey] = useState(0);
  const [isFeedLoading, setIsFeedLoading] = useState(true);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [feedError, setFeedError] = useState<string | null>(null);
  const hasLoadedFeedRef = useRef(false);
  const [route, setRoute] = useState<NewsRoute>(() => getInitialRoute(isMobile));
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [storageError, setStorageError] = useState<string | null>(null);
  const [adminForm, setAdminForm] = useState<AdminFormState>(DEFAULT_ADMIN_FORM);
  const [locations, setLocations] = useState<NewsLocation[]>([]);
  const [isLocationsLoading, setIsLocationsLoading] = useState(false);
  const [locationsError, setLocationsError] = useState<string | null>(null);
  const [isSubmittingAdminNews, setIsSubmittingAdminNews] = useState(false);
  const [adminFormError, setAdminFormError] = useState<string | null>(null);
  const [adminSuccess, setAdminSuccess] = useState<string | null>(null);
  const [profile, setProfile] = useState<NewsProfile | null>(null);
  const [profileDraft, setProfileDraft] = useState<{
    locationId: string;
    selectedTopics: CategoryId[];
  } | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState(true);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [isPreferencesOpen, setIsPreferencesOpen] = useState(false);
  const feedScrollRef = useRef<ScrollView>(null);
  const scrollYRef = useRef(0);
  const scrollViewportHeightRef = useRef(0);
  const articleContainerTopRef = useRef(0);
  const articleViewTopRef = useRef(0);
  const articleBodyLayoutRef = useRef<{ top: number; height: number } | null>(null);
  const articleBodyRelativeLayoutRef = useRef<{ y: number; height: number } | null>(null);
  const readingSessionRef = useRef<{
    slug: string;
    feedPosition: number | null;
    activeSeconds: number;
    activeSince: number | null;
    shortVisibleSeconds: number;
    shortVisibleSince: number | null;
    readSent: boolean;
    readInFlight: boolean;
  } | null>(null);
  const openedRequestRef = useRef<Promise<void> | null>(null);
  const finalReadingRequestRef = useRef<Promise<void> | null>(null);
  const pendingFeedOpenRef = useRef<{ slug: string; position: number | null } | null>(null);

  const isAdmin = user.role === "admin";
  const isReadingArticle = route.name === "article";

  useEffect(() => {
    // Keep the current detail and its reading measurements stable until leaving it.
    if (isReadingArticle && hasLoadedFeedRef.current) return;
    let active = true;
    if (!hasLoadedFeedRef.current) setIsFeedLoading(true);
    // The exit signal can add interests too; load the ranking after it settles.
    void (finalReadingRequestRef.current ?? Promise.resolve())
      .then(() => getCurrentFirebaseIdToken())
      .then((token) => fetchNewsFeedWithStatus(token))
      .then((result) => {
        if (!active) return;
        setFeedError(result.error);
        if (!result.error) {
          setArticles(result.articles);
          setRankedArticleIds(result.articles.map((article) => article.id));
          hasLoadedFeedRef.current = true;
        }
      })
      .catch(() => {
        if (!active) return;
        setFeedError("No pudimos cargar las noticias.");
      })
      .finally(() => {
        if (active) setIsFeedLoading(false);
      });
    return () => {
      active = false;
    };
  }, [feedRefreshKey, isReadingArticle]);

  useEffect(() => {
    AsyncStorage.getItem(SAVED_STORAGE_KEY)
      .then((raw) => {
        if (raw) setSavedIds(JSON.parse(raw) as string[]);
      })
      .catch(() => setStorageError("No pudimos restaurar tus guardados locales."));
  }, []);

  useEffect(() => {
    let active = true;
    setIsLocationsLoading(true);
    setLocationsError(null);
    void fetchLocations()
      .then((items) => {
        if (!active) return;
        setLocations(items);
        if (isAdmin) {
          setAdminForm((current) => ({
            ...current,
            locationId: current.locationId || items[0]?.id || "",
          }));
        }
      })
      .catch(() => {
        if (active) setLocationsError("No pudimos cargar el catálogo de ubicaciones.");
      })
      .finally(() => {
        if (active) setIsLocationsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isAdmin]);

  useEffect(() => {
    let active = true;
    setIsProfileLoading(true);
    setProfileError(null);
    void getCurrentFirebaseIdToken()
      .then(fetchNewsProfile)
      .then((nextProfile) => {
        if (!active) return;
        setProfile(nextProfile);
        setProfileDraft({
          locationId: nextProfile.locationId,
          selectedTopics: nextProfile.selectedTopics,
        });
      })
      .catch(() => {
        if (active) setProfileError("No pudimos cargar tus preferencias de noticias.");
      })
      .finally(() => {
        if (active) setIsProfileLoading(false);
      });
    return () => {
      active = false;
    };
  }, [user.id]);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") return;
    const onHashChange = () => setRoute(parseRouteFromHash(window.location.hash, isMobile));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [isMobile]);

  useEffect(() => {
    if (Platform.OS === "web") return;
    const show = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
      () => setIsKeyboardVisible(true),
    );
    const hide = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide",
      () => setIsKeyboardVisible(false),
    );
    return () => { show.remove(); hide.remove(); };
  }, []);

  const detailSlug = route.name === "article" || route.name === "chat" ? route.slug : undefined;
  const hasDetail = !detailSlug || articles.some((article) => article.slug === detailSlug);
  useEffect(() => {
    setDetailError(null);
    if (!detailSlug || hasDetail || isFeedLoading) return;
    let active = true;
    setIsDetailLoading(true);
    void fetchNewsArticleBySlug(detailSlug)
      .then((article) => {
        if (active && article) setArticles((current) => [...current, article]);
        if (active && !article) setDetailError("La noticia no existe o no está publicada.");
      })
      .catch(() => {
        if (active) setDetailError("No pudimos cargar la noticia. Intenta de nuevo.");
      })
      .finally(() => {
        if (active) setIsDetailLoading(false);
      });
    return () => { active = false; };
  }, [detailSlug, hasDetail, isFeedLoading]);

  const currentArticle = useMemo(
    () => (route.name === "article" ? getArticleBySlug(route.slug, articles) : null),
    [articles, route],
  );

  const feedPositionById = useMemo(
    () => new Map(rankedArticleIds.map((id, index) => [id, index] as const)),
    [rankedArticleIds],
  );

  const activeReadingSeconds = useCallback((session: NonNullable<typeof readingSessionRef.current>) => {
    return calculateActiveReadingSeconds(
      session.activeSeconds,
      session.activeSince,
      Date.now(),
    );
  }, []);

  const maybeRecordRead = useCallback(() => {
    const session = readingSessionRef.current;
    const body = articleBodyLayoutRef.current;
    const currentSlug = currentArticle?.slug;
    if (
      !session || !currentSlug || session.slug !== currentSlug || !body ||
      body.height <= 0 || session.readSent || session.readInFlight
    ) return;
    const visibleFraction = articleVisibleFraction(
      scrollYRef.current,
      scrollViewportHeightRef.current,
      body.top,
      body.height,
    );
    if (body.height <= scrollViewportHeightRef.current) {
      if (visibleFraction < 0.9 || AppState.currentState !== "active") {
        if (session.shortVisibleSince !== null) {
          session.shortVisibleSeconds = calculateActiveReadingSeconds(
            session.shortVisibleSeconds,
            session.shortVisibleSince,
            Date.now(),
          );
          session.shortVisibleSince = null;
        }
        return;
      }
      if (session.shortVisibleSince === null) session.shortVisibleSince = Date.now();
      const visibleActiveSeconds = calculateActiveReadingSeconds(
        session.shortVisibleSeconds,
        session.shortVisibleSince,
        Date.now(),
      );
      if (!shortArticleReadComplete(visibleFraction, visibleActiveSeconds)) return;
    } else if (visibleFraction < 0.9) {
      return;
    }

    session.readInFlight = true;
    const duration = activeReadingSeconds(session);
    void (openedRequestRef.current ?? Promise.resolve())
      .then(async () => {
        const token = await getCurrentFirebaseIdToken();
        await recordNewsInteraction(token, session.slug, "read", {
          dwellTimeSeconds: duration,
        });
        session.readSent = true;
        setFeedRefreshKey((value) => value + 1);
      })
      .catch(() => undefined)
      .finally(() => {
        session.readInFlight = false;
      });
  }, [activeReadingSeconds, currentArticle?.slug]);

  useEffect(() => {
    if (route.name !== "article" || !currentArticle) return;
    const session = {
      slug: currentArticle.slug,
      feedPosition:
        pendingFeedOpenRef.current?.slug === currentArticle.slug
          ? pendingFeedOpenRef.current.position
          : null,
      activeSeconds: 0,
      activeSince: AppState.currentState === "active" ? Date.now() : null,
      shortVisibleSeconds: 0,
      shortVisibleSince: null,
      readSent: false,
      readInFlight: false,
    };
    pendingFeedOpenRef.current = null;
    readingSessionRef.current = session;
    articleBodyLayoutRef.current = null;
    articleBodyRelativeLayoutRef.current = null;
    scrollYRef.current = 0;
    feedScrollRef.current?.scrollTo({ y: 0, animated: false });

    openedRequestRef.current = getCurrentFirebaseIdToken()
      .then((token) => recordNewsInteraction(token, session.slug, "opened", {
        feedPosition: session.feedPosition,
      }));
    openedRequestRef.current.catch(() => undefined);
    maybeRecordRead();

    const subscription = AppState.addEventListener("change", (nextState) => {
      if (nextState === "active" && session.activeSince === null) {
        session.activeSince = Date.now();
        maybeRecordRead();
      } else if (nextState !== "active" && session.activeSince !== null) {
        session.activeSeconds += Math.floor((Date.now() - session.activeSince) / 1000);
        session.activeSince = null;
        if (session.shortVisibleSince !== null) {
          session.shortVisibleSeconds = calculateActiveReadingSeconds(
            session.shortVisibleSeconds,
            session.shortVisibleSince,
            Date.now(),
          );
          session.shortVisibleSince = null;
        }
      }
    });
    const readProgressTimer = setInterval(maybeRecordRead, 250);

    return () => {
      const duration = activeReadingSeconds(session);
      session.activeSeconds = duration;
      session.activeSince = null;
      finalReadingRequestRef.current = getCurrentFirebaseIdToken()
        .then((token) => recordNewsInteraction(token, session.slug, "opened", {
          feedPosition: session.feedPosition,
          dwellTimeSeconds: duration,
        }))
        .catch(() => undefined);
      subscription.remove();
      clearInterval(readProgressTimer);
      if (readingSessionRef.current === session) readingSessionRef.current = null;
    };
  }, [activeReadingSeconds, currentArticle?.id, maybeRecordRead, route.name]);

  useEffect(() => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      document.title = `${routeTitle(route, currentArticle)} | AI News`;
    }
  }, [currentArticle, route]);

  const navigate = useCallback((nextRoute: NewsRoute, replace = false) => {
    setRoute(nextRoute);
    if (Platform.OS !== "web" || typeof window === "undefined") return;
    const hash = serializeRoute(nextRoute);
    if (replace) {
      window.history.replaceState(null, "", hash);
    } else if (window.location.hash !== hash) {
      window.location.hash = hash;
    }
  }, []);

  const toggleSave = useCallback((article: NewsArticle) => {
    setStorageError(null);
    setSavedIds((current) => {
      const next = current.includes(article.id)
        ? current.filter((id) => id !== article.id)
        : [...current, article.id];
      AsyncStorage.setItem(SAVED_STORAGE_KEY, JSON.stringify(next)).catch(() =>
        setStorageError("No pudimos actualizar tus guardados locales."),
      );
      return next;
    });
  }, []);

  const savedArticles = useMemo(
    () => articles.filter((article) => savedIds.includes(article.id)),
    [articles, savedIds],
  );

  const openArticle = useCallback((article: NewsArticle) => {
    const originatesInHomeFeed = route.name === "home" && !searchQuery.trim();
    pendingFeedOpenRef.current = {
      slug: article.slug,
      position: originatesInHomeFeed ? feedPositionById.get(article.id) ?? null : null,
    };
    navigate({ name: "article", slug: article.slug });
  }, [feedPositionById, navigate, route.name, searchQuery]);

  const handleProfileChanged = useCallback((nextProfile: NewsProfile) => {
    setProfile(nextProfile);
    setProfileDraft({
      locationId: nextProfile.locationId,
      selectedTopics: nextProfile.selectedTopics,
    });
    setFeedRefreshKey((value) => value + 1);
  }, []);

  const toggleProfileTopic = useCallback((topic: CategoryId) => {
    setProfileDraft((current) => {
      if (!current) return current;
      const selectedTopics = current.selectedTopics.includes(topic)
        ? current.selectedTopics.filter((item) => item !== topic)
        : [...current.selectedTopics, topic];
      return { ...current, selectedTopics };
    });
  }, []);

  const saveProfile = useCallback(async () => {
    if (!profileDraft) return;
    setIsSavingProfile(true);
    setProfileError(null);
    try {
      const token = await getCurrentFirebaseIdToken();
      const updated = await updateNewsProfile(
        token,
        profileDraft.locationId,
        profileDraft.selectedTopics,
      );
      handleProfileChanged(updated);
      setIsPreferencesOpen(false);
    } catch (error) {
      setProfileError(
        error instanceof Error ? error.message : "No pudimos guardar tus preferencias.",
      );
    } finally {
      setIsSavingProfile(false);
    }
  }, [handleProfileChanged, profileDraft]);

  const isSaved = useCallback(
    (article: NewsArticle) => savedIds.includes(article.id),
    [savedIds],
  );

  function updateAdminField<K extends keyof AdminFormState>(
    field: K,
    value: AdminFormState[K],
  ) {
    setAdminForm((current) => ({ ...current, [field]: value }));
    setAdminFormError(null);
    setAdminSuccess(null);
  }

  function buildAdminInput(): AdminNewsCreateInput | null {
    const title = adminForm.title.trim();
    const summary = adminForm.summary.trim();
    const content = adminForm.content.trim();
    const locationId = adminForm.locationId.trim();
    const sourceName = adminForm.sourceName.trim();
    const sourceUrl = adminForm.sourceUrl.trim();

    if (!title || !summary || !content || !locationId) {
      setAdminFormError("Completa título, resumen, contenido y ubicación.");
      return null;
    }
    if (Boolean(sourceName) !== Boolean(sourceUrl)) {
      setAdminFormError("La fuente necesita nombre y URL juntos.");
      return null;
    }

    return {
      title,
      slug: adminForm.slug.trim(),
      summary,
      content,
      topic: adminForm.topic,
      keywords: adminForm.keywords
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      locationId,
      status: adminForm.status,
      verificationStatus: adminForm.verificationStatus,
      sourceName: sourceName || undefined,
      sourceUrl: sourceUrl || undefined,
      sourceType: adminForm.sourceType,
      imageUrl: adminForm.imageUrl.trim() || undefined,
      imageAlt: adminForm.imageAlt.trim() || undefined,
      imageCredit: adminForm.imageCredit.trim() || undefined,
      imageRights: adminForm.imageRights.trim() || undefined,
    };
  }

  const submitAdminNews = useCallback(async () => {
    if (!isAdmin) {
      setAdminFormError("Inicia sesión como admin para crear noticias.");
      return;
    }
    const input = buildAdminInput();
    if (!input) return;

    setIsSubmittingAdminNews(true);
    setAdminFormError(null);
    setAdminSuccess(null);
    try {
      const idToken = await getCurrentFirebaseIdToken();
      const created = await createAdminNews(idToken, input);
      if (input.status === "published") {
        setArticles((current) => [
          created,
          ...current.filter((article) => article.id !== created.id),
        ]);
      }
      setAdminSuccess(
        input.status === "published"
          ? "Noticia publicada y agregada al feed local."
          : "Borrador guardado en MongoDB.",
      );
      setAdminForm({
        ...DEFAULT_ADMIN_FORM,
        locationId: input.locationId,
        topic: input.topic,
      });
    } catch (error) {
      setAdminFormError(
        error instanceof Error ? error.message : "No pudimos crear la noticia.",
      );
    } finally {
      setIsSubmittingAdminNews(false);
    }
  }, [adminForm, isAdmin]);

  const renderNotice = () => (
    <>
      <Text style={styles.notice}>Feed conectado a MongoDB</Text>
      {feedError ? <Text style={styles.warningText}>{feedError}</Text> : null}
    </>
  );

  const renderSectionTitle = (title: string, kicker?: string) => (
    <View style={styles.sectionHeading}>
      {kicker ? <Text style={styles.kicker}>{kicker}</Text> : null}
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );

  const renderCategoryChips = () => (
    <View style={styles.chips}>
      {CATEGORIES.map((category) => {
        const active = route.name === "category" && route.category === category.id;
        return (
          <Pressable
            key={category.id}
            accessibilityRole="button"
            accessibilityState={{ selected: active }}
            onPress={() => navigate({ name: "category", category: category.id })}
            style={({ pressed }) => [
              styles.chip,
              active ? styles.chipActive : null,
              pressed ? styles.pressed : null,
            ]}
          >
            <Text style={[styles.chipLabel, active ? styles.chipLabelActive : null]}>
              {category.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );

  const renderPreferences = () => {
    if (!profile) {
      return isProfileLoading ? (
        <View style={styles.preferencesPanel}>
          <ActivityIndicator color={colors.action} />
          <Text style={styles.formHint}>Cargando tus preferencias de noticias.</Text>
        </View>
      ) : profileError ? (
        <Text accessibilityRole="alert" style={styles.errorText}>{profileError}</Text>
      ) : null;
    }

    if (profile.onboardingCompleted && !isPreferencesOpen) {
      return (
        <AppButton
          label={`Personalizar feed · ${profile.locationName}`}
          variant="secondary"
          onPress={() => setIsPreferencesOpen(true)}
        />
      );
    }

    return (
      <View style={styles.preferencesPanel}>
        <View style={styles.preferencesHeader}>
          <View style={styles.preferencesHeading}>
            <Text style={styles.preferencesTitle}>
              {profile.onboardingCompleted ? "Personaliza tu feed" : "Configura tu feed"}
            </Text>
            <Text style={styles.formHint}>
              Elige manualmente una ubicación y los temas que quieres seguir. No usamos GPS.
            </Text>
          </View>
          {profile.onboardingCompleted ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Cerrar preferencias"
              onPress={() => setIsPreferencesOpen(false)}
              style={({ pressed }) => [styles.preferenceClose, pressed ? styles.pressed : null]}
            >
              <X size={20} color={colors.textSecondary} />
            </Pressable>
          ) : null}
        </View>
        {profileError ? <Text accessibilityRole="alert" style={styles.errorText}>{profileError}</Text> : null}
        {locationsError ? <Text accessibilityRole="alert" style={styles.errorText}>{locationsError}</Text> : null}
        {isProfileLoading || isLocationsLoading ? (
          <View style={styles.inlineLoading}>
            <ActivityIndicator color={colors.action} />
            <Text style={styles.formHint}>Cargando opciones.</Text>
          </View>
        ) : (
          <>
            <Text style={styles.fieldLabel}>Ubicación</Text>
            <View style={styles.formChips}>
              {locations.map((location) => {
                const selected = profileDraft?.locationId === location.id;
                return (
                  <Pressable
                    key={location.id}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    onPress={() => setProfileDraft((current) => current
                      ? { ...current, locationId: location.id }
                      : current)}
                    style={({ pressed }) => [
                      styles.formChip,
                      selected ? styles.formChipActive : null,
                      pressed ? styles.pressed : null,
                    ]}
                  >
                    <Text style={[styles.formChipLabel, selected ? styles.formChipLabelActive : null]}>
                      {location.name}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            <Text style={styles.fieldLabel}>Temas</Text>
            <View style={styles.formChips}>
              {CATEGORIES.map((category) => {
                const selected = Boolean(profileDraft?.selectedTopics.includes(category.id));
                return (
                  <Pressable
                    key={category.id}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    onPress={() => toggleProfileTopic(category.id)}
                    style={({ pressed }) => [
                      styles.formChip,
                      selected ? styles.formChipActive : null,
                      pressed ? styles.pressed : null,
                    ]}
                  >
                    <Text style={[styles.formChipLabel, selected ? styles.formChipLabelActive : null]}>
                      {category.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            <AppButton
              label={isSavingProfile ? "Guardando…" : "Guardar preferencias"}
              onPress={() => void saveProfile()}
              disabled={isSavingProfile || !profileDraft || locations.length === 0}
            />
          </>
        )}
      </View>
    );
  };

  const renderInlineSearch = () => (
    <View style={styles.searchBox}>
      <Search size={20} color={colors.textSecondary} />
      <TextInput
        accessibilityLabel="Buscar noticias"
        placeholder="Buscar por tema, categoría o titular"
        placeholderTextColor={colors.textSecondary}
        value={searchQuery}
        onChangeText={setSearchQuery}
        style={styles.searchInput}
        returnKeyType="search"
      />
      {searchQuery.trim() ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Limpiar búsqueda"
          hitSlop={8}
          onPress={() => setSearchQuery("")}
          style={({ pressed }) => [styles.clearSearchButton, pressed ? styles.pressed : null]}
        >
          <X size={18} color={colors.textSecondary} />
        </Pressable>
      ) : null}
    </View>
  );

  const renderArticleGrid = (items: NewsArticle[]) => (
    <View style={styles.articleGrid}>
      {items.map((article) => (
        <View
          key={article.id}
          style={[
            styles.gridItem,
            isDesktop ? styles.gridItemDesktop : isTablet ? styles.gridItemTablet : null,
          ]}
        >
          <ArticleCard
            article={article}
            isSaved={isSaved(article)}
            onOpen={openArticle}
            onToggleSave={toggleSave}
            variant={isMobile ? "compact" : "standard"}
          />
        </View>
      ))}
    </View>
  );

  function updateAdminTextField(field: keyof AdminFormState, value: string) {
    setAdminForm((current) => ({ ...current, [field]: value }));
    setAdminFormError(null);
    setAdminSuccess(null);
  }

  const renderAdminTextField = ({
    label,
    field,
    placeholder,
    multiline = false,
    keyboardType = "default",
  }: {
    label: string;
    field: keyof AdminFormState;
    placeholder: string;
    multiline?: boolean;
    keyboardType?: KeyboardTypeOptions;
  }) => (
    <View style={styles.fieldGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        autoCapitalize="sentences"
        autoCorrect
        editable={!isSubmittingAdminNews}
        keyboardType={keyboardType}
        multiline={multiline}
        onChangeText={(value) => updateAdminTextField(field, value)}
        placeholder={placeholder}
        placeholderTextColor={colors.textSecondary}
        style={[styles.formInput, multiline ? styles.formTextArea : null]}
        textAlignVertical={multiline ? "top" : "center"}
        value={String(adminForm[field])}
      />
    </View>
  );

  const renderAdminOption = (
    label: string,
    active: boolean,
    onPress: () => void,
    optionKey?: string,
  ) => (
    <Pressable
      key={optionKey}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.formChip,
        active ? styles.formChipActive : null,
        pressed ? styles.pressed : null,
      ]}
    >
      <Text style={[styles.formChipLabel, active ? styles.formChipLabelActive : null]}>
        {label}
      </Text>
    </Pressable>
  );

  const renderAdminCreate = () => {
    if (!isAdmin) {
      return (
        <>
          {renderNotice()}
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>Acceso admin requerido</Text>
            <Text style={styles.emptyText}>
              Inicia sesión con una cuenta admin para crear noticias en MongoDB.
            </Text>
            <AppButton label="Volver al inicio" onPress={() => navigate({ name: "home" })} />
          </View>
        </>
      );
    }

    const selectedLocation = locations.find((location) => location.id === adminForm.locationId);

    return (
      <>
        {renderNotice()}
        <AppButton
          label="Volver al inicio"
          variant="ghost"
          onPress={() => navigate({ name: "home" })}
          icon={<ArrowLeft size={18} color={colors.action} />}
        />

        <View style={styles.adminShell}>
          <View style={styles.adminIntro}>
            <Text style={styles.kicker}>Panel admin</Text>
            <Text style={styles.adminTitle}>Nueva noticia</Text>
            <Text style={styles.adminCopy}>
              Crea una pieza manual con ubicación simulada, verificación y fuente.
              Los borradores quedan guardados, pero solo las publicadas aparecen en el feed.
            </Text>
          </View>

          <View style={styles.adminForm}>
            {adminFormError ? <Text style={styles.errorText}>{adminFormError}</Text> : null}
            {adminSuccess ? <Text style={styles.successText}>{adminSuccess}</Text> : null}

            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Contenido</Text>
              {renderAdminTextField({
                label: "Título",
                field: "title",
                placeholder: "Titular de la noticia",
              })}
              {renderAdminTextField({
                label: "Slug",
                field: "slug",
                placeholder: "se-genera-desde-el-titulo-si-lo-dejas-vacio",
              })}
              {renderAdminTextField({
                label: "Resumen",
                field: "summary",
                placeholder: "Una entradilla breve y clara",
                multiline: true,
              })}
              {renderAdminTextField({
                label: "Contenido",
                field: "content",
                placeholder: "Escribe la noticia completa. Separa párrafos con una línea vacía.",
                multiline: true,
              })}
              {renderAdminTextField({
                label: "Palabras clave",
                field: "keywords",
                placeholder: "local, comunidad, transporte",
              })}
            </View>

            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Clasificación</Text>
              <Text style={styles.fieldLabel}>Categoría</Text>
              <View style={styles.formChips}>
                {CATEGORIES.map((category) =>
                  renderAdminOption(
                    category.label,
                    adminForm.topic === category.id,
                    () => updateAdminField("topic", category.id),
                    category.id,
                  ),
                )}
              </View>

              <Text style={styles.fieldLabel}>Estado</Text>
              <View style={styles.formChips}>
                {renderAdminOption("Publicar ahora", adminForm.status === "published", () =>
                  updateAdminField("status", "published"),
                )}
                {renderAdminOption("Guardar borrador", adminForm.status === "draft", () =>
                  updateAdminField("status", "draft"),
                )}
              </View>

              <Text style={styles.fieldLabel}>Verificación</Text>
              <View style={styles.formChips}>
                {renderAdminOption("Confirmada", adminForm.verificationStatus === "confirmed", () =>
                  updateAdminField("verificationStatus", "confirmed"),
                )}
                {renderAdminOption("En desarrollo", adminForm.verificationStatus === "developing", () =>
                  updateAdminField("verificationStatus", "developing"),
                )}
                {renderAdminOption(
                  "Fuentes insuficientes",
                  adminForm.verificationStatus === "insufficient_sources",
                  () => updateAdminField("verificationStatus", "insufficient_sources"),
                )}
                {renderAdminOption(
                  "Fuentes en conflicto",
                  adminForm.verificationStatus === "conflicting_sources",
                  () => updateAdminField("verificationStatus", "conflicting_sources"),
                )}
              </View>
            </View>

            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Ubicación</Text>
              {isLocationsLoading ? (
                <View style={styles.inlineLoading}>
                  <ActivityIndicator color={colors.action} />
                  <Text style={styles.emptyText}>Cargando ubicaciones</Text>
                </View>
              ) : null}
              {locationsError ? <Text style={styles.errorText}>{locationsError}</Text> : null}
              {!isLocationsLoading && locations.length === 0 ? (
                <Text style={styles.warningText}>
                  Ejecuta el seeder de catálogo para crear ubicaciones antes de publicar.
                </Text>
              ) : null}
              <View style={styles.formChips}>
                {locations.map((location) =>
                  renderAdminOption(
                    location.name,
                    adminForm.locationId === location.id,
                    () => updateAdminField("locationId", location.id),
                    location.id,
                  ),
                )}
              </View>
              {selectedLocation ? (
                <Text style={styles.formHint}>
                  Seleccionada: {selectedLocation.country} ({selectedLocation.countryCode})
                </Text>
              ) : null}
            </View>

            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Fuente e imagen</Text>
              {renderAdminTextField({
                label: "Nombre de fuente",
                field: "sourceName",
                placeholder: "Medio, institución o fuente primaria",
              })}
              {renderAdminTextField({
                label: "URL de fuente",
                field: "sourceUrl",
                placeholder: "https://example.com/noticia",
                keyboardType: "url",
              })}
              <Text style={styles.fieldLabel}>Tipo de fuente</Text>
              <View style={styles.formChips}>
                {renderAdminOption("Oficial", adminForm.sourceType === "official", () =>
                  updateAdminField("sourceType", "official"),
                )}
                {renderAdminOption("Medio", adminForm.sourceType === "media", () =>
                  updateAdminField("sourceType", "media"),
                )}
                {renderAdminOption("Primaria", adminForm.sourceType === "primary_source", () =>
                  updateAdminField("sourceType", "primary_source"),
                )}
                {renderAdminOption("Testigo", adminForm.sourceType === "witness", () =>
                  updateAdminField("sourceType", "witness"),
                )}
                {renderAdminOption("Otra", adminForm.sourceType === "other", () =>
                  updateAdminField("sourceType", "other"),
                )}
              </View>
              {renderAdminTextField({
                label: "URL de imagen",
                field: "imageUrl",
                placeholder: "https://example.com/imagen.jpg",
                keyboardType: "url",
              })}
              {renderAdminTextField({
                label: "Texto alternativo de imagen",
                field: "imageAlt",
                placeholder: "Describe la imagen si agregas una URL",
              })}
              {renderAdminTextField({
                label: "Crédito de imagen",
                field: "imageCredit",
                placeholder: "Autor, medio o licencia",
              })}
              {renderAdminTextField({
                label: "Derechos de imagen",
                field: "imageRights",
                placeholder: "Uso permitido, licencia o nota interna",
              })}
            </View>

            <View style={styles.adminActions}>
              <AppButton
                label={isSubmittingAdminNews ? "Guardando..." : "Guardar noticia"}
                onPress={() => void submitAdminNews()}
                disabled={isSubmittingAdminNews || isLocationsLoading || locations.length === 0}
                icon={<FilePlus size={18} color={colors.onSolid} />}
              />
              <AppButton
                label="Limpiar"
                variant="secondary"
                onPress={() =>
                  setAdminForm({
                    ...DEFAULT_ADMIN_FORM,
                    locationId: adminForm.locationId,
                  })
                }
                disabled={isSubmittingAdminNews}
              />
            </View>
          </View>
        </View>
      </>
    );
  };

  const renderHome = () => {
    const hasSearch = searchQuery.trim().length > 0;
    const searchResults = hasSearch ? searchArticles(searchQuery, articles) : [];
    const featured = getFeaturedArticles(articles);
    const latest = getLatestArticles(articles, 6);
    const categoryArticles = CATEGORIES.map((category) => ({
      ...category,
      articles: getArticlesByCategory(category.id, articles).slice(0, 3),
    }));
    const hasArticles = articles.length > 0;

    return (
      <>
        {renderNotice()}
        {renderInlineSearch()}
        {renderPreferences()}
        {hasSearch ? (
          <View style={styles.searchResultsBlock}>
            <Text style={styles.resultsTitle}>Resultados</Text>
            {searchResults.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyTitle}>No encontramos coincidencias</Text>
                <Text style={styles.emptyText}>
                  Revisa la escritura o prueba con una categoría distinta.
                </Text>
                <AppButton
                  label="Limpiar búsqueda"
                  variant="secondary"
                  onPress={() => setSearchQuery("")}
                />
              </View>
            ) : (
              <>
                <Text style={styles.resultsCount}>
                  {searchResults.length} resultado{searchResults.length === 1 ? "" : "s"}
                </Text>
                {renderArticleGrid(searchResults)}
              </>
            )}
          </View>
        ) : (
          <>
            {hasArticles ? renderCategoryChips() : null}

            {!hasArticles ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyTitle}>No hay noticias publicadas</Text>
                <Text style={styles.emptyText}>
                  El feed ahora lee únicamente desde MongoDB. Crea una noticia desde el
                  panel admin o publica documentos en la colección `news`.
                </Text>
                {isAdmin ? (
                  <AppButton
                    label="Crear noticia"
                    onPress={() => navigate({ name: "adminCreate" })}
                    icon={<FilePlus size={18} color={colors.onSolid} />}
                  />
                ) : null}
              </View>
            ) : null}

            {hasArticles ? (
            <View style={[styles.hero, isDesktop ? styles.heroDesktop : null]}>
              {featured.lead ? (
                <View style={styles.heroLead}>
                  <ArticleCard
                    article={featured.lead}
                    isSaved={isSaved(featured.lead)}
                    onOpen={openArticle}
                    onToggleSave={toggleSave}
                    variant="lead"
                  />
                </View>
              ) : null}

              <View style={[styles.heroSecondary, isTablet ? styles.heroSecondaryTablet : null]}>
                {featured.secondary.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    isSaved={isSaved(article)}
                    onOpen={openArticle}
                    onToggleSave={toggleSave}
                    variant={isMobile ? "compact" : "secondary"}
                  />
                ))}
              </View>
            </View>
            ) : null}

            {hasArticles ? (
            <View style={styles.section}>
              {renderSectionTitle("Más noticias para ti", "Siguientes en tu feed")}
              <View style={styles.latestList}>
                {latest.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    isSaved={isSaved(article)}
                    onOpen={openArticle}
                    onToggleSave={toggleSave}
                    variant="compact"
                  />
                ))}
              </View>
            </View>
            ) : null}

            {hasArticles ? categoryArticles.map((category) => (
              <View key={category.id} style={styles.section}>
                <View style={styles.sectionRow}>
                  {renderSectionTitle(category.label, "Sección")}
                  <AppButton
                    label="Ver todo"
                    variant="ghost"
                    onPress={() => navigate({ name: "category", category: category.id })}
                  />
                </View>
                {renderArticleGrid(category.articles)}
              </View>
            )) : null}
          </>
        )}
      </>
    );
  };

  const renderCategory = (category: CategoryId) => {
    const items = getArticlesByCategory(category, articles);
    return (
      <>
        {renderNotice()}
        <AppButton
          label="Volver al inicio"
          variant="ghost"
          onPress={() => navigate({ name: "home" })}
          icon={<ArrowLeft size={18} color={colors.action} />}
        />
        {renderSectionTitle(getCategoryLabel(category), "Sección")}
        {renderArticleGrid(items)}
      </>
    );
  };

  const renderSaved = () => (
    <>
      {renderNotice()}
      {renderSectionTitle("Guardados", "Lectura pendiente")}
      {storageError ? <Text style={styles.errorText}>{storageError}</Text> : null}
      {savedArticles.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Todavía no tienes noticias guardadas</Text>
          <Text style={styles.emptyText}>
            Usa el botón de marcador en cualquier noticia para verla aquí después.
          </Text>
          <AppButton label="Ir al inicio" onPress={() => navigate({ name: "home" })} />
        </View>
      ) : (
        renderArticleGrid(savedArticles)
      )}
    </>
  );

  const renderArticle = () => {
    if (!currentArticle) {
      return (
        <>
          {renderNotice()}
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No encontramos esta noticia</Text>
            <Text style={styles.emptyText}>
              Puede que el enlace esté incompleto o que la pieza ya no exista en MongoDB.
            </Text>
            <AppButton label="Volver al inicio" onPress={() => navigate({ name: "home" })} />
          </View>
        </>
      );
    }

    const related = getRelatedArticles(currentArticle, articles);
    const saved = isSaved(currentArticle);

    return (
      <>
        {renderNotice()}
        <AppButton
          label="Volver"
          variant="ghost"
          onPress={() => {
            if (Platform.OS === "web" && typeof window !== "undefined" && window.history.length > 1) {
              window.history.back();
            } else {
              navigate({ name: "home" });
            }
          }}
          icon={<ArrowLeft size={18} color={colors.action} />}
        />

        <View
          style={styles.articleView}
          onLayout={(event) => {
            articleViewTopRef.current = event.nativeEvent.layout.y;
            const bodyLayout = articleBodyRelativeLayoutRef.current;
            if (bodyLayout) {
              articleBodyLayoutRef.current = {
                top: articleContainerTopRef.current + articleViewTopRef.current + bodyLayout.y,
                height: bodyLayout.height,
              };
              maybeRecordRead();
            }
          }}
        >
          <Text style={styles.category}>{getCategoryLabel(currentArticle.category)}</Text>
          <Text style={styles.articleTitle}>{currentArticle.title}</Text>
          <Text style={styles.articleSummary}>{currentArticle.summary}</Text>
          <Text style={styles.articleMeta}>
            {currentArticle.author} · {formatLongDate(currentArticle.publishedAt)} ·{" "}
            {currentArticle.readingMinutes} min de lectura
          </Text>

          <ArticleImage image={currentArticle.image} size="lead" />
          <Text style={styles.credit}>{currentArticle.image.credit}</Text>
          {currentArticle.image.aiDisclosure ? (
            <Text style={styles.credit}>{currentArticle.image.aiDisclosure}</Text>
          ) : null}
          {currentArticle.verification ? (
            <Text style={styles.articleMeta}>
              Verificación: {{
                confirmed: "Confirmada",
                developing: "En desarrollo",
                insufficient_sources: "Fuentes insuficientes",
                conflicting_sources: "Fuentes contradictorias",
              }[currentArticle.verification.status]}
            </Text>
          ) : null}
          {currentArticle.sources.map((source) => (
            <Text key={source.url} style={styles.credit}>Fuente: {source.name} · {source.url}</Text>
          ))}

          <Pressable
            accessibilityRole="button"
            accessibilityState={{ selected: saved }}
            onPress={() => toggleSave(currentArticle)}
            style={({ pressed }) => [styles.saveInline, pressed ? styles.pressed : null]}
          >
            {saved ? (
              <BookmarkCheck size={20} color={colors.action} />
            ) : (
              <Bookmark size={20} color={colors.action} />
            )}
            <Text style={styles.saveInlineLabel}>
              {saved ? "Guardada" : "Guardar noticia"}
            </Text>
          </Pressable>

          <AppButton
            label="Preguntar al asistente"
            variant="secondary"
            onPress={() => navigate({ name: "chat", slug: currentArticle.slug })}
            icon={<MessageCircle size={18} color={colors.action} />}
          />

          <View
            style={styles.readerBody}
            onLayout={(event) => {
              const { y, height } = event.nativeEvent.layout;
              articleBodyRelativeLayoutRef.current = { y, height };
              articleBodyLayoutRef.current = {
                top: articleContainerTopRef.current
                  + articleViewTopRef.current
                  + y,
                height,
              };
              maybeRecordRead();
            }}
          >
            {currentArticle.body.map((paragraph) => (
              <Text key={paragraph} style={styles.paragraph}>
                {paragraph}
              </Text>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          {renderSectionTitle("Relacionadas", getCategoryLabel(currentArticle.category))}
          {renderArticleGrid(related)}
        </View>
      </>
    );
  };

  const renderContent = () => {
    if (isFeedLoading || (detailSlug && !hasDetail && (isDetailLoading || !detailError))) {
      return renderLoading();
    }
    if (detailSlug && !hasDetail && detailError) {
      return (
        <View style={styles.emptyState}>
          <Text accessibilityRole="alert" style={styles.emptyText}>{detailError}</Text>
          <AppButton label="Volver al inicio" onPress={() => navigate({ name: "home" })} />
        </View>
      );
    }
    if (route.name === "adminCreate") return renderAdminCreate();
    if (route.name === "saved") return renderSaved();
    if (route.name === "chat") {
      return (
        <ChatScreen
          isKeyboardVisible={isKeyboardVisible}
          user={user}
          contextArticle={route.slug ? getArticleBySlug(route.slug, articles) : null}
          onClearContext={() => navigate({ name: "chat" }, true)}
          onOpenArticle={(slug) => navigate({ name: "article", slug })}
          onProfileChanged={handleProfileChanged}
        />
      );
    }
    if (route.name === "category") return renderCategory(route.category);
    if (route.name === "article") return renderArticle();
    return renderHome();
  };

  const activeBottom =
    route.name === "adminCreate"
      ? "admin"
      : route.name === "saved"
        ? "saved"
        : route.name === "chat"
          ? "chat"
          : "home";

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => navigate({ name: isMobile ? "chat" : "home" })}
          style={({ pressed }) => [styles.brand, pressed ? styles.pressed : null]}
        >
          <Text style={styles.brandName}>AI News</Text>
          <View style={styles.brandUnderline} />
        </Pressable>

        {!isMobile ? (
          <View style={styles.headerNav}>
            <AppButton label="Inicio" variant="ghost" onPress={() => navigate({ name: "home" })} />
            <AppButton
              label={`Guardados (${savedIds.length})`}
              variant="ghost"
              onPress={() => navigate({ name: "saved" })}
            />
            <AppButton
              label="Asistente"
              variant="ghost"
              onPress={() => navigate({ name: "chat" })}
              icon={<MessageCircle size={18} color={colors.action} />}
            />
            {isAdmin ? (
              <AppButton
                label="Nueva noticia"
                variant="ghost"
                onPress={() => navigate({ name: "adminCreate" })}
                icon={<FilePlus size={18} color={colors.action} />}
              />
            ) : null}
          </View>
        ) : null}

        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Cerrar sesión de ${user.name}`}
          hitSlop={10}
          onPress={onSignOut}
          style={({ pressed }) => [styles.signOut, pressed ? styles.pressed : null]}
        >
          <LogOut size={20} color={colors.textSecondary} />
          {!isMobile ? <Text style={styles.signOutLabel}>Salir</Text> : null}
        </Pressable>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.contentFrame}
      >
        {route.name === "chat" ? (
          <View style={[styles.container, styles.chatContainer]}>{renderContent()}</View>
        ) : (
          <ScrollView
            ref={feedScrollRef}
            onLayout={(event) => {
              scrollViewportHeightRef.current = event.nativeEvent.layout.height;
              maybeRecordRead();
            }}
            onScroll={(event) => {
              scrollYRef.current = event.nativeEvent.contentOffset.y;
              scrollViewportHeightRef.current = event.nativeEvent.layoutMeasurement.height;
              maybeRecordRead();
            }}
            scrollEventThrottle={100}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={[
              styles.scrollContent,
              isMobile ? styles.scrollContentMobile : null,
            ]}
          >
            <View
              style={styles.container}
              onLayout={(event) => {
                articleContainerTopRef.current = event.nativeEvent.layout.y;
                const bodyLayout = articleBodyRelativeLayoutRef.current;
                if (bodyLayout) {
                  articleBodyLayoutRef.current = {
                    top: articleContainerTopRef.current + articleViewTopRef.current + bodyLayout.y,
                    height: bodyLayout.height,
                  };
                  maybeRecordRead();
                }
              }}
            >
              {renderContent()}
            </View>
          </ScrollView>
        )}
      </KeyboardAvoidingView>

      {isMobile && !isKeyboardVisible ? (
        <View style={styles.bottomNav}>
          <BottomNavItem
            label="Inicio"
            active={activeBottom === "home"}
            icon={<Home size={20} color={activeBottom === "home" ? colors.action : colors.textSecondary} />}
            onPress={() => navigate({ name: "home" })}
          />
          <BottomNavItem
            label="Guardados"
            active={activeBottom === "saved"}
            icon={
              <Bookmark
                size={20}
                color={activeBottom === "saved" ? colors.action : colors.textSecondary}
              />
            }
            onPress={() => navigate({ name: "saved" })}
          />
          <BottomNavItem
            label="Asistente"
            active={activeBottom === "chat"}
            icon={
              <MessageCircle
                size={20}
                color={activeBottom === "chat" ? colors.action : colors.textSecondary}
              />
            }
            onPress={() => navigate({ name: "chat" })}
          />
          {isAdmin ? (
            <BottomNavItem
              label="Crear"
              active={activeBottom === "admin"}
              icon={
                <FilePlus
                  size={20}
                  color={activeBottom === "admin" ? colors.action : colors.textSecondary}
                />
              }
              onPress={() => navigate({ name: "adminCreate" })}
            />
          ) : null}
        </View>
      ) : null}
    </SafeAreaView>
  );
}

function renderLoading() {
  return (
    <>
      <Text style={styles.notice}>Feed conectado a MongoDB</Text>
      <View style={styles.loadingState}>
        <ActivityIndicator color={colors.action} />
        <Text style={styles.loadingTitle}>Cargando noticias</Text>
        <Text style={styles.emptyText}>Leyendo el feed desde MongoDB.</Text>
      </View>
    </>
  );
}

function BottomNavItem({
  label,
  active,
  icon,
  onPress,
}: {
  label: string;
  active: boolean;
  icon: React.ReactNode;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.bottomNavItem,
        active ? styles.bottomNavItemActive : null,
        pressed ? styles.pressed : null,
      ]}
    >
      {icon}
      <Text style={[styles.bottomNavLabel, active ? styles.bottomNavLabelActive : null]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    minHeight: 72,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    zIndex: 2,
  },
  brand: {
    minHeight: 48,
    justifyContent: "center",
    gap: spacing.xxs,
  },
  brandName: {
    color: colors.ink,
    fontFamily: fonts.headingBold,
    fontSize: 30,
    lineHeight: 32,
  },
  brandUnderline: {
    width: 44,
    height: 3,
    backgroundColor: colors.brand,
  },
  headerNav: {
    flex: 1,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.xs,
  },
  signOut: {
    minWidth: 48,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: spacing.xs,
    borderRadius: radii.control,
  },
  signOutLabel: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
  },
  contentFrame: {
    flex: 1,
    minHeight: 0,
  },
  scrollContent: {
    paddingVertical: spacing.lg,
  },
  scrollContentMobile: {
    paddingBottom: spacing.xl,
  },
  container: {
    width: "100%",
    maxWidth: layout.maxContentWidth,
    alignSelf: "center",
    paddingHorizontal: spacing.md,
    gap: spacing.xl,
  },
  chatContainer: {
    flex: 1,
    minHeight: 0,
    paddingVertical: 0,
    gap: 0,
  },
  notice: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    lineHeight: 19,
    marginBottom: spacing.md,
  },
  warningText: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    lineHeight: 19,
    marginBottom: spacing.md,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
    marginBottom: spacing.xl,
  },
  preferencesPanel: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.panel,
    gap: spacing.md,
  },
  preferencesHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  preferencesHeading: {
    flex: 1,
    gap: spacing.xs,
  },
  preferencesTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  preferenceClose: {
    minWidth: 44,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radii.pill,
  },
  chip: {
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radii.pill,
    borderColor: colors.border,
    borderWidth: 1,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  chipActive: {
    backgroundColor: colors.actionSoft,
    borderColor: colors.action,
  },
  chipLabel: {
    color: colors.ink,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
  },
  chipLabelActive: {
    color: colors.action,
  },
  hero: {
    gap: spacing.xl,
  },
  heroDesktop: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  heroLead: {
    flex: 2,
  },
  heroSecondary: {
    gap: spacing.lg,
    flex: 1,
  },
  heroSecondaryTablet: {
    flexDirection: "row",
  },
  section: {
    marginTop: spacing["3xl"],
    gap: spacing.md,
  },
  sectionHeading: {
    gap: spacing.xxs,
  },
  kicker: {
    color: colors.brand,
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    letterSpacing: 0.72,
    textTransform: "uppercase",
  },
  sectionTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 30,
    lineHeight: 35,
  },
  sectionRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: spacing.md,
  },
  latestList: {
    gap: spacing.md,
  },
  articleGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.lg,
  },
  gridItem: {
    width: "100%",
  },
  gridItemTablet: {
    flexBasis: "47%",
    flexGrow: 1,
  },
  gridItemDesktop: {
    flexBasis: "30%",
    flexGrow: 1,
  },
  directory: {
    gap: spacing.sm,
  },
  directoryItem: {
    minHeight: 72,
    padding: spacing.md,
    borderRadius: radii.panel,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  directoryTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  directoryMeta: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
  },
  directoryAction: {
    color: colors.action,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
  },
  searchBox: {
    minHeight: 52,
    paddingHorizontal: spacing.md,
    borderRadius: radii.control,
    borderWidth: 1,
    borderColor: colors.controlBorder,
    backgroundColor: colors.surface,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  searchInput: {
    flex: 1,
    minHeight: 48,
    color: colors.ink,
    fontFamily: fonts.body,
    fontSize: 16,
  },
  clearSearchButton: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radii.pill,
  },
  resultsCount: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    marginVertical: spacing.md,
  },
  searchResultsBlock: {
    marginTop: spacing.xl,
    gap: spacing.md,
  },
  resultsTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 30,
    lineHeight: 35,
  },
  emptyState: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.panel,
    gap: spacing.sm,
    ...shadows.panel,
  },
  loadingState: {
    minHeight: 220,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.panel,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    ...shadows.panel,
  },
  loadingTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  emptyTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  emptyText: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 16,
    lineHeight: 25,
  },
  errorText: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    lineHeight: 21,
  },
  successText: {
    color: colors.success,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    lineHeight: 21,
  },
  adminShell: {
    gap: spacing.xl,
  },
  adminIntro: {
    maxWidth: layout.readerWidth,
    gap: spacing.sm,
  },
  adminTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 38,
    lineHeight: 42,
  },
  adminCopy: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 16,
    lineHeight: 25,
  },
  adminForm: {
    width: "100%",
    maxWidth: 920,
    padding: spacing.lg,
    borderRadius: radii.panel,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    gap: spacing.lg,
    ...shadows.panel,
  },
  formSection: {
    gap: spacing.sm,
  },
  formSectionTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  fieldGroup: {
    gap: spacing.xs,
  },
  fieldLabel: {
    color: colors.text,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    lineHeight: 20,
  },
  formInput: {
    minHeight: 48,
    borderColor: colors.controlBorder,
    borderRadius: radii.control,
    borderWidth: 1,
    color: colors.text,
    fontFamily: fonts.body,
    fontSize: 16,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
  },
  formTextArea: {
    minHeight: 116,
    lineHeight: 24,
  },
  formChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  formChip: {
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radii.pill,
    borderColor: colors.border,
    borderWidth: 1,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  formChipActive: {
    backgroundColor: colors.actionSoft,
    borderColor: colors.action,
  },
  formChipLabel: {
    color: colors.text,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    lineHeight: 20,
  },
  formChipLabelActive: {
    color: colors.action,
  },
  formHint: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 13,
    lineHeight: 20,
  },
  inlineLoading: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  adminActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  articleView: {
    width: "100%",
    maxWidth: 960,
    alignSelf: "center",
    gap: spacing.md,
  },
  category: {
    color: colors.brand,
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    letterSpacing: 0.72,
    textTransform: "uppercase",
  },
  articleTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 42,
    lineHeight: 45,
  },
  articleSummary: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 18,
    lineHeight: 28,
  },
  articleMeta: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 21,
  },
  credit: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 12,
    lineHeight: 18,
  },
  saveInline: {
    minHeight: 48,
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    borderRadius: radii.control,
    borderWidth: 1,
    borderColor: colors.action,
    backgroundColor: colors.actionSoft,
  },
  saveInlineLabel: {
    color: colors.action,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
  },
  readerBody: {
    width: "100%",
    maxWidth: layout.readerWidth,
    alignSelf: "center",
    gap: spacing.md,
    marginTop: spacing.md,
  },
  paragraph: {
    color: colors.ink,
    fontFamily: fonts.body,
    fontSize: 18,
    lineHeight: 31,
  },
  pressed: {
    opacity: 0.76,
  },
  bottomNav: {
    flexShrink: 0,
    minHeight: layout.mobileBottomNavHeight,
    paddingHorizontal: spacing.xs,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    backgroundColor: colors.surface,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
  },
  bottomNavItem: {
    flex: 1,
    minHeight: 56,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xxs,
    borderRadius: radii.control,
  },
  bottomNavItemActive: {
    backgroundColor: colors.actionSoft,
  },
  bottomNavLabel: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 12,
    lineHeight: 16,
  },
  bottomNavLabelActive: {
    color: colors.action,
  },
});
