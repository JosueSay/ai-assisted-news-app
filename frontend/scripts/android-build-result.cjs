/** Select only a successful APK produced for this linked EAS project. */
function readApkBuildUrl(results, projectId) {
  const build = Array.isArray(results) && results.length === 1 ? results[0] : null;
  if (!projectId || !build || build.status !== "FINISHED" || build.platform !== "ANDROID"
      || build.buildProfile !== "apk" || build.distribution !== "INTERNAL" || build.app?.id !== projectId) {
    throw new Error("EAS no devolvió un APK terminado del proyecto y perfil esperados.");
  }
  const value = build.artifacts?.buildUrl;
  if (typeof value !== "string" || /\s/.test(value)) throw new Error("Falta una URL de APK válida.");
  const url = new URL(value);
  if (url.protocol !== "https:" || url.hostname !== "expo.dev" || url.port
      || url.username || url.password || url.search || url.hash
      || !/^\/artifacts\/eas\/[^/]+\.apk$/.test(url.pathname)) {
    throw new Error("El artefacto EAS debe ser una descarga APK HTTPS de Expo.");
  }
  return url.href;
}

if (require.main === module) {
  try {
    const fs = require("node:fs");
    const app = require("../app.json");
    const url = readApkBuildUrl(JSON.parse(fs.readFileSync(process.argv[2], "utf8")), app.expo.extra?.eas?.projectId);
    if (!process.env.GITHUB_ENV) throw new Error("Falta el archivo de entorno del runner GitHub.");
    fs.appendFileSync(process.env.GITHUB_ENV, `EXPO_PUBLIC_ANDROID_DOWNLOAD_URL=${url}\n`);
    console.log("APK completado: enlace preparado para el export web.");
  } catch {
    console.error("No se publicará la web: el resultado EAS no contiene un APK válido del proyecto.");
    process.exitCode = 1;
  }
}

module.exports = { readApkBuildUrl };
