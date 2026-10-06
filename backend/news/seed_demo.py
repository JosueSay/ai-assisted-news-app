"""Seeder idempotente para noticias locales de demostración."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .models import ImageType, LocationLevel, NewsStatus, VerificationStatus
from .models.news import AiAssistance, GeographicScope, Image, News, Verification
from .models.reading_time import compute_reading_time
from .models.user import User
from .schema.initialize import initialize_schema
from .seed_catalog import CATALOG_LOCATION_IDS, seed_catalog_data

DEMO_LOCATION_ID = CATALOG_LOCATION_IDS["GT"]
DEMO_AUTHOR_ID = ObjectId("670000000000000000000002")

DEMO_NEWS = [
    {
        "_id": ObjectId("670000000000000000000101"),
        "slug": "paseo-peatonal-comercio-descanso",
        "title": "Un nuevo paseo peatonal reúne comercio y espacios de descanso",
        "summary": (
            "La iniciativa piloto combina bancas, sombra y horarios de carga para "
            "ordenar una zona con alta circulación vecinal."
        ),
        "topic": "actualidad",
        "publishedAt": "2026-10-04T08:30:00-06:00",
        "content": [
            "La municipalidad ficticia de San Jacinto abrió esta semana un tramo peatonal temporal en una avenida de comercio barrial. El proyecto busca medir cómo cambia la circulación cuando los autos comparten menos espacio con quienes caminan.",
            "Durante la primera etapa se instalaron bancas, maceteros y señalización removible. Los locales mantienen horarios de carga por la mañana y por la noche para evitar que la operación diaria quede interrumpida.",
            "Vecinos consultados por la redacción demo destacaron que el área se siente más tranquila, aunque pidieron mejorar la sombra en las horas de mayor sol. Los organizadores recopilarán observaciones durante seis semanas.",
            "El piloto no representa una decisión definitiva. Al cierre del periodo se publicará un informe con conteos de paso, tiempos de entrega y comentarios de comerciantes para decidir si el paseo continúa.",
        ],
    },
    {
        "_id": ObjectId("670000000000000000000102"),
        "slug": "sensores-huertos-urbanos",
        "title": "Jóvenes desarrollan sensores para cuidar los huertos urbanos",
        "summary": (
            "El prototipo mide humedad y temperatura con piezas de bajo costo para "
            "apoyar a grupos que cultivan en terrazas y patios."
        ),
        "topic": "tecnologia",
        "publishedAt": "2026-10-04T07:20:00-06:00",
        "content": [
            "Un grupo de estudiantes demo presentó sensores sencillos para monitorear huertos urbanos. La propuesta nació de visitas a terrazas comunitarias donde el riego depende de turnos y experiencia manual.",
            "El dispositivo mide humedad del suelo y temperatura ambiente. Cuando detecta sequedad persistente, muestra una alerta local para que el equipo revise la planta antes de regar por costumbre.",
            "El proyecto prioriza piezas fáciles de conseguir y reparación abierta. Sus creadores preparan una guía para que otros grupos puedan ensamblarlo sin depender de una tienda especializada.",
            "La siguiente fase será probarlo durante un mes en cuatro huertos con condiciones distintas. Los resultados definirán si conviene agregar energía solar o una carcasa resistente a lluvia.",
        ],
    },
    {
        "_id": ObjectId("670000000000000000000103"),
        "slug": "mercado-digital-comunitario",
        "title": "Pequeños comercios prueban un mercado digital comunitario",
        "summary": (
            "La plataforma piloto agrupa inventarios de tiendas cercanas para que "
            "compradores comparen disponibilidad antes de salir."
        ),
        "topic": "economia",
        "publishedAt": "2026-10-04T06:50:00-06:00",
        "content": [
            "Treinta comercios demo participan en un mercado digital comunitario que muestra productos disponibles por barrio. La plataforma no procesa pagos; su primera meta es reducir viajes innecesarios.",
            "Cada tienda actualiza una lista sencilla de inventario destacado. Los clientes pueden revisar horarios, medios de contacto y notas sobre productos agotados antes de llamar o visitar.",
            "La cámara de comercio local acompañará la prueba con capacitación en fotografía básica y atención por mensajes. El reto principal será mantener información actualizada sin cargar de trabajo a los vendedores.",
            "El piloto durará ocho semanas. Si se confirma uso constante, el equipo evaluará pedidos reservados y métricas anónimas para entender qué categorías generan más consultas.",
        ],
    },
    {
        "_id": ObjectId("670000000000000000000104"),
        "slug": "ruta-lectura-aire-libre",
        "title": "Bibliotecas de barrio abren una ruta de lectura al aire libre",
        "summary": (
            "La programación conecta plazas, parques y patios escolares con clubes "
            "de lectura breves para todas las edades."
        ),
        "topic": "cultura",
        "publishedAt": "2026-10-04T09:10:00-06:00",
        "content": [
            "Bibliotecas de barrio demo abrieron una ruta de lectura al aire libre para acercar libros a plazas, parques y patios escolares. La agenda combina sesiones breves con préstamo temporal de materiales.",
            "Cada punto tendrá una mesa de orientación y lecturas de veinte minutos. La programación evita amplificación sonora para mantener el ambiente de parque y favorecer conversaciones pequeñas.",
            "El circuito empieza con cuentos para niñas y niños, sigue con crónica local y termina con poesía breve. Las personas asistentes pueden proponer textos para próximas fechas.",
            "La red bibliotecaria medirá asistencia y devolución de libros durante un mes. Si la respuesta es positiva, la ruta se repetirá los primeros sábados de cada mes.",
        ],
    },
    {
        "_id": ObjectId("670000000000000000000105"),
        "slug": "liga-comunitaria-canchas-vecindario",
        "title": "Una liga comunitaria recupera las canchas del vecindario",
        "summary": (
            "Equipos juveniles y familias organizan jornadas de limpieza, horarios "
            "compartidos y torneos cortos de fin de semana."
        ),
        "topic": "deportes",
        "publishedAt": "2026-10-03T16:25:00-06:00",
        "content": [
            "Una liga comunitaria demo comenzó a recuperar canchas de barrio con jornadas de limpieza y pintura básica. La iniciativa reúne a equipos juveniles, familias y entrenadores voluntarios.",
            "El calendario reserva horarios para niñas, niños y personas adultas, con reglas claras para evitar que un solo grupo ocupe todo el espacio. Los torneos serán cortos y sin inscripción costosa.",
            "Vecinos cercanos pidieron cuidar el ruido nocturno y mantener botes de basura suficientes. La organización respondió con cierres tempranos y turnos de limpieza después de cada jornada.",
            "El proyecto busca convertir las canchas en un punto estable de convivencia. Al terminar el primer mes se revisará asistencia, mantenimiento y percepción de seguridad alrededor del espacio.",
        ],
    },
]


@dataclass
class DemoSeedResult:
    database: str
    locations_upserted: int = 0
    users_upserted: int = 0
    news_upserted: int = 0
    news_modified: int = 0

    def format(self) -> str:
        return "\n".join(
            [
                "=== AI Assisted News — Demo Seed ===",
                f"Database: {self.database}",
                "Operation:",
                "- upsert demo location",
                "- upsert demo author",
                "- upsert published demo news",
                "",
                "No collections or indexes will be dropped.",
                "",
                f"Locations upserted: {self.locations_upserted}",
                f"Users upserted: {self.users_upserted}",
                f"News upserted: {self.news_upserted}",
                f"News modified: {self.news_modified}",
            ]
        )


def _published_at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _demo_author() -> dict:
    return User(
        _id=DEMO_AUTHOR_ID,
        firebaseUid="demo-news-author",
        email="redaccion@demo.local",
        displayName="Redacción AI News",
        photoUrl="",
        simulatedLocationId=DEMO_LOCATION_ID,
    ).model_dump_mongo()


def _demo_news_document(item: dict) -> dict:
    content = "\n\n".join(item["content"])
    word_count, reading_minutes = compute_reading_time(content)
    published_at = _published_at(item["publishedAt"])
    news = News(
        _id=item["_id"],
        slug=item["slug"],
        title=item["title"],
        summary=item["summary"],
        content=content,
        authorId=DEMO_AUTHOR_ID,
        status=NewsStatus.published,
        topics=[item["topic"]],
        keywords=[item["topic"], "demo", "local"],
        geographicScope=GeographicScope(
            level=LocationLevel.city,
            locationIds=[DEMO_LOCATION_ID],
        ),
        verification=Verification(
            status=VerificationStatus.confirmed,
            reviewedBy=DEMO_AUTHOR_ID,
            reviewedAt=published_at,
            notes="Noticia ficticia para prueba local.",
        ),
        sources=[],
        image=Image(
            url=None,
            alt=None,
            type=ImageType.none,
            credit="Imagen ilustrativa pendiente",
            rights="Placeholder local; requiere reemplazo por foto con licencia verificada.",
            aiDisclosure=None,
        ),
        aiAssistance=AiAssistance(humanReviewed=True),
        wordCount=word_count,
        estimatedReadingMinutes=reading_minutes,
        publishedAt=published_at,
        createdAt=published_at,
        updatedAt=published_at,
    )
    return news.model_dump_mongo()


def seed_demo_data(database: Database) -> DemoSeedResult:
    initialize_schema(database)
    result = DemoSeedResult(database=database.name)

    catalog_result = seed_catalog_data(database)
    result.locations_upserted = catalog_result.locations_upserted

    user_result = database["users"].replace_one(
        {"_id": DEMO_AUTHOR_ID},
        _demo_author(),
        upsert=True,
    )
    result.users_upserted = 1 if user_result.upserted_id else 0

    for item in DEMO_NEWS:
        upsert_result = database["news"].replace_one(
            {"_id": item["_id"]},
            _demo_news_document(item),
            upsert=True,
        )
        if upsert_result.upserted_id:
            result.news_upserted += 1
        else:
            result.news_modified += upsert_result.modified_count

    return result


def run_seed_demo() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = seed_demo_data(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    print(run_seed_demo())


if __name__ == "__main__":
    main()
