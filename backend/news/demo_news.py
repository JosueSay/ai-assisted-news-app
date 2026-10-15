"""Generador determinista de noticias demo (Loop 05).

DEMO / SYNTHETIC DATA: todo el contenido producido por este módulo es
sintético y ficticio. No representa acontecimientos reales y no atribuye
hechos a organizaciones, gobiernos, medios ni personas reales. Las fuentes
son ficticias con dominios reservados (``example.com``) y no se realiza
ninguna llamada de red, IA ni API externa.

El generador es una función pura: no se conecta a MongoDB. La misma
configuración produce siempre los mismos slugs, títulos, topics, locations,
estados, contenidos, timestamps de fixture e identificadores.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from .models import ImageType, LocationLevel, NewsStatus, VerificationStatus
from .models.news import AiAssistance, GeographicScope, Image, News, Verification
from .models.reading_time import compute_reading_time
from .seed_catalog import CATALOG_LOCATION_IDS

EXPECTED_NEWS_COUNT = 32

# Identificador sintético de autor para las fixtures. No se persiste ningún
# documento en `users` durante este loop: MongoDB no impone foreign keys y
# tanto el modelo como el validator solo exigen tipo ObjectId. La
# correspondencia con un usuario real queda pendiente de decisión humana.
DEMO_NEWS_AUTHOR_ID = ObjectId("672000000000000000000099")

DEMO_NEWS_BASE_PUBLISHED_AT = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
DEMO_NEWS_BASE_DRAFT_AT = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
DEMO_NEWS_SOURCE_ACCESSED_AT = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

_SYNTHETIC_NOTES = {
    "confirmed": (
        "DEMO / SYNTHETIC DATA: fixture ficticia confirmada dentro de la "
        "ficción demo; no describe hechos reales."
    ),
    "developing": (
        "DEMO / SYNTHETIC DATA: fixture ficticia en desarrollo dentro de la "
        "ficción demo; sujeta a cambios; no describe hechos reales."
    ),
    "insufficient_sources": (
        "DEMO / SYNTHETIC DATA: fixture ficticia con respaldo insuficiente "
        "deliberado para probar ese estado; no describe hechos reales."
    ),
    "conflicting_sources": (
        "DEMO / SYNTHETIC DATA: fixture ficticia con fuentes demo en "
        "contradicción deliberada para probar ese estado; no describe "
        "hechos reales."
    ),
}


def _news_id(index: int) -> ObjectId:
    return ObjectId(f"6720000000000000000000{index + 1:02x}")


def _published_at(index: int) -> datetime:
    return DEMO_NEWS_BASE_PUBLISHED_AT + timedelta(hours=index * 20)


def _draft_at(index: int) -> datetime:
    return DEMO_NEWS_BASE_DRAFT_AT + timedelta(hours=index * 11)


def _image(image_type: str, slug: str, alt: str) -> dict:
    if image_type == "none":
        return {
            "url": None,
            "alt": None,
            "type": "none",
            "credit": None,
            "rights": None,
            "aiDisclosure": None,
        }
    base = {
        "url": f"https://example.com/demo/img/{slug}.jpg",
        "alt": alt,
        "type": image_type,
        "credit": "Ilustración demo ficticia",
        "rights": "Fixture sintética; sin derechos de terceros.",
        "aiDisclosure": None,
    }
    if image_type == "ai_generated":
        base["aiDisclosure"] = (
            "Imagen demo generada con IA (fixture sintética, sin hechos reales)."
        )
    elif image_type == "ai_modified":
        base["aiDisclosure"] = (
            "Imagen demo real alterada con IA (fixture sintética, sin hechos reales)."
        )
    return base


# Cada especificación define una noticia demo. `paragraphs` es el contenido
# ficticio; `sources` se describe con (sourceType, supports).
_SPECS: tuple[dict, ...] = (
    {
        "country": "CA",
        "slug": "demo-ca-01-sensores-jardin",
        "title": "Vecinos demo prueban sensores de humedad en jardines comunitarios",
        "summary": (
            "Un colectivo ficticio instala sensores de bajo costo en parcelas "
            "demo para decidir el riego sin desperdiciar agua."
        ),
        "topics": ["tecnologia", "ciencia"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una parcela ficticia con sensores",
        "sources": [("media", None), ("primary_source", None)],
        "paragraphs": [
            "En una localidad demo de Canadá, un colectivo vecinal ficticio instaló sensores sencillos de humedad en doce parcelas comunitarias. La prueba busca responder una pregunta práctica: cuánta agua necesita cada parcela sin regar por costumbre ni desperdiciar recursos.",
            "Los dispositivos son piezas de bajo costo armadas en un taller demo. Cada sensor muestra una luz local cuando la tierra permanece seca durante varias horas. Nadie recibe notificaciones en el teléfono: la lectura se hace pasando frente a la parcela.",
            "Durante la primera quincena, el grupo ficticio anotó lecturas en una libreta compartida. Descubrieron que dos parcelas a la sombra retenían humedad el doble de tiempo que las expuestas al sol directo del mediodía.",
            "La siguiente fase comparará el consumo de agua con el de la temporada anterior en la misma ficción. Si el ahorro se confirma dentro del escenario demo, el colectivo publicará una guía abierta para que otros grupos repliquen la prueba.",
            "Nada de lo descrito ocurrió en la realidad: es una fixture sintética para probar el feed por ubicación y por topics de tecnología y ciencia.",
            "Los turnos de lectura se reparten entre seis voluntarios ficticios del colectivo. Cada uno visita las parcelas dos mañanas por semana y deja su marca en la libreta compartida de la prueba.",
            "El cuaderno demo ya muestra un patrón inventado: las parcelas con mantillo retienen humedad más días que las de tierra desnuda. Ese hallazgo de la ficción orientará la guía abierta prometida.",
            "Quienes quieran replicar la prueba ficticia recibirán la lista de piezas y el plano del sensor. Nada requiere soldadura avanzada dentro del escenario demo.",
        ],
    },
    {
        "country": "CA",
        "slug": "demo-ca-02-club-lectura",
        "title": "Biblioteca demo abre un club de lectura infantil al aire libre",
        "summary": (
            "Sesiones breves de cuentos en un parque ficticio para acercar "
            "libros a niñas y niños del vecindario demo."
        ),
        "topics": ["educacion"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de una lectura en un parque ficticio",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "Una biblioteca ficticia en una localidad demo de Canadá abrió un club de lectura infantil al aire libre. Las sesiones duran veinte minutos y se celebran en un parque imaginario con mantas y cajas de libros prestados.",
            "Cada encuentro combina un cuento leído en voz alta con un juego de palabras. Las personas voluntarias del escenario demo rotan la lectura para que niñas y niños escuchen distintas voces.",
            "La red bibliotecaria ficticia medirá asistencia y devolución de libros durante un mes dentro de la prueba. Si la respuesta es positiva en la ficción, el club se repetirá los primeros sábados de cada mes.",
        ],
    },
    {
        "country": "MX",
        "slug": "demo-mx-01-teatro-barrial",
        "title": "Festival demo de teatro barrial con marionetas en patio vecinal",
        "summary": (
            "Tres compañías ficticias presentan obras breves con marionetas "
            "hechas de material reciclado en un patio demo."
        ),
        "topics": ["cultura", "entretenimiento"],
        "status": "published",
        "verification": "confirmed",
        "image": "ai_generated",
        "image_alt": "Imagen demo generada con IA de un teatrino ficticio",
        "sources": [("media", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de México, tres compañías ficticias organizaron un festival breve de teatro barrial con marionetas. El escenario es un patio imaginario con un teatrino armado con cajas y telas reutilizadas.",
            "Cada obra dura quince minutos y cuenta historias inventadas sobre oficios del barrio ficticio: la panadera que amasa de madrugada, el jardinero que conversa con las macetas y la bibliotecaria que ordena libros soñados.",
            "Las marionetas están hechas de material reciclado en un taller demo previo. Niñas y niños del vecindario ficticio ayudaron a pintar fondos y a ensayar los saludos de apertura.",
            "La entrada es libre dentro de la ficción y el orden de las funciones se sortea cada tarde. Al cierre, el público demo vota con semillas de frijol cuál historia regresa el fin de semana siguiente.",
            "Todo el festival es una invención para fixtures: permite probar topics de cultura y entretenimiento y el tratamiento de imágenes generadas con IA con su disclosure correspondiente.",
            "Los ensayos ocurren tres tardes por semana en el mismo patio ficticio. Cada compañía practica por turnos de una hora mientras las otras pintan fondos o remiendan marionetas.",
            "La entrada libre se organiza con boletos de papel reciclado repartidos en tiendas demo. Cada boleto inventado indica día y orden de funciones para evitar aglomeraciones en la ficción.",
            "El voto con semillas de frijol definirá la obra que regresa el fin de semana siguiente. El conteo se hace en público dentro del escenario para que niñas y niños verifiquen el resultado demo.",
        ],
    },
    {
        "country": "MX",
        "slug": "demo-mx-02-pausas-activas",
        "title": "Borrador demo: guía de pausas activas para teletrabajo vecinal",
        "summary": (
            "Borrador ficticio con rutinas breves de estiramiento para quienes "
            "trabajan desde casa en el vecindario demo."
        ),
        "topics": ["salud"],
        "status": "draft",
        "verification": "insufficient_sources",
        "image": "none",
        "image_alt": "",
        "sources": [("other", None)],
        "paragraphs": [
            "Este borrador ficticio reúne rutinas breves de pausas activas para personas que teletrabajan en un vecindario demo. Cada rutina dura cinco minutos y combina estiramientos de cuello, hombros y muñecas.",
            "La guía demo propone tres pausas al día dentro de la ficción: a media mañana, después de comer y antes de cerrar la jornada. Ninguna rutina requiere equipo especial, solo una silla estable y espacio para estirar los brazos.",
            "El documento sigue incompleto a propósito: le falta respaldo suficiente y por eso permanece en borrador. Servirá para probar que los borradores no aparecen en el feed ni pueden citarse en el chat.",
        ],
    },
    {
        "country": "GT",
        "slug": "demo-gt-01-mercado-comunitario",
        "title": "Mercado demo agrupa tiendas de barrio en un catálogo común",
        "summary": (
            "Treinta comercios ficticios comparten un catálogo sencillo para "
            "que compradores comparen disponibilidad antes de salir."
        ),
        "topics": ["economia", "negocios"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de puestos de un mercado ficticio",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de Guatemala, treinta comercios ficticios participan en un mercado comunitario que muestra productos disponibles por barrio. La plataforma imaginaria no procesa pagos: su primera meta dentro de la ficción es reducir viajes innecesarios.",
            "Cada tienda actualiza una lista sencilla de inventario destacado. Los compradores demo revisan horarios, medios de contacto y notas sobre productos agotados antes de llamar o visitar el puesto.",
            "Una asociación ficticia acompaña la prueba con capacitación en fotografía básica y atención por mensajes. El reto principal dentro del escenario es mantener la información actualizada sin cargar de trabajo a los vendedores.",
            "El piloto durará ocho semanas en la ficción. Si se confirma uso constante dentro de la prueba, el equipo evaluará reservas de pedidos y métricas anónimas para entender qué categorías generan más consultas.",
            "La historia es sintética y sirve para cubrir los topics de economía y negocios con dos noticias por país y tiempos de lectura medios.",
            "La capacitación ficticia enseña a fotografiar productos con luz natural y fondos claros. Cada tienda demo practica con cinco artículos antes de publicar su lista en la prueba.",
            "Un piloto de encargos reservados empezará en la quinta semana de la ficción. Los compradores apartan por mensaje y recogen en tienda sin pagos anticipados dentro del escenario.",
            "Las métricas anónimas de la prueba mostrarán qué categorías generan más consultas. Ese dato inventado decidirá si el mercado demo agrega repartos conjuntos entre tiendas cercanas.",
        ],
    },
    {
        "country": "GT",
        "slug": "demo-gt-02-liga-fin-semana",
        "title": "Liga demo organiza un torneo corto de fin de semana",
        "summary": (
            "Equipos juveniles ficticios disputan partidos breves con horarios "
            "compartidos y reglas de convivencia."
        ),
        "topics": ["deportes"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una cancha vecinal ficticia",
        "sources": [("witness", None), ("media", None)],
        "paragraphs": [
            "Una liga comunitaria ficticia en una localidad demo de Guatemala organizó un torneo corto de fin de semana. Participan equipos juveniles del vecindario imaginario con partidos de treinta minutos.",
            "El calendario reserva horarios equitativos para que ningún grupo ocupe toda la cancha. Las reglas demo premian la puntualidad y la limpieza del espacio después de cada jornada.",
            "Al cierre de la ficción se revisarán asistencia y percepción de convivencia. El torneo es una fixture sintética para el topic de deportes con tiempo de lectura corto.",
        ],
    },
    {
        "country": "CR",
        "slug": "demo-cr-01-monitoreo-quebradas",
        "title": "Monitoreo demo de quebradas urbanas con registros vecinales",
        "summary": (
            "Brigadas ficticias registran nivel y residuos en quebradas demo "
            "para planificar jornadas de limpieza."
        ),
        "topics": ["medio_ambiente", "ciencia"],
        "status": "published",
        "verification": "developing",
        "image": "ai_modified",
        "image_alt": "Imagen demo alterada con IA de una quebrada ficticia",
        "sources": [("primary_source", None), ("official", None)],
        "paragraphs": [
            "En una localidad demo de Costa Rica, brigadas vecinales ficticias monitorean tres quebradas urbanas con reglas y fichas de papel. Cada brigada registra el nivel del agua y los residuos visibles dos veces por semana dentro de la ficción.",
            "Las fichas usan dibujos simples para que cualquier persona pueda participar sin entrenamiento previo. Un círculo indica agua clara, un triángulo agua turbia y una equis presencia de residuos grandes en el tramo demo.",
            "Los datos se pegan en un mapa mural del salón comunal ficticio. Con el mapa a la vista, la asamblea demo prioriza qué tramos limpiar primero y cuántas bolsas y guantes necesita cada jornada.",
            "La noticia sigue en desarrollo dentro de la ficción: faltan cuatro semanas de registros para distinguir variaciones normales de episodios de vertido. Por eso su verificación demo es developing y sus notas lo explican.",
            "El equipo ficticio también anota la fauna observada en cada visita: libélulas, ranas pequeñas y aves que beben en las orillas imaginarias. Esos avistamientos no sustituyen un estudio real, solo enriquecen la actividad vecinal demo.",
            "Cuando el registro esté completo en la ficción, el colectivo publicará un resumen mural con los tramos más afectados. La historia completa es sintética y prueba contenidos largos, verificación developing e imágenes ai_modified con disclosure.",
            "Ninguna quebrada real fue medida: todo el monitoreo pertenece al dataset demo para ejercitar feed por ubicación, topics de medio ambiente y ciencia, y tiempos de lectura de tres minutos o más.",
            "Los turnos de monitoreo rotan entre doce voluntarios ficticios para cubrir los tres tramos demo. Cada pareja recorre su tramo asignado con regla, fichas y bolsas de la prueba.",
            "Una escuela ficticia adoptó el tramo medio como aula abierta dentro de la ficción. Sus estudiantes dibujan el mapa mural y aprenden a distinguir agua clara de agua turbia.",
            "Los puntos de acumulación recurrente reciben visitas de seguimiento cada semana demo. Si un punto se limpia tres veces seguidas en la ficción, la brigada investiga su origen.",
            "La asamblea demo cerrará el ciclo con una jornada grande de limpieza en el tramo más afectado. La convocatoria ficticia pedirá guantes, gorras y agua para todos.",
            "El archivo de fichas quedará en el salón comunal para consultas futuras de la prueba. Ese archivo inventado es la memoria del monitoreo demo.",
            "Las escuelas vecinas reciben copias de las fichas para sus clases ficticias de ciencias. Cada copia demo incluye instrucciones dibujadas para registrar sin mojarse.",
            "El cierre anual premiará con diplomas simbólicos a las brigadas constantes de la prueba. Esos diplomas inventados reconocen asistencia, no resultados reales.",
        ],
    },
    {
        "country": "CR",
        "slug": "demo-cr-02-paseo-peatonal",
        "title": "Paseo peatonal demo ordena comercio y espacios de descanso",
        "summary": (
            "Un tramo peatonal ficticio combina bancas, sombra y horarios de "
            "carga para ordenar una zona de alta circulación."
        ),
        "topics": ["actualidad"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de un paseo peatonal ficticio",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "Una municipalidad ficticia abrió un tramo peatonal temporal en una avenida de comercio barrial dentro del escenario demo. El proyecto mide cómo cambia la circulación cuando hay menos autos y más espacio para caminar.",
            "Se instalaron bancas, maceteros y señalización removible. Los locales ficticios mantienen horarios de carga por la mañana y por la noche para no interrumpir la operación diaria.",
            "Al cierre del periodo demo se publicará un informe con conteos de paso y comentarios de comerciantes ficticios. La nota es sintética y cubre el topic de actualidad con lectura corta.",
        ],
    },
    {
        "country": "AR",
        "slug": "demo-ar-01-asamblea-salon",
        "title": "Asamblea vecinal demo define reglas de uso del salón comunal",
        "summary": (
            "Vecinos ficticios acuerdan horarios, limpieza y prioridades para "
            "el salón comunal del barrio demo."
        ),
        "topics": ["politica", "actualidad"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de un salón comunal ficticio",
        "sources": [("official", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Argentina, una asamblea vecinal ficticia definió las reglas de uso del salón comunal. Asistieron delegados imaginarios de cada cuadra con propuestas escritas en fichas de colores.",
            "Los acuerdos demo fijan horarios por bloques: mañanas para talleres, tardes para juegos de mesa y noches para reuniones. Cada grupo deja limpio el espacio y anota desperfectos en un cuaderno visible.",
            "La asamblea ficticia también definió prioridades de reserva: primero actividades abiertas al barrio, luego celebraciones familiares y al final ensayos cerrados. Ninguna decisión de la ficción afecta a instituciones reales.",
            "Un comité rotativo revisará los acuerdos dentro de tres meses en la ficción. La nota sintética cubre política vecinal ficticia y actualidad sin atribuir nada a gobiernos reales.",
            "Con esta fixture se prueban dos topics a la vez y un tiempo de lectura medio con fuentes demo claramente identificadas.",
            "Un comité rotativo de tres vecinos ficticios vigila el cumplimiento de los acuerdos. Cada mes cambian los integrantes para que nadie concentre decisiones en la ficción.",
            "Los desacuerdos se resuelven con una ronda de propuestas escritas antes de votar. La regla demo prohíbe interrumpir y obliga a resumir la postura contraria primero.",
            "La próxima asamblea revisará el cuaderno de desperfectos del salón ficticio. Con ese registro inventado se priorizarán reparaciones menores antes del invierno imaginario.",
        ],
    },
    {
        "country": "AR",
        "slug": "demo-ar-02-precios-feria",
        "title": "Dos registros demo difieren sobre precios de la feria barrial",
        "summary": (
            "Fichas ficticias de precios se contradicen y la feria demo queda "
            "marcada como información en disputa."
        ),
        "topics": ["economia"],
        "status": "published",
        "verification": "conflicting_sources",
        "image": "none",
        "image_alt": "",
        "sources": [
            ("witness", "La ficha demo A afirma precios bajos estables."),
            ("witness", "La ficha demo B afirma subidas recientes en la ficción."),
        ],
        "paragraphs": [
            "En una feria barrial ficticia de una localidad demo de Argentina, dos registros de precios se contradicen. La ficha demo A anota precios bajos y estables durante cuatro semanas imaginarias seguidas.",
            "La ficha demo B, levantada por otro grupo ficticio en los mismos puestos y las mismas fechas de la ficción, anota subidas recientes en frutas y verduras de la prueba.",
            "Ante la contradicción deliberada, la noticia demo queda marcada como conflicting_sources. Ningún puesto real fue medido: la disputa existe solo para probar cómo se muestra la incertidumbre en el feed y el chat.",
            "La asamblea ficticia propone una tercera medición conjunta dentro del escenario. Hasta entonces, la recomendación demo es comparar ambas fichas antes de planificar compras imaginarias.",
            "Esta fixture sintética ejercita el estado de verificación más delicado con tiempo de lectura medio y sin imagen.",
            "La asamblea ficticia propuso una tercera medición conjunta para resolver la disputa. Ambos grupos pesarán y anotarán juntos durante dos semanas de la prueba.",
            "Mientras tanto, la recomendación demo es comparar ambas fichas antes de planificar compras imaginarias. Ninguna de las dos describe puestos reales ni precios verdaderos.",
            "El caso sirve al dataset como ejemplo de incertidumbre visible: el feed y el chat deberán mostrar el estado en disputa sin ocultar ninguna fuente ficticia.",
        ],
    },
    {
        "country": "BR",
        "slug": "demo-br-01-caminatas-matutinas",
        "title": "Caminatas demo matutinas con control básico de esfuerzo",
        "summary": (
            "Grupos ficticios caminan tres mañanas por semana con registro "
            "simple de pulso y distancia en un parque demo."
        ),
        "topics": ["deportes", "salud"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una caminata ficticia al amanecer",
        "sources": [("official", None), ("primary_source", None)],
        "paragraphs": [
            "En una localidad demo de Brasil, grupos vecinales ficticios organizan caminatas matutinas tres veces por semana. El recorrido imaginario bordea un parque demo con estaciones marcadas cada doscientos metros.",
            "Cada participante anota en una tarjeta ficticia su distancia y una estimación simple de esfuerzo. Nadie compite: las tarjetas sirven para que cada persona compare su propio progreso dentro de la ficción.",
            "Un voluntario ficticio con formación básica enseña a tomar el pulso en la muñeca antes y después de caminar. La indicación demo es detenerse y descansar si aparece mareo o dolor, sin excepciones.",
            "Las rutas tienen tres niveles inventados: paseo corto, vuelta media y circuito largo. Cada nivel está señalizado con cintas de colores en el escenario imaginario para no perderse.",
            "La hidratación corre por cuenta de puntos de agua ficticios al inicio y al final del recorrido. El grupo demo recuerda llevar gorra y protector en las mañanas soleadas de la prueba.",
            "Al cierre de cada mes ficticio, el colectivo revisa asistencia y ajusta horarios según el calor de la temporada imaginaria. Todo es sintético y prueba topics de deportes y salud con lectura larga.",
            "Ninguna recomendación sustituye consejo médico real: la fixture solo ejercita el modelo de noticias, el feed por ubicación y los tiempos de lectura de tres minutos o más.",
            "Las tarjetas ficticias usan tres colores según el esfuerzo percibido en la prueba. El verde indica paseo cómodo, el amarillo esfuerzo moderado y el rojo necesidad de pausa.",
            "En días de lluvia ficticia, la caminata se traslada bajo el techo del mercado demo. El recorrido alternativo mide cuatrocientos metros por vuelta dentro del escenario.",
            "Una caminata aniversario reunirá a todos los grupos del barrio imaginario. Cada grupo llevará una pancarta inventada con el nombre de su cuadra demo.",
            "Vecinos de otros barrios ficticios pidieron replicar el formato en sus parques. El colectivo compartirá tarjetas, rutas y reglas en una jornada abierta de la prueba.",
            "El registro anual cerrará con una gráfica mural de asistencia por mes ficticio. Esa gráfica sintética mostrará la constancia del grupo sin medir a personas reales.",
            "El botiquín demo acompaña cada caminata con vendas y sales de rehidratación ficticias. Su responsable imaginario revisa existencias antes de cada salida.",
            "Los recién llegados reciben una charla breve sobre ritmo y respiración en la ficción. La consigna demo es empezar por el paseo corto durante dos semanas.",
            "La cartelera del parque muestra la foto grupal mensual de la prueba. Esas fotos pertenecen al escenario demo y no identifican personas reales.",
        ],
    },
    {
        "country": "BR",
        "slug": "demo-br-02-taller-reparacion",
        "title": "Taller demo repara lámparas y pequeños aparatos del barrio",
        "summary": (
            "Voluntarios ficticios enseñan reparaciones básicas para alargar "
            "la vida útil de objetos cotidianos demo."
        ),
        "topics": ["tecnologia"],
        "status": "published",
        "verification": "developing",
        "image": "ai_generated",
        "image_alt": "Imagen demo generada con IA de un taller ficticio",
        "sources": [("media", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Brasil, un taller vecinal ficticio repara lámparas y pequeños aparatos del barrio imaginario. Cada sesión atiende diez objetos con turno previo anotado en una pizarra demo.",
            "Los voluntarios ficticios enseñan diagnósticos básicos: revisar el cable, probar el interruptor y limpiar contactos antes de declarar un aparato como inservible dentro de la ficción.",
            "El taller demo presta herramientas comunes y vende a precio de costo los repuestos más usados en la prueba. Todo lo recaudado en la ficción compra más soldadura y cinta aislante.",
            "La noticia sigue en desarrollo porque el colectivo aún mide cuántos objetos vuelven a fallar tras la reparación ficticia. Esa tasa definirá si el taller agrega una sesión mensual de seguimiento.",
            "Mientras tanto, el grupo publica fichas ilustradas con los cinco fallos más comunes encontrados en el escenario demo. Las fichas son inventadas y sirven para probar verificación developing con imagen generada.",
            "El taller es una fixture sintética: ningún aparato real fue reparado y la imagen generada con IA lleva su disclosure correspondiente sin presentar nada como fotografía real.",
            "La recepción ficticia admite diez objetos por sesión con turno anotado en pizarra. Cada turno demo indica el tipo de aparato y el fallo descrito por su dueño imaginario.",
            "Un banco de pruebas verifica cada reparación antes de devolver el objeto en la ficción. Si el fallo persiste, el caso pasa a la lista de segundas oportunidades demo.",
            "Las fichas ilustradas describen los cinco fallos más comunes del escenario. Cada ficha inventada muestra el síntoma, la causa probable y la herramienta necesaria.",
            "Los repuestos se venden a precio de costo dentro de la prueba. Lo recaudado compra soldadura, cinta aislante y fusibles para las sesiones siguientes.",
            "Una escuela ficticia visita el taller cada mes para una clase práctica demo. Sus estudiantes desarman aparatos donados y aprenden a clasificar piezas en la ficción.",
            "Donantes de la prueba aportan herramientas en desuso al taller demo. Cada donación ficticia se anota en un mural de agradecimientos del local.",
            "El registro de reparaciones anota objeto, fallo y solución de cada caso ficticio. Ese cuaderno demo orienta las compras de repuestos de la prueba.",
            "Los casos difíciles se discuten en una mesa redonda quincenal de la ficción. Cada voluntario demo aporta su diagnóstico antes de votar la solución.",
            "La jornada de puertas abiertas muestra el taller a vecinos curiosos de la prueba. Las visitas guiadas ficticias duran veinte minutos por grupo.",
        ],
    },
    {
        "country": "CU",
        "slug": "demo-cu-01-talleres-escritura",
        "title": "Talleres demo de escritura breve para jóvenes del barrio",
        "summary": (
            "Sesiones ficticias de microrrelatos con lectura colectiva en la "
            "biblioteca demo del vecindario."
        ),
        "topics": ["educacion", "cultura"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de un taller de escritura ficticio",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de Cuba, la biblioteca ficticia abrió talleres de escritura breve para jóvenes. Cada sesión propone un tema inventado y cien palabras como límite dentro de la prueba.",
            "Los textos se leen en voz alta al cierre de la jornada demo. El grupo comenta con reglas amables: primero lo que gustó, después una pregunta y al final una sugerencia.",
            "Una selección ficticia se pegará en el mural del pasillo durante un mes. El taller es sintético y cubre educación y cultura con lectura corta.",
        ],
    },
    {
        "country": "CU",
        "slug": "demo-cu-02-nota-hidratacion",
        "title": "Nota demo incompleta sobre hidratación en caminatas vecinales",
        "summary": (
            "Apunte ficticio pendiente de respaldo sobre consumo de agua en "
            "recorridos cortos del barrio demo."
        ),
        "topics": ["salud"],
        "status": "published",
        "verification": "insufficient_sources",
        "image": "none",
        "image_alt": "",
        "sources": [("other", None)],
        "paragraphs": [
            "Este apunte ficticio reúne consejos provisorios sobre hidratación para caminatas cortas en un barrio demo. Sugiere llevar agua, caminar a la sombra y descansar cada veinte minutos dentro de la ficción.",
            "La nota demo tiene una sola fuente y mediciones incompletas a propósito. Por eso su verificación es insufficient_sources y no debe tomarse como recomendación real.",
            "Cuando el grupo ficticio complete sus registros, la nota se actualizará en la ficción. Mientras tanto sirve para probar el estado de respaldo insuficiente con lectura corta.",
        ],
    },
    {
        "country": "JM",
        "slug": "demo-jm-01-noche-acustica",
        "title": "Noche demo de música acústica en patio vecinal",
        "summary": (
            "Dúos ficticios tocan piezas breves sin amplificación en un patio "
            "demo con sillas prestadas."
        ),
        "topics": ["entretenimiento", "cultura"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de un patio ficticio con instrumentos",
        "sources": [("witness", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de Jamaica, vecinos ficticios organizaron una noche de música acústica en un patio prestado. Tocan dúos rotativos con guitarra, maracas y cajón dentro del escenario imaginario.",
            "No hay amplificación en la ficción: los músicos demo se ubican en círculo para que el sonido llegue parejo. El repertorio inventado mezcla piezas tradicionales imaginarias con composiciones del grupo.",
            "La entrada se paga con un plato para compartir en la ficción. Al cierre, el patio queda limpio por turnos y los instrumentos se guardan en el salón comunal demo.",
            "La velada es sintética y prueba entretenimiento y cultura con fuentes demo y lectura media sin atribuir nada a artistas reales.",
            "Con su ambiente pequeño, la noche demo muestra cómo el feed puede destacar planes barriales ficticios junto a noticias de otros países del dataset.",
            "El repertorio inventado incluye piezas lentas para abrir y ritmos alegres para cerrar. Cada dúo demo propone una pieza nueva por mes dentro de la ficción.",
            "Los turnos de limpieza se sortean al inicio de la velada ficticia. Un equipo recoge sillas y otro barre el patio antes de guardar los instrumentos demo.",
            "La próxima fecha ya quedó anotada en el calendario mural del salón. Si llueve en la ficción, la noche se mueve bajo el techo del mismo patio imaginario.",
        ],
    },
    {
        "country": "JM",
        "slug": "demo-jm-02-trueque-libros",
        "title": "Trueque demo de libros y plantas entre vecinos",
        "summary": (
            "Mesa ficticia de intercambio donde libros y esquejes cambian de "
            "manos sin dinero en el barrio demo."
        ),
        "topics": ["economia"],
        "status": "published",
        "verification": "confirmed",
        "image": "none",
        "image_alt": "",
        "sources": [("witness", None), ("official", None)],
        "paragraphs": [
            "En un barrio demo, una mesa de trueque ficticia intercambia libros y esquejes de plantas sin dinero. Cada objeto lleva una tarjeta inventada con su historia dentro de la prueba.",
            "Las reglas demo son simples: un objeto por turno y prioridad para quienes traen algo para compartir. Un cuaderno ficticio registra los intercambios de la jornada.",
            "La mesa es sintética y cubre economía cotidiana ficticia con lectura corta y sin imagen.",
        ],
    },
    {
        "country": "ES",
        "slug": "demo-es-01-conteo-aves",
        "title": "Conteo demo de aves urbanas con fichas vecinales",
        "summary": (
            "Voluntarios ficticios registran aves en plazas demo para armar "
            "un atlas ilustrado del barrio."
        ),
        "topics": ["ciencia", "medio_ambiente"],
        "status": "published",
        "verification": "developing",
        "image": "illustration",
        "image_alt": "Ilustración demo de aves ficticias en una plaza",
        "sources": [("primary_source", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de España, voluntarios ficticios cuentan aves urbanas en seis plazas imaginarias. Cada observador lleva fichas con siluetas inventadas y anota hora, plaza y comportamiento dentro de la prueba.",
            "Los conteos se hacen al amanecer y al atardecer durante diez minutos por punto. La regla demo prohíbe alimentar a las aves para no alterar su conducta en la ficción.",
            "Un tablero mural reúne los registros semanales del escenario. Con esos datos ficticios, el grupo dibuja un atlas ilustrado con las especies imaginarias más vistas por plaza.",
            "La noticia sigue en desarrollo porque faltan conteos de la temporada de lluvias inventada. Esa segunda ronda definirá si algunas aves de la ficción solo visitan en ciertas semanas.",
            "Mientras tanto, el colectivo publica guías de observación con consejos simples: mirar en silencio, anotar primero y consultar la guía después. Todo el material pertenece a la prueba demo.",
            "El atlas es sintético y ningún ave real fue censada. La fixture ejercita ciencia y medio ambiente con lectura larga y verificación developing.",
            "Con plazas de varios barrios ficticios, el conteo demo también prueba la distribución geográfica del dataset sin salir del nivel país.",
            "La formación de voluntarios dura una mañana en el centro cívico ficticio. Cada participante practica con fichas de prueba antes de salir a su plaza demo.",
            "Un grupo escolar adoptó la plaza central como observatorio fijo de la ficción. Sus registros quincenales alimentan el tablero mural de la prueba.",
            "Los avistamientos raros se confirman con una segunda visita al día siguiente demo. Solo entonces entran al atlas ilustrado del barrio imaginario.",
            "El atlas se imprimirá en cartel para las seis plazas de la prueba. Cada cartel inventado mostrará las especies ficticias más vistas por estación.",
            "El archivo de conteos quedará en la biblioteca demo para consultas futuras. Ese archivo sintético documenta diez semanas de observación ficticia.",
            "La caminata de cierre reunirá a todos los observadores en la plaza mayor imaginaria. Allí se presentará el atlas completo dentro de la ficción.",
            "Las fichas de repuesto se guardan en una caja común del centro cívico ficticio. Cada observador demo repone las suyas antes de cada salida.",
            "Un taller de dibujo convierte los registros en láminas del atlas imaginario. Cada lámina inventada combina silueta, hábitat y horarios de la prueba.",
            "La presentación del atlas incluirá una caminata guiada por la plaza mayor demo. Los autores ficticios explicarán cada lámina en la ficción.",
        ],
    },
    {
        "country": "ES",
        "slug": "demo-es-02-horarios-salon",
        "title": "Borrador demo: dos versiones sobre horarios del salón comunal",
        "summary": (
            "Borrador ficticio con propuestas contradictorias para repartir "
            "los horarios del salón entre grupos demo."
        ),
        "topics": ["politica"],
        "status": "draft",
        "verification": "conflicting_sources",
        "image": "none",
        "image_alt": "",
        "sources": [
            ("witness", "La propuesta demo A prioriza talleres matutinos."),
            ("witness", "La propuesta demo B prioriza ensayos nocturnos."),
        ],
        "paragraphs": [
            "Este borrador ficticio reúne dos propuestas contradictorias para los horarios del salón comunal demo. La propuesta A prioriza talleres matutinos abiertos dentro de la ficción.",
            "La propuesta B prioriza ensayos nocturnos de grupos cerrados en el mismo escenario. Ambas citan asambleas distintas de la prueba que aún no se concilian.",
            "El borrador permanece sin publicar a propósito para probar que los drafts con conflicto no aparecen en el feed. Ningún salón real está en disputa.",
        ],
    },
    {
        "country": "FR",
        "slug": "demo-fr-01-ruta-lectura",
        "title": "Ruta demo de lectura al aire libre entre plazas vecinales",
        "summary": (
            "Bibliotecas ficticias conectan plazas con clubes breves de "
            "lectura para todas las edades en el barrio demo."
        ),
        "topics": ["cultura", "actualidad"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una lectura en una plaza ficticia",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "Bibliotecas de barrio ficticias abrieron una ruta de lectura al aire libre en una localidad demo de Francia. La agenda conecta plazas, parques y patios escolares imaginarios con clubes breves.",
            "Cada punto tiene una mesa de orientación y lecturas de veinte minutos. La programación evita amplificación para mantener el ambiente de parque dentro de la ficción.",
            "El circuito empieza con cuentos infantiles inventados, sigue con crónica barrial ficticia y termina con poesía breve. Los asistentes demo proponen textos para próximas fechas.",
            "La red ficticia medirá asistencia y devolución durante un mes de prueba. Si la respuesta es positiva en la ficción, la ruta se repetirá los primeros sábados.",
            "La ruta es sintética y cubre cultura y actualidad con lectura media y fotografía demo sin hechos reales.",
            "Las personas voluntarias rotan entre puntos de lectura cada semana ficticia. Así conocen todos los tramos de la ruta demo y a los asistentes habituales.",
            "Los textos propuestos por asistentes se revisan en una mesa abierta de la prueba. Cada propuesta inventada recibe una lectura de prueba antes de entrar al circuito.",
            "Si la asistencia se mantiene en la ficción, la ruta agregará un punto nocturno con lámparas solares demo. Esa extensión queda pendiente del informe mensual ficticio.",
        ],
    },
    {
        "country": "FR",
        "slug": "demo-fr-02-directorio-oficios",
        "title": "Directorio demo de oficios por barrio",
        "summary": (
            "Lista ficticia de carpinteros, costureras y técnicos demo con "
            "horarios y zonas de atención."
        ),
        "topics": ["negocios"],
        "status": "published",
        "verification": "confirmed",
        "image": "none",
        "image_alt": "",
        "sources": [("official", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Francia, vecinos ficticios armaron un directorio de oficios por barrio. Incluye carpinteros, costureras y técnicos inventados con horarios y zonas de atención.",
            "Cada ficha demo indica si atiende a domicilio y qué trabajos no realiza. Un teléfono ficticio central recibe las solicitudes de la prueba.",
            "El directorio es sintético y cubre negocios barriales con lectura corta y sin imagen.",
        ],
    },
    {
        "country": "JP",
        "slug": "demo-jp-01-estacion-lluvia",
        "title": "Estación demo mide lluvia con pluviómetros caseros",
        "summary": (
            "Escuelas ficticias registran precipitaciones con botellas "
            "graduadas para comparar microclimas del barrio demo."
        ),
        "topics": ["tecnologia", "ciencia"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de pluviómetros caseros ficticios",
        "sources": [("primary_source", None), ("official", None)],
        "paragraphs": [
            "En una localidad demo de Japón, escuelas ficticias instalaron pluviómetros caseros hechos con botellas graduadas. Cada escuela registra la lluvia diaria en una tabla mural dentro de la prueba.",
            "Los estudiantes demo comparan microclimas: patios altos contra patios bajos, zonas arboladas contra explanadas. Las diferencias inventadas alimentan clases de medición y promedio.",
            "Un encuentro mensual reúne las tablas de la ficción en un gráfico común. Si un pluviómetro da valores extraños, el grupo revisa su instalación antes de descartar el dato demo.",
            "La red ficticia publicará al cierre un mapa de lluvias del barrio imaginario. Todo es sintético y prueba tecnología y ciencia con lectura media.",
            "Ninguna medición corresponde a estaciones reales: la estación demo solo ejercita el modelo de noticias y el feed por topics.",
            "El encuentro mensual reúne las tablas de todas las escuelas ficticias en un gráfico común. Los picos inventados se marcan con pegatinas de colores en la prueba.",
            "Cuando un pluviómetro da valores extraños, el grupo revisa su nivelación y limpieza antes de descartar el dato. La revisión queda anotada en la ficha demo correspondiente.",
            "Al cierre, la red publicará un mapa de lluvias del barrio imaginario. Ese mapa sintético coronará el proyecto sin representar ninguna estación real.",
        ],
    },
    {
        "country": "JP",
        "slug": "demo-jp-02-lista-salidas",
        "title": "Borrador demo: lista de verificación para salidas nocturnas en grupo",
        "summary": (
            "Borrador ficticio con pasos de organización para caminatas "
            "nocturnas seguras en el barrio demo."
        ),
        "topics": ["seguridad"],
        "status": "draft",
        "verification": "insufficient_sources",
        "image": "none",
        "image_alt": "",
        "sources": [("other", None)],
        "paragraphs": [
            "Este borrador ficticio propone una lista de verificación para salidas nocturnas en grupo dentro del barrio demo. Incluye avisar la ruta, llevar linterna y caminar en parejas en la ficción.",
            "La lista demo aún tiene una sola fuente y mediciones incompletas a propósito. Por eso permanece en borrador con verificación de respaldo insuficiente.",
            "Cuando el grupo ficticio complete sus recorridos de prueba, la lista se publicará en la ficción. Ninguna salida real está involucrada.",
        ],
    },
    {
        "country": "CN",
        "slug": "demo-cn-01-clubes-cocina",
        "title": "Intercambio demo de recetas entre clubes de cocina de varios países",
        "summary": (
            "Clubes ficticios comparten recetas inventadas por correo demo "
            "para una muestra gastronómica sin fronteras."
        ),
        "topics": ["economia", "internacional"],
        "status": "published",
        "verification": "confirmed",
        "image": "ai_generated",
        "image_alt": "Imagen demo generada con IA de una mesa ficticia",
        "sources": [("media", None), ("official", None)],
        "paragraphs": [
            "En una localidad demo de China, un club de cocina ficticio intercambia recetas inventadas con clubes imaginarios de otros países. Cada mes rota un ingrediente base de la prueba: arroz, fideos, calabaza o frijol.",
            "Las recetas viajan por correo demo con fotos del proceso y notas de sustitución. Si un ingrediente no existe en la ficción local, el club propone un reemplazo y anota el cambio.",
            "La muestra anual reúne los platos de la ficción en un salón comunal imaginario. Cada plato lleva una tarjeta con su historia inventada y el club que lo envió.",
            "Un jurado rotativo de vecinos demo prueba porciones pequeñas y vota con fichas de colores. Los criterios ficticios premian el sabor, la presentación y la historia contada.",
            "El intercambio es sintético y permite probar el topic internacional sin cambiar el nivel geográfico país. Las recetas inventadas no representan cocinas reales.",
            "Con clubes de varios países imaginarios, la fixture también ejercita búsquedas por topic internacional dentro de noticias de alcance nacional.",
            "La imagen generada con IA lleva su disclosure y la noticia completa valida el modelo con lectura larga y múltiples fuentes demo.",
            "El cuaderno de sustituciones registra cada reemplazo de ingrediente en la ficción. Esa bitácora inventada ayuda a otros clubes a adaptar recetas demo.",
            "Las hojas de degustación puntúan sabor, presentación e historia con fichas de colores. Cada comensal demo vota una sola vez por plato en la prueba.",
            "Un taller infantil decora las tarjetas de los platos con dibujos de la ficción. Esas tarjetas acompañan cada fuente en la muestra anual imaginaria.",
            "El fondo común de la prueba compra especias y aceites para los clubes. Cada aporte ficticio se anota en un libro abierto del salón demo.",
            "El intercambio cumple un año ficticio con una cena de aniversario en la prueba. Cada club cocina la receta que más votos recibió en la ficción.",
            "Al cierre, las recetas se encuadernarán en un recetario mural del salón. Ese recetario sintético coronará el proyecto sin representar cocinas reales.",
            "Cada club nombra un corresponsal rotativo para el intercambio de la ficción. El corresponsal demo redacta la carta mensual y adjunta las fotos del proceso.",
            "Las fotos del proceso se archivan en un álbum común del salón ficticio. Ese álbum inventado documenta un año de cocinas imaginarias.",
            "La cena de aniversario cerrará con brindis de jugos de la prueba. Cada club demo propondrá el ingrediente base del año siguiente.",
        ],
    },
    {
        "country": "CN",
        "slug": "demo-cn-02-estiramiento-parques",
        "title": "Grupo demo prueba sesiones de estiramiento en parques",
        "summary": (
            "Sesiones ficticias de movilidad suave al amanecer con rutinas "
            "guiadas por voluntarios demo."
        ),
        "topics": ["deportes"],
        "status": "published",
        "verification": "developing",
        "image": "photograph",
        "image_alt": "Fotografía demo de una sesión ficticia en un parque",
        "sources": [("witness", None), ("official", None)],
        "paragraphs": [
            "En una localidad demo de China, un grupo ficticio prueba sesiones de estiramiento en parques al amanecer. Las rutinas duran media hora y las guía un voluntario demo dentro de la ficción.",
            "Cada sesión combina respiración, movilidad de articulaciones y estiramientos suaves. Los participantes anotan en una ficha inventada cómo se sienten antes y después.",
            "La prueba sigue en desarrollo porque el grupo aún ajusta horarios según la asistencia ficticia. Si la constancia se confirma en el escenario, pedirán un espacio fijo semanal.",
            "La sesión es sintética y cubre deportes con lectura media y verificación developing sin consejos médicos reales.",
            "Con parques de distintos barrios ficticios, el grupo demo también muestra la cobertura geográfica del dataset.",
            "La inscripción se hace en una hoja mural del parque ficticio. Cada participante anota su nombre inventado y su nivel para balancear los grupos demo.",
            "Si la constancia se confirma en el escenario, el grupo pedirá un espacio fijo semanal. La solicitud ficticia incluirá asistencia promedio y horarios preferidos.",
            "Las sesiones rotan entre tres parques imaginarios para repartir el uso. Cada parque demo aporta un punto de encuentro distinto dentro de la prueba.",
        ],
    },
    {
        "country": "EG",
        "slug": "demo-eg-01-postales-escuelas",
        "title": "Muestra demo de postales ilustradas entre escuelas de varios países",
        "summary": (
            "Escuelas ficticias intercambian postales dibujadas a mano sobre "
            "la vida cotidiana de sus barrios demo."
        ),
        "topics": ["cultura", "internacional"],
        "status": "published",
        "verification": "confirmed",
        "image": "ai_modified",
        "image_alt": "Imagen demo alterada con IA de postales ficticias",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de Egipto, escuelas ficticias intercambian postales ilustradas con escuelas imaginarias de otros países. Cada postal dibujada a mano muestra la vida cotidiana del barrio demo.",
            "Los temas rotan cada mes en la ficción: mercados, juegos, transportes y fiestas inventadas. Al reverso, cada clase escribe tres preguntas para sus corresponsales demo.",
            "La muestra anual cuelga las postales en el pasillo de la escuela ficticia. Los visitantes votan con pegatinas cuáles historias les gustaría conocer en persona dentro de la prueba.",
            "El intercambio es sintético y prueba cultura e internacional con imagen ai_modified y su disclosure. Ninguna escuela real participa.",
            "Con remitentes de varios países imaginarios, la fixture demuestra cómo el topic internacional convive con el alcance país de cada noticia.",
            "Los temas mensuales de la ficción cubren mercados, juegos, transportes y fiestas inventadas. Cada clase elige su enfoque y lo dibuja a su manera demo.",
            "La muestra anual colgará las postales en el pasillo de la escuela ficticia. Los visitantes votarán con pegatinas sus historias favoritas de la prueba.",
            "Cada postal viaja con tres preguntas para los corresponsales demo. Las respuestas regresan en el siguiente envío del intercambio imaginario.",
        ],
    },
    {
        "country": "EG",
        "slug": "demo-eg-02-fichas-sueno",
        "title": "Dos fichas demo discrepan sobre horas de sueño en la ficción",
        "summary": (
            "Apuntes ficticios contradictorios sobre descanso que dejan la "
            "nota demo en estado de disputa."
        ),
        "topics": ["salud", "ciencia"],
        "status": "published",
        "verification": "conflicting_sources",
        "image": "none",
        "image_alt": "",
        "sources": [
            ("primary_source", "La ficha demo A afirma ocho horas en la ficción."),
            ("primary_source", "La ficha demo B afirma seis horas en la ficción."),
        ],
        "paragraphs": [
            "En un club de salud ficticio, dos fichas demo discrepan sobre las horas de sueño recomendadas dentro de la ficción. La ficha A anota ocho horas como meta de la prueba imaginaria.",
            "La ficha B, con registros del mismo periodo ficticio, anota seis horas y descanso fraccionado. Ambas usan el mismo formato de la prueba pero llegan a conclusiones opuestas.",
            "La contradicción es deliberada y deja la nota en conflicting_sources. Ninguna ficha describe personas reales ni sustituye consejo médico.",
        ],
    },
    {
        "country": "ZA",
        "slug": "demo-za-01-limpieza-parques",
        "title": "Jornadas demo de limpieza de parques con registro de residuos",
        "summary": (
            "Brigadas ficticias limpian parques demo y clasifican residuos "
            "para planificar contenedores."
        ),
        "topics": ["medio_ambiente"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una jornada ficticia en un parque",
        "sources": [("official", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Sudáfrica, brigadas vecinales ficticias organizan jornadas de limpieza en tres parques imaginarios. Cada jornada dura tres horas dentro de la ficción y cierra con un conteo de bolsas.",
            "Los residuos se clasifican en la prueba: plásticos, vidrio, papel y restos de poda. Una tabla mural del salón demo muestra qué parque ficticio genera cada tipo de residuo.",
            "Con esos datos inventados, la asamblea demo decide dónde pedir contenedores nuevos y dónde reforzar turnos. Ningún parque real fue intervenido en esta historia.",
            "Las brigadas ficticias también marcan puntos de acumulación recurrente en un mapa mural. Esos puntos reciben visitas de seguimiento en la siguiente jornada de la ficción.",
            "Un taller previo enseña a separar sin riesgos dentro de la prueba: guantes, pinzas y bolsas de colores. La seguridad de la jornada demo está primero en cada convocatoria ficticia.",
            "Al cierre del ciclo imaginario, el colectivo publica un resumen con kilos clasificados por parque. Todo es sintético y prueba medio ambiente con lectura larga.",
            "La fixture completa valida el modelo, usa fotografía demo y deja fuentes claramente identificadas como ficticias.",
            "Una escuela ficticia adoptó el parque norte como aula abierta de la prueba. Sus estudiantes pesan las bolsas y dibujan la gráfica semanal demo.",
            "El cobertizo de herramientas presta pinzas, guantes y rastrillos en cada jornada. Cada préstamo ficticio se anota y se devuelve al cierre en la ficción.",
            "El pesaje ritual cierra cada jornada con aplausos de la brigada demo. Los kilos clasificados se cantan en voz alta antes de anotarlos.",
            "Un mural fotográfico muestra el antes y después de cada parque imaginario. Las fotos pertenecen al escenario demo y no retratan lugares reales.",
            "En temporada de lluvias ficticia, las jornadas se acortan a dos horas. La regla demo prioriza la seguridad sobre el conteo en esos días.",
            "El informe anual reunirá asistencia, kilos y contenedores pedidos en la ficción. Ese informe sintético cerrará el ciclo del proyecto demo.",
            "Los comercios cercanos donan bolsas y guantes a las brigadas de la prueba. Cada donación ficticia se agradece en la cartelera del parque demo.",
            "El conteo por parque se compara mes a mes en la tabla mural ficticia. Las tendencias inventadas orientan los pedidos de contenedores.",
            "La brigada más constante elige primero su parque en el ciclo siguiente demo. Ese reconocimiento simbólico premia asistencia dentro de la ficción.",
        ],
    },
    {
        "country": "ZA",
        "slug": "demo-za-02-turnos-vigilancia",
        "title": "Borrador demo: dos propuestas para turnos de vigilancia vecinal",
        "summary": (
            "Borrador ficticio con esquemas opuestos de rondas que aún no se "
            "concilian en la asamblea demo."
        ),
        "topics": ["seguridad", "politica"],
        "status": "draft",
        "verification": "conflicting_sources",
        "image": "none",
        "image_alt": "",
        "sources": [
            ("witness", "El esquema demo A propone rondas cortas frecuentes."),
            ("witness", "El esquema demo B propone rondas largas espaciadas."),
        ],
        "paragraphs": [
            "Este borrador ficticio compara dos esquemas opuestos de rondas vecinales en un barrio demo. El esquema A propone rondas cortas y frecuentes dentro de la ficción.",
            "El esquema B propone rondas largas y espaciadas en el mismo escenario. Cada esquema cita recorridos distintos de la prueba que aún no se concilian.",
            "El documento permanece en borrador con conflicto deliberado para probar drafts no visibles. Ningún barrio real está involucrado.",
        ],
    },
    {
        "country": "AU",
        "slug": "demo-au-01-ciclismo-recreativo",
        "title": "Ciclismo demo recreativo con rutas de baja dificultad",
        "summary": (
            "Rodadas ficticias de fin de semana con guías, puntos de agua y "
            "reglas de convivencia en ciclovías demo."
        ),
        "topics": ["deportes", "medio_ambiente"],
        "status": "published",
        "verification": "confirmed",
        "image": "photograph",
        "image_alt": "Fotografía demo de una rodada ficticia al amanecer",
        "sources": [("official", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Australia, un club ficticio organiza rodadas recreativas de fin de semana. Las rutas imaginarias usan ciclovías demo de baja dificultad con guías en cabeza y cola.",
            "Cada rodada incluye paradas de agua ficticias cada cuarenta minutos. Los guías demo revisan frenos y cascos antes de partir dentro de la ficción.",
            "Las reglas de convivencia inventadas piden avisar al rebasar y mantener distancia en bajadas. Nadie compite: el grupo rueda junto de principio a fin en la prueba.",
            "Al cierre, el club anota asistencia y pinchazos en un cuaderno demo. Esos datos ficticios definen cuántos kits de reparación llevar la próxima vez.",
            "La rodada es sintética y prueba deportes y medio ambiente con lectura media y fotografía demo sin eventos reales.",
            "Las reglas inventadas piden avisar al rebasar y mantener distancia en bajadas. Los guías demo repiten las consignas antes de cada partida en la ficción.",
            "El cuaderno demo registra asistencia y pinchazos de cada rodada. Con esos datos ficticios se calcula cuántos kits de reparación llevar la próxima vez.",
            "Las paradas de agua se ubican cada cuarenta minutos del recorrido imaginario. Cada parada demo tiene sombra y espacio para revisar bicicletas.",
        ],
    },
    {
        "country": "AU",
        "slug": "demo-au-02-curso-computadoras",
        "title": "Curso demo de reparación básica de computadoras para vecinos",
        "summary": (
            "Clases ficticias de limpieza, respaldo y reinstalación para "
            "alargar la vida de equipos demo."
        ),
        "topics": ["educacion", "tecnologia"],
        "status": "published",
        "verification": "confirmed",
        "image": "illustration",
        "image_alt": "Ilustración demo de un aula ficticia con equipos",
        "sources": [("official", None), ("primary_source", None)],
        "paragraphs": [
            "En una localidad demo de Australia, vecinos ficticios dictan un curso de reparación básica de computadoras. Las clases se celebran en un aula prestada con equipos donados dentro de la ficción.",
            "El temario demo cubre limpieza interna, respaldo de archivos y reinstalación del sistema. Cada estudiante practica con un equipo asignado de la prueba y anota cada paso en una ficha.",
            "Un módulo enseña a distinguir fallos de software y de hardware con pruebas simples. La regla ficticia es respaldar siempre antes de abrir cualquier equipo demo.",
            "El curso incluye una sesión de seguridad básica inventada: contraseñas, actualizaciones y cuidado con adjuntos desconocidos. Todo el material pertenece al escenario demo.",
            "Los egresados ficticios ofrecen una jornada mensual de ayuda a otros vecinos de la prueba. Esa jornada cierra el ciclo dentro de la ficción sin atender equipos reales.",
            "Al final, el grupo publica una guía ilustrada con los diez problemas más comunes del aula imaginaria. La guía es sintética y prueba educación y tecnología con lectura larga.",
            "Ningún equipo real fue reparado: la fixture ejercita el modelo completo con ilustración demo y fuentes ficticias.",
            "La inscripción se hace en una lista mural del centro vecinal ficticio. Cada estudiante anota su nombre inventado y su nivel inicial en la prueba.",
            "Los bancos de práctica tienen un equipo asignado por pareja demo. Cada pareja sigue la ficha paso a paso sin adelantar etapas en la ficción.",
            "El estante de repuestos guarda discos, memorias y cargadores donados a la prueba. Cada pieza ficticia lleva una etiqueta con su estado.",
            "Una charla invitada explica el cuidado de baterías con ejemplos del aula imaginaria. La charla demo cierra con preguntas abiertas de la prueba.",
            "El diploma simbólico se entrega a quienes completan las ocho sesiones ficticias. Ese diploma inventado no acredita competencias reales.",
            "El curso cumple un ciclo con una jornada de ayuda abierta en la ficción. Los egresados atienden consultas de vecinos bajo supervisión demo.",
            "La pizarra del aula muestra el diagrama de un equipo abierto de la ficción. Cada parte inventada lleva su nombre para memorizar componentes demo.",
            "Las parejas avanzadas ayudan a las nuevas en la tercera sesión ficticia. Esa tutoría demo refuerza lo aprendido sin calificaciones reales.",
            "El inventario mensual cuenta herramientas y repuestos del aula imaginaria. Cada faltante demo se repone con el fondo común de la prueba.",
        ],
    },
    {
        "country": "NZ",
        "slug": "demo-nz-01-simulacro-evacuacion",
        "title": "Simulacro demo de evacuación en centro comunal",
        "summary": (
            "Vecinos ficticios practican rutas de salida y puntos de encuentro "
            "en un simulacro anual del barrio demo."
        ),
        "topics": ["seguridad", "actualidad"],
        "status": "published",
        "verification": "confirmed",
        "image": "ai_generated",
        "image_alt": "Imagen demo generada con IA de un simulacro ficticio",
        "sources": [("official", None), ("witness", None)],
        "paragraphs": [
            "En una localidad demo de Nueva Zelanda, vecinos ficticios practicaron un simulacro de evacuación en el centro comunal imaginario. Sonó la alarma de prueba y cada grupo siguió su ruta marcada.",
            "Los monitores demo cronometraron la salida por puertas y verificaron la lista en el punto de encuentro. Nadie corrió en la ficción: caminar ordenado fue la consigna de la jornada.",
            "Al cierre, la asamblea ficticia revisó tiempos y cuellos de botella del escenario. Acordaron señalizar mejor una salida lateral antes del próximo simulacro demo.",
            "El ejercicio es sintético y prueba seguridad y actualidad con imagen generada y su disclosure. Ninguna emergencia real ocurrió.",
            "Con rutas y roles claros, el simulacro demo muestra cómo una noticia de servicio ficticia cabe en el feed junto a cultura y deportes.",
            "Los monitores cronometraron la salida por cada puerta del centro ficticio. La lista de verificación se completó en el punto de encuentro sin faltantes demo.",
            "La asamblea revisó tiempos y cuellos de botella del escenario inventado. La salida lateral recibirá mejor señalización antes del próximo simulacro.",
            "El informe de la prueba quedará pegado en la cartelera del centro demo. Servirá de referencia cuando se incorporen vecinos nuevos a la ficción.",
        ],
    },
    {
        "country": "NZ",
        "slug": "demo-nz-02-foro-plazas",
        "title": "Foro demo entre asambleas vecinales de varios países sobre plazas",
        "summary": (
            "Asambleas ficticias comparan diseños de plazas por correo demo "
            "para una guía común de espacios públicos."
        ),
        "topics": ["internacional", "politica"],
        "status": "published",
        "verification": "developing",
        "image": "ai_modified",
        "image_alt": "Imagen demo alterada con IA de una plaza ficticia",
        "sources": [("official", None), ("media", None)],
        "paragraphs": [
            "En una localidad demo de Nueva Zelanda, la asamblea vecinal ficticia abrió un foro con asambleas imaginarias de otros países. El tema de la prueba: cómo diseñar plazas que inviten a quedarse.",
            "Cada asamblea envió por correo demo fotos de su plaza ficticia con notas sobre sombra, bancas y juegos. Las coincidencias inventadas saltaron rápido: todas pedían más árboles y bebederos.",
            "Las diferencias también se anotaron en la ficción: unas plazas priorizan mercados semanales y otras canchas pequeñas. El foro demo respeta ambas preferencias sin imponer un modelo único.",
            "La guía común sigue en redacción dentro del escenario, por eso la verificación es developing. Faltan los capítulos de mantenimiento y de turnos de limpieza imaginarios.",
            "Un borrador circuló entre las asambleas de la prueba para comentarios escritos. Cada comentario demo se responde en la siguiente ronda del foro ficticio.",
            "El foro es sintético y prueba el topic internacional con alcance país. Ninguna asamblea real participa y la imagen alterada lleva su disclosure.",
            "Cuando la guía esté lista en la ficción, se imprimirá en cartel para las plazas demo. Hasta entonces, esta fixture ejercita lectura larga y verificación en desarrollo.",
            "El capítulo de mantenimiento propone turnos mensuales por cuadra ficticia. Cada turno demo incluye riego, barrido y revisión de bancas en la prueba.",
            "Los turnos de limpieza se sortean con fichas numeradas en la asamblea imaginaria. Nadie repite turno hasta completar la ronda en la ficción.",
            "Cada comentario al borrador recibe respuesta escrita en la siguiente ronda. Ese diálogo inventado mantiene vivo el foro entre asambleas demo.",
            "Una mesa de ayuda traduce los aportes entre idiomas de la prueba. Cada traducción ficticia se revisa por dos lectores antes de circular.",
            "El foro anual reunirá delegados de todas las asambleas imaginarias. La sede rotará cada año dentro de la ficción demo.",
            "Un fondo común imprimirá la guía final para las plazas de la prueba. Cada plaza demo recibirá dos carteles plastificados en la ficción.",
            "Las fotos de plazas se archivan en carpetas por país imaginario. Cada carpeta demo reúne diseños, notas y comentarios de la prueba.",
            "La guía dedicará un capítulo a juegos infantiles con ejemplos ficticios. Cada ejemplo inventado indica edades y materiales de la prueba.",
            "La portada de la guía llevará un collage de plazas dibujadas por niños demo. Esas ilustraciones pertenecen a la ficción del foro.",
        ],
    },
)


def _spec_news_id(spec_index: int) -> ObjectId:
    return _news_id(spec_index)


def _spec_sources(spec: dict) -> list[dict]:
    """Construye las fuentes demo de una especificación (una sola pasada)."""
    items = []
    for position, (source_type, supports) in enumerate(spec["sources"], start=1):
        items.append(
            {
                "name": f"Demo News Source {position} ({spec['slug']})",
                "url": f"https://example.com/demo/{spec['slug']}/source-{position}",
                "sourceType": source_type,
                "publishedAt": None,
                "accessedAt": DEMO_NEWS_SOURCE_ACCESSED_AT,
                "supports": supports,
            }
        )
    return items


def build_demo_news() -> list[News]:
    """Construye las 32 noticias demo validando cada una con `News`."""
    items: list[News] = []
    for index, spec in enumerate(_SPECS):
        content = "\n\n".join(spec["paragraphs"])
        word_count, reading_minutes = compute_reading_time(content)
        status = NewsStatus(spec["status"])
        published_at = _published_at(index) if status == NewsStatus.published else None
        stamp = published_at if published_at is not None else _draft_at(index)
        verification_status = VerificationStatus(spec["verification"])
        image_doc = _image(spec["image"], spec["slug"], spec["image_alt"])
        news = News(
            _id=_spec_news_id(index),
            slug=spec["slug"],
            title=spec["title"],
            summary=spec["summary"],
            content=content,
            authorId=DEMO_NEWS_AUTHOR_ID,
            status=status,
            topics=list(spec["topics"]),
            keywords=[spec["topics"][0], "demo", "sintetico"],
            geographicScope=GeographicScope(
                level=LocationLevel.country,
                locationIds=[CATALOG_LOCATION_IDS[spec["country"]]],
            ),
            verification=Verification(
                status=verification_status,
                reviewedBy=None,
                reviewedAt=None,
                notes=_SYNTHETIC_NOTES[spec["verification"]],
            ),
            sources=_spec_sources(spec),
            image=Image(**image_doc),
            aiAssistance=AiAssistance(
                summaryGenerated=False,
                topicsGenerated=False,
                imageGenerated=(spec["image"] == ImageType.ai_generated.value),
                humanReviewed=(status == NewsStatus.published)
                and spec["verification"]
                in {"confirmed", "developing"},
            ),
            wordCount=word_count,
            estimatedReadingMinutes=reading_minutes,
            publishedAt=published_at,
            createdAt=stamp,
            updatedAt=stamp,
        )
        items.append(news)
    return items


def get_demo_news_documents() -> list[dict]:
    """Devuelve los documentos listos para Mongo (copias profundas)."""
    return [news.model_dump_mongo() for news in build_demo_news()]


def get_expected_slugs() -> list[str]:
    return [spec["slug"] for spec in _SPECS]


def demo_news_summary() -> str:
    return (
        f"DEMO / SYNTHETIC DATA: {EXPECTED_NEWS_COUNT} noticias ficticias, "
        "2 por cada uno de los 16 países, sin hechos reales."
    )


if __name__ == "__main__":
    print(demo_news_summary())
    print(f"Slugs: {len(get_expected_slugs())}")
