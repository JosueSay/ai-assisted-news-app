import { StyleSheet, Text, View } from "react-native";

import { colors, radii, spacing } from "../theme";
import type { NewsArticle } from "../types";

export function ArticleCard({ article }: { article: NewsArticle }) {
  const date = new Date(article.publishedAt).toLocaleDateString("es-GT", {
    day: "2-digit",
    month: "short",
  });

  return (
    <View style={styles.card}>
      <Text style={styles.source}>
        {article.source} · {date}
      </Text>
      <Text style={styles.title}>{article.title}</Text>
      <Text style={styles.summary}>{article.summary}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.sm,
    gap: spacing.xs,
  },
  source: {
    color: colors.textMuted,
    fontSize: 12,
    textTransform: "uppercase",
  },
  title: { color: colors.text, fontSize: 17, fontWeight: "700" },
  summary: { color: colors.textMuted, fontSize: 14, lineHeight: 20 },
});
