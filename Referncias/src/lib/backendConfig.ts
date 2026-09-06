const placeholderPattern =
  /your-project|tu_project_ref|replace_me|pega_aqui|placeholder|\.\.\./i;

export function hasUsableSupabaseConfiguration(
  rawUrl: string | undefined,
  rawKey: string | undefined,
): boolean {
  const url = rawUrl?.trim();
  const key = rawKey?.trim();

  if (!url || !key || placeholderPattern.test(url) || placeholderPattern.test(key)) {
    return false;
  }

  try {
    const parsedUrl = new URL(url);
    return (
      (parsedUrl.protocol === 'https:' || parsedUrl.protocol === 'http:') &&
      key.length >= 20
    );
  } catch {
    return false;
  }
}

export function shouldConnectToSupabase(
  rawUrl: string | undefined,
  rawKey: string | undefined,
  demoMode: string | undefined,
): boolean {
  return demoMode === 'false' && hasUsableSupabaseConfiguration(rawUrl, rawKey);
}
