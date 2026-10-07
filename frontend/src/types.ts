export const CATEGORIES = [
  { id: "actualidad", label: "Actualidad" },
  { id: "tecnologia", label: "Tecnología" },
  { id: "economia", label: "Economía" },
  { id: "cultura", label: "Cultura" },
  { id: "deportes", label: "Deportes" },
] as const;

export type CategoryId = (typeof CATEGORIES)[number]["id"];

export function getCategoryLabel(categoryId: CategoryId) {
  return CATEGORIES.find((category) => category.id === categoryId)?.label ?? categoryId;
}

export type ArticleImage = {
  src: string | null;
  alt: string;
  width: number;
  height: number;
  credit: string;
  sourceUrl: string;
  license: string;
};

export type NewsArticle = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  category: CategoryId;
  author: string;
  publishedAt: string;
  body: string[];
  readingMinutes: number;
  source: string;
  image: ArticleImage;
};

export type AppUser = {
  id: string;
  name: string;
  email: string;
  photoUrl?: string;
  isGuest: boolean;
  role?: "user" | "admin";
  adminToken?: string;
};
