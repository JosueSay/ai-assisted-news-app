export type NewsArticle = {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
};

export type AppUser = {
  id: string;
  name: string;
  email: string;
  photoUrl?: string;
  isGuest: boolean;
};
