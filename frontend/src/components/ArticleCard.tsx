import { Pressable, StyleSheet, Text, View } from "react-native";
import { Bookmark, BookmarkCheck } from "lucide-react-native";

import { ArticleImage } from "./ArticleImage";
import { colors, fonts, radii, spacing } from "../theme";
import { getCategoryLabel, type NewsArticle } from "../types";

type Variant = "lead" | "standard" | "secondary" | "compact";

type Props = {
  article: NewsArticle;
  isSaved: boolean;
  onOpen: (article: NewsArticle) => void;
  onToggleSave: (article: NewsArticle) => void;
  variant?: Variant;
};

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-GT", {
    day: "2-digit",
    month: "short",
  });
}

export function ArticleCard({
  article,
  isSaved,
  onOpen,
  onToggleSave,
  variant = "standard",
}: Props) {
  const isCompact = variant === "compact";
  const isLead = variant === "lead";
  const titleStyle = isLead
    ? styles.leadTitle
    : isCompact
      ? styles.compactTitle
      : styles.title;

  return (
    <View style={[styles.card, styles[variant]]}>
      <Pressable
        accessibilityRole="link"
        accessibilityLabel={`Abrir noticia: ${article.title}`}
        onPress={() => onOpen(article)}
        style={({ pressed }) => [styles.openArea, pressed ? styles.pressed : null]}
      >
        <View style={isCompact ? styles.compactLayout : styles.stack}>
          <ArticleImage
            image={article.image}
            size={isLead ? "lead" : isCompact ? "compact" : "standard"}
          />
          <View style={styles.content}>
            <Text style={styles.category}>{getCategoryLabel(article.category)}</Text>
            <Text style={titleStyle}>{article.title}</Text>
            {!isCompact ? <Text style={styles.summary}>{article.summary}</Text> : null}
            <Text style={styles.meta}>
              {article.author} · {formatDate(article.publishedAt)} · {article.readingMinutes} min
            </Text>
          </View>
        </View>
      </Pressable>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={isSaved ? "Quitar de guardados" : "Guardar noticia"}
        accessibilityState={{ selected: isSaved }}
        hitSlop={10}
        onPress={() => onToggleSave(article)}
        style={({ pressed }) => [styles.saveButton, pressed ? styles.pressed : null]}
      >
        {isSaved ? (
          <BookmarkCheck size={20} color={colors.action} />
        ) : (
          <Bookmark size={20} color={colors.textSecondary} />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    position: "relative",
    backgroundColor: "transparent",
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: spacing.md,
  },
  lead: {
    gap: spacing.md,
  },
  standard: {
    gap: spacing.sm,
  },
  secondary: {
    gap: spacing.sm,
  },
  compact: {
    paddingBottom: spacing.sm,
  },
  openArea: {
    borderRadius: radii.panel,
  },
  pressed: {
    opacity: 0.78,
  },
  stack: {
    gap: spacing.sm,
  },
  compactLayout: {
    flexDirection: "row",
    gap: spacing.sm,
    alignItems: "flex-start",
  },
  content: {
    flex: 1,
    gap: spacing.xs,
    paddingRight: spacing.xl,
  },
  category: {
    color: colors.brand,
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    letterSpacing: 0.72,
    lineHeight: 17,
    textTransform: "uppercase",
  },
  leadTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 36,
    lineHeight: 39,
  },
  title: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 24,
    lineHeight: 29,
  },
  compactTitle: {
    color: colors.ink,
    fontFamily: fonts.heading,
    fontSize: 20,
    lineHeight: 25,
  },
  summary: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 16,
    lineHeight: 25,
  },
  meta: {
    color: colors.textSecondary,
    fontFamily: fonts.body,
    fontSize: 13,
    lineHeight: 19,
  },
  saveButton: {
    position: "absolute",
    top: 0,
    right: 0,
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
});
