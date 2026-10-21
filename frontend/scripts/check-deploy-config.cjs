const path = require("node:path");

/** Validate public build settings without printing any configuration values. */
function checkDeployConfig(environment, expectedProjectId) {
  const errors = [];
  const required = [
    "EXPO_PUBLIC_FIREBASE_API_KEY",
    "EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN",
    "EXPO_PUBLIC_FIREBASE_PROJECT_ID",
    "EXPO_PUBLIC_FIREBASE_APP_ID",
    "EXPO_PUBLIC_NEWS_API_BASE_URL",
    "EXPO_PUBLIC_ASSISTANT_API_BASE_URL",
  ];
  for (const name of required) {
    if (!environment[name]?.trim()) errors.push(`Falta ${name}.`);
  }
  if (environment.EXPO_PUBLIC_FIREBASE_PROJECT_ID?.trim() !== expectedProjectId) {
    errors.push("EXPO_PUBLIC_FIREBASE_PROJECT_ID debe coincidir con NEWS_FIREBASE_PROJECT_ID.");
  }
  const urls = ["EXPO_PUBLIC_NEWS_API_BASE_URL", "EXPO_PUBLIC_ASSISTANT_API_BASE_URL"];
  if (environment.EXPO_PUBLIC_ANDROID_DOWNLOAD_URL) urls.push("EXPO_PUBLIC_ANDROID_DOWNLOAD_URL");
  for (const name of urls) {
    try {
      const url = new URL(environment[name]);
      if (url.protocol !== "https:" || ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)
          || url.username || url.password || url.search || url.hash) {
        throw new Error("invalid deployment URL");
      }
    } catch {
      errors.push(`${name} debe ser una URL HTTPS pública sin credenciales, query ni fragmento.`);
    }
  }
  return errors;
}

if (require.main === module) {
  // Match the .env loading used by Expo, including .env.production and shell overrides.
  process.env.NODE_ENV = "production";
  require("@expo/env").load(path.resolve(__dirname, ".."));
  const errors = checkDeployConfig(process.env, process.argv[2]);
  if (errors.length) {
    for (const error of errors) console.error(error);
    process.exitCode = 1;
  } else {
    console.log("Configuración pública de Hosting, Firebase Auth y APIs: OK.");
  }
}

module.exports = { checkDeployConfig };
