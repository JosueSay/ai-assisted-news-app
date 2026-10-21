export function activeReadingSeconds(
  accumulatedSeconds: number,
  activeSince: number | null,
  now: number,
): number {
  if (activeSince === null) return accumulatedSeconds;
  return accumulatedSeconds + Math.max(0, Math.floor((now - activeSince) / 1000));
}

export function articleVisibleFraction(
  scrollTop: number,
  viewportHeight: number,
  bodyTop: number,
  bodyHeight: number,
): number {
  if (bodyHeight <= 0 || viewportHeight <= 0) return 0;
  return Math.min(1, Math.max(0, (scrollTop + viewportHeight - bodyTop) / bodyHeight));
}

export function reachedReadThreshold(
  scrollTop: number,
  viewportHeight: number,
  bodyTop: number,
  bodyHeight: number,
): boolean {
  return articleVisibleFraction(scrollTop, viewportHeight, bodyTop, bodyHeight) >= 0.9;
}

export function shortArticleReadComplete(
  visibleFraction: number,
  activeVisibleSeconds: number,
): boolean {
  return visibleFraction >= 0.9 && activeVisibleSeconds >= 5;
}
