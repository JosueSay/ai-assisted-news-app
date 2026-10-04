import { Image, StyleSheet, Text, View } from "react-native";
import { ImageOff } from "lucide-react-native";

import { colors, fonts, radii, spacing } from "../theme";
import type { ArticleImage as ArticleImageType } from "../types";

type Props = {
  image: ArticleImageType;
  size?: "lead" | "standard" | "compact";
};

export function ArticleImage({ image, size = "standard" }: Props) {
  if (image.src) {
    return (
      <Image
        source={{ uri: image.src }}
        accessibilityLabel={image.alt}
        resizeMode="cover"
        style={[styles.image, styles[size]]}
      />
    );
  }

  return (
    <View
      accessible
      accessibilityLabel={`${image.alt}. Imagen no disponible.`}
      style={[styles.placeholder, styles[size]]}
    >
      <ImageOff size={size === "compact" ? 18 : 24} color={colors.textSecondary} />
      {size !== "compact" ? (
        <Text style={styles.placeholderText}>Imagen no disponible</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  image: {
    width: "100%",
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.image,
  },
  placeholder: {
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radii.image,
    borderWidth: 1,
    gap: spacing.xs,
  },
  lead: {
    aspectRatio: 16 / 9,
  },
  standard: {
    aspectRatio: 16 / 9,
  },
  compact: {
    width: 104,
    height: 80,
    aspectRatio: undefined,
  },
  placeholderText: {
    color: colors.textSecondary,
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
  },
});
