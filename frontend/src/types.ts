import {
  CATEGORIES,
  type CategoryId,
  type ImageType,
  type LocationLevel,
  type SourceType,
  type VerificationStatus,
  type UserRole,
} from "./generated/newsContract";
export { CATEGORIES, type CategoryId } from "./generated/newsContract";

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
  type: ImageType;
  aiDisclosure: string | null;
};

export type NewsArticle = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  category: CategoryId;
  topics: string[];
  geographicScope: { level: LocationLevel; locationIds: string[] } | null;
  verification: {
    status: VerificationStatus;
    reviewedBy: string | null;
    reviewedAt: string | null;
    notes: string | null;
  } | null;
  sources: {
    name: string;
    url: string;
    sourceType: SourceType;
    publishedAt: string | null;
    accessedAt: string;
    supports: string | null;
  }[];
  aiAssistance: {
    summaryGenerated: boolean;
    topicsGenerated: boolean;
    imageGenerated: boolean;
    humanReviewed: boolean;
  };
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
  role?: UserRole;
};
