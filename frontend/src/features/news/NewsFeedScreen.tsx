import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";

import { ArticleCard } from "../../components/ArticleCard";
import { fetchNewsFeed } from "../../services/newsService";
import { colors, spacing } from "../../theme";
import type { AppUser, NewsArticle } from "../../types";

type Props = {
  user: AppUser;
  onSignOut: () => void;
};

export function NewsFeedScreen({ user, onSignOut }: Props) {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const load = useCallback(async () => {
    setIsRefreshing(true);
    try {
      setArticles(await fetchNewsFeed());
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hola, {user.name}</Text>
          <Text style={styles.email}>{user.email}</Text>
        </View>
        <Text style={styles.signOut} onPress={onSignOut}>
          Salir
        </Text>
      </View>

      <FlatList
        data={articles}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <ArticleCard article={item} />}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={() => void load()} />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: spacing.md,
    paddingTop: spacing.xl,
  },
  greeting: { color: colors.text, fontSize: 18, fontWeight: "700" },
  email: { color: colors.textMuted, fontSize: 13 },
  signOut: { color: colors.primary, fontWeight: "600" },
  list: { padding: spacing.md },
});
