import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from "react-native";
import {
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Grid3X3,
  Home,
  LogOut,
  Search,
} from "lucide-react-native";

import { ArticleCard } from "../../components/ArticleCard";
import { ArticleImage } from "../../components/ArticleImage";
import { AppButton } from "../../components/AppButton";
import { CATEGORIES, type AppUser, type CategoryId, type NewsArticle } from "../../types";
import { getCategoryLabel } from "../../data/demoArticles";
import {
  fetchNewsFeed,
  getArticleBySlug,
  getArticlesByCategory,
  getFeaturedArticles,
  getLatestArticles,
  getRelatedArticles,
  searchArticles,
} from "../../services/newsService";
import { colors, fonts, layout, radii, shadows, spacing } from "../../theme";

type Props = {
  user: AppUser;
  onSignOut: () => void;
};

type NewsRoute =
  | { name: "home" }
  | { name: "sections" }
  | { name: "search"; query: string }
  | { name: "saved" }
  | { name: "category"; category: CategoryId }
  | { name: "article"; slug: string };

const SAVED_STORAGE_KEY = "ai-news:saved-articles";

function isCategoryId(value: string): value is CategoryId {
  return CATEGORIES.some((category) => category.id === value);
}

function serializeRoute(route: NewsRoute) {
  switch (route.name) {
    case "home":
      return "#/inicio";
    case "sections":
      return "#/secciones";
    case "search":
      return route.query
        ? `#/buscar?q=${encodeURIComponent(route.query)}`
        : "#/buscar";
    case "saved":
      return "#/guardados";
    case "category":
      return `#/seccion/${route.category}`;
    case "article":
      return `#/noticia/${route.slug}`;
  }
}

function parseRouteFromHash(hash: string): NewsRoute {
  const cleanHash = hash.replace(/^#\/?/, "");
  if (!cleanHash || cleanHash === "inicio") return { name: "home" };
  if (cleanHash === "secciones") return { name: "sections" };
  if (cleanHash === "guardados") return { name: "saved" };
  if (cleanHash.startsWith("buscar")) {
    const query = cleanHash.includes("?")
      ? new URLSearchParams(cleanHash.split("?")[1]).get("q") ?? ""
      : "";
    return { name: "search", query };
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

function getInitialRoute(): NewsRoute {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    return parseRouteFromHash(window.location.hash);
  }
  return { name: "home" };
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
  if (route.name === "sections") return "Secciones";
  if (route.name === "search") return "Buscar";
  if (route.name === "saved") return "Guardados";
  return "Inicio";
}

export function NewsFeedScreen({ user, onSignOut }: Props) {
  const { width } = useWindowDimensions();
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1024;
  const isDesktop = width >= 1024;
  const searchInputRef = useRef<TextInput>(null);

  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [route, setRoute] = useState<NewsRoute>(getInitialRoute);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [storageError, setStorageError] = useState<string | null>(null);

  useEffect(() => {
    void fetchNewsFeed().then(setArticles);
  }, []);

  useEffect(() => {
    AsyncStorage.getItem(SAVED_STORAGE_KEY)
      .then((raw) => {
        if (raw) setSavedIds(JSON.parse(raw) as string[]);
      })
      .catch(() => setStorageError("No pudimos restaurar tus guardados locales."));
  }, []);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") return;
    const onHashChange = () => setRoute(parseRouteFromHash(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const currentArticle = useMemo(
    () => (route.name === "article" ? getArticleBySlug(route.slug, articles) : null),
    [articles, route],
  );

  useEffect(() => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      document.title = `${routeTitle(route, currentArticle)} | AI News`;
    }
  }, [currentArticle, route]);

  useEffect(() => {
    if (route.name === "search") {
      const timeout = setTimeout(() => searchInputRef.current?.focus(), 120);
      return () => clearTimeout(timeout);
    }
    return undefined;
  }, [route.name]);

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

  const openArticle = useCallback(
    (article: NewsArticle) => navigate({ name: "article", slug: article.slug }),
    [navigate],
  );

  const isSaved = useCallback(
    (article: NewsArticle) => savedIds.includes(article.id),
    [savedIds],
  );

  const renderNotice = () => (
    <Text style={styles.notice}>Edición de demostración · Noticias ficticias</Text>
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

  const renderHome = () => {
    const featured = getFeaturedArticles(articles);
    const latest = getLatestArticles(articles, 6);
    const categoryArticles = CATEGORIES.map((category) => ({
      ...category,
      articles: getArticlesByCategory(category.id, articles).slice(0, 3),
    }));

    return (
      <>
        {renderNotice()}
        {renderCategoryChips()}

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

        <View style={styles.section}>
          {renderSectionTitle("Últimas noticias", "Actualidad reciente")}
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

        {categoryArticles.map((category) => (
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
        ))}
      </>
    );
  };

  const renderSections = () => (
    <>
      {renderNotice()}
      {renderSectionTitle("Secciones", "Explorar")}
      <View style={styles.directory}>
        {CATEGORIES.map((category) => {
          const count = getArticlesByCategory(category.id, articles).length;
          return (
            <Pressable
              key={category.id}
              accessibilityRole="button"
              onPress={() => navigate({ name: "category", category: category.id })}
              style={({ pressed }) => [styles.directoryItem, pressed ? styles.pressed : null]}
            >
              <View>
                <Text style={styles.directoryTitle}>{category.label}</Text>
                <Text style={styles.directoryMeta}>{count} noticias simuladas</Text>
              </View>
              <Text style={styles.directoryAction}>Abrir</Text>
            </Pressable>
          );
        })}
      </View>
    </>
  );

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

  const renderSearch = (query: string) => {
    const results = searchArticles(query, articles);
    const hasQuery = query.trim().length > 0;
    return (
      <>
        {renderNotice()}
        {renderSectionTitle("Buscar", "Archivo local")}
        <View style={styles.searchBox}>
          <Search size={20} color={colors.textSecondary} />
          <TextInput
            ref={searchInputRef}
            accessibilityLabel="Buscar noticias"
            placeholder="Buscar por tema, categoría o titular"
            placeholderTextColor={colors.textSecondary}
            value={query}
            onChangeText={(nextQuery) => navigate({ name: "search", query: nextQuery }, true)}
            style={styles.searchInput}
            returnKeyType="search"
          />
        </View>

        {!hasQuery ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>Escribe para buscar en la edición demo</Text>
            <Text style={styles.emptyText}>
              Puedes probar con tecnología, mercado, lectura, transporte o canchas.
            </Text>
          </View>
        ) : results.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No encontramos coincidencias</Text>
            <Text style={styles.emptyText}>
              Revisa la escritura o prueba con una categoría distinta.
            </Text>
            <AppButton
              label="Limpiar búsqueda"
              variant="secondary"
              onPress={() => navigate({ name: "search", query: "" }, true)}
            />
          </View>
        ) : (
          <>
            <Text style={styles.resultsCount}>
              {results.length} resultado{results.length === 1 ? "" : "s"}
            </Text>
            {renderArticleGrid(results)}
          </>
        )}
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
              Puede que el enlace esté incompleto o que la pieza ya no exista en el
              dataset demo.
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

        <View style={styles.articleView}>
          <Text style={styles.category}>{getCategoryLabel(currentArticle.category)}</Text>
          <Text style={styles.articleTitle}>{currentArticle.title}</Text>
          <Text style={styles.articleSummary}>{currentArticle.summary}</Text>
          <Text style={styles.articleMeta}>
            {currentArticle.author} · {formatLongDate(currentArticle.publishedAt)} ·{" "}
            {currentArticle.readingMinutes} min de lectura
          </Text>

          <ArticleImage image={currentArticle.image} size="lead" />
          <Text style={styles.credit}>
            Noticia simulada · {currentArticle.image.credit}
          </Text>

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

          <View style={styles.readerBody}>
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
    if (route.name === "sections") return renderSections();
    if (route.name === "search") return renderSearch(route.query);
    if (route.name === "saved") return renderSaved();
    if (route.name === "category") return renderCategory(route.category);
    if (route.name === "article") return renderArticle();
    return renderHome();
  };

  const activeBottom = route.name === "category" ? "sections" : route.name;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => navigate({ name: "home" })}
          style={({ pressed }) => [styles.brand, pressed ? styles.pressed : null]}
        >
          <Text style={styles.brandName}>AI News</Text>
          <View style={styles.brandUnderline} />
        </Pressable>

        {!isMobile ? (
          <View style={styles.headerNav}>
            <AppButton label="Inicio" variant="ghost" onPress={() => navigate({ name: "home" })} />
            <AppButton
              label="Secciones"
              variant="ghost"
              onPress={() => navigate({ name: "sections" })}
            />
            <AppButton
              label="Buscar"
              variant="ghost"
              onPress={() => navigate({ name: "search", query: "" })}
            />
            <AppButton
              label={`Guardados (${savedIds.length})`}
              variant="ghost"
              onPress={() => navigate({ name: "saved" })}
            />
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

      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={[
          styles.scrollContent,
          isMobile ? styles.scrollContentMobile : null,
        ]}
      >
        <View style={styles.container}>{renderContent()}</View>
      </ScrollView>

      {isMobile ? (
        <View style={styles.bottomNav}>
          <BottomNavItem
            label="Inicio"
            active={activeBottom === "home"}
            icon={<Home size={20} color={activeBottom === "home" ? colors.action : colors.textSecondary} />}
            onPress={() => navigate({ name: "home" })}
          />
          <BottomNavItem
            label="Secciones"
            active={activeBottom === "sections"}
            icon={
              <Grid3X3
                size={20}
                color={activeBottom === "sections" ? colors.action : colors.textSecondary}
              />
            }
            onPress={() => navigate({ name: "sections" })}
          />
          <BottomNavItem
            label="Buscar"
            active={activeBottom === "search"}
            icon={<Search size={20} color={activeBottom === "search" ? colors.action : colors.textSecondary} />}
            onPress={() => navigate({ name: "search", query: "" })}
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
        </View>
      ) : null}
    </SafeAreaView>
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
  scrollContent: {
    paddingVertical: spacing.lg,
  },
  scrollContentMobile: {
    paddingBottom: layout.mobileBottomNavHeight + spacing.xl,
  },
  container: {
    width: "100%",
    maxWidth: layout.maxContentWidth,
    alignSelf: "center",
    paddingHorizontal: spacing.md,
    gap: spacing.xl,
  },
  notice: {
    color: colors.textSecondary,
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
  resultsCount: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    marginVertical: spacing.md,
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
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
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
