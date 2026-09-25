import type { NewsArticle } from "../types";

const DEMO_ARTICLES: NewsArticle[] = [
  {
    id: "1",
    title: "Guatemala impulsa programas de ahorro digital para jóvenes",
    summary:
      "Nuevas iniciativas buscan acercar la educación financiera a estudiantes universitarios mediante apps móviles.",
    source: "Prensa Libre",
    publishedAt: "2026-09-20T09:00:00-06:00",
  },
  {
    id: "2",
    title: "Bancos regionales adoptan asistentes conversacionales con IA",
    summary:
      "La banca centroamericana explora chatbots para resolver consultas frecuentes y mejorar la atención al cliente.",
    source: "El Economista",
    publishedAt: "2026-09-19T14:30:00-06:00",
  },
  {
    id: "3",
    title: "Crece la adopción de billeteras digitales en Centroamérica",
    summary:
      "Un reporte reciente muestra un aumento sostenido en el uso de pagos móviles entre pequeños comercios.",
    source: "Forbes Centroamérica",
    publishedAt: "2026-09-18T11:15:00-06:00",
  },
];

/**
 * Fuente de datos del feed. Hoy devuelve datos de demostración; el contrato
 * (async, mismo shape de NewsArticle) ya queda listo para apuntar a un
 * servicio real en backend/services cuando exista.
 */
export async function fetchNewsFeed(): Promise<NewsArticle[]> {
  return DEMO_ARTICLES;
}
