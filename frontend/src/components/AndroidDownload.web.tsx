import * as React from "react";

import { colors, fonts, radii, spacing } from "../theme";

const fallbackAndroidBuildUrl =
  "https://expo.dev/accounts/donmathiuz/projects/ai-assisted-news-app/builds/33425211-31ac-4a45-bda4-e33dcbcbe6fc";

export function AndroidDownload() {
  const androidBuildUrl = process.env.EXPO_PUBLIC_ANDROID_DOWNLOAD_URL?.trim() || fallbackAndroidBuildUrl;
  const isDirectApk = new URL(androidBuildUrl).pathname.endsWith(".apk");
  return (
    <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: spacing.md }}>
      <a
        href={androidBuildUrl}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: 48,
          padding: `0 ${spacing.md}px`,
          border: `1px solid ${colors.controlBorder}`,
          borderRadius: radii.control,
          color: colors.action,
          fontFamily: fonts.bodyMedium,
          fontSize: 15,
          textAlign: "center",
          textDecoration: "underline",
          textUnderlineOffset: 3,
        }}
      >
        Descargar para Android
      </a>
      <p style={{ color: colors.textSecondary, fontFamily: fonts.body, fontSize: 13, lineHeight: "20px", margin: `${spacing.xs}px 0 0` }}>
        {isDirectApk
          ? "Descarga el APK para instalar AI News. Solo para Android."
          : "Abre la página de instalación del APK en Expo. Solo para Android."}
      </p>
    </div>
  );
}
