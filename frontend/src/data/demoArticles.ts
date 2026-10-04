import type { ArticleImage, CategoryId, NewsArticle } from "../types";

function placeholderImage(alt: string): ArticleImage {
  return {
    src: null,
    alt,
    width: 960,
    height: 540,
    credit: "Imagen ilustrativa pendiente",
    sourceUrl: "",
    license: "Placeholder local; requiere reemplazo por foto con licencia verificada.",
  };
}

function article(
  data: Omit<NewsArticle, "isDemo" | "source" | "image"> & {
    imageAlt: string;
  },
): NewsArticle {
  const { imageAlt, ...articleData } = data;
  return {
    ...articleData,
    isDemo: true,
    source: "Edición demo",
    image: placeholderImage(imageAlt),
  };
}

export const FEATURED_ARTICLE_ID = "demo-actualidad-001";
export const SECONDARY_ARTICLE_IDS = ["demo-tecnologia-001", "demo-economia-001"];

export const DEMO_ARTICLES: NewsArticle[] = [
  article({
    id: "demo-actualidad-001",
    slug: "paseo-peatonal-comercio-descanso",
    title: "Un nuevo paseo peatonal reúne comercio y espacios de descanso",
    summary:
      "La iniciativa piloto combina bancas, sombra y horarios de carga para ordenar una zona con alta circulación vecinal.",
    category: "actualidad",
    author: "Lucía Andrade",
    publishedAt: "2026-10-04T08:30:00-06:00",
    readingMinutes: 4,
    imageAlt: "Calle peatonal arbolada con bancas y comercios de barrio.",
    body: [
      "La municipalidad ficticia de San Jacinto abrió esta semana un tramo peatonal temporal en una avenida de comercio barrial. El proyecto busca medir cómo cambia la circulación cuando los autos comparten menos espacio con quienes caminan.",
      "Durante la primera etapa se instalaron bancas, maceteros y señalización removible. Los locales mantienen horarios de carga por la mañana y por la noche para evitar que la operación diaria quede interrumpida.",
      "Vecinos consultados por la redacción demo destacaron que el área se siente más tranquila, aunque pidieron mejorar la sombra en las horas de mayor sol. Los organizadores recopilarán observaciones durante seis semanas.",
      "El piloto no representa una decisión definitiva. Al cierre del periodo se publicará un informe con conteos de paso, tiempos de entrega y comentarios de comerciantes para decidir si el paseo continúa.",
    ],
  }),
  article({
    id: "demo-actualidad-002",
    slug: "red-barrial-alertas-lluvia",
    title: "Barrios coordinan una red de alertas tempranas durante la temporada de lluvia",
    summary:
      "Comités comunitarios ensayan reportes por zonas para informar en minutos sobre calles anegadas y rutas alternas.",
    category: "actualidad",
    author: "Mateo Rivas",
    publishedAt: "2026-10-03T17:10:00-06:00",
    readingMinutes: 3,
    imageAlt: "Personas revisando un mapa de barrio durante una jornada comunitaria.",
    body: [
      "Cinco barrios de la ciudad demo activaron una red de mensajes para compartir alertas de lluvia intensa, pasos cerrados y rutas alternas. El ejercicio busca evitar información dispersa cuando las tormentas llegan en hora pico.",
      "Cada zona tendrá dos enlaces voluntarios encargados de verificar reportes antes de publicarlos. La regla principal es distinguir entre observaciones confirmadas y advertencias preventivas.",
      "El sistema funcionará con herramientas comunes de mensajería, sin recopilar ubicación automática. Quienes participen podrán reportar únicamente el punto de la incidencia y una breve descripción.",
      "La prueba durará hasta finales de octubre. Si resulta útil, los comités proponen convertirla en una guía abierta para mercados, escuelas y transporte vecinal.",
    ],
  }),
  article({
    id: "demo-actualidad-003",
    slug: "escuelas-abren-patios-familias",
    title: "Escuelas abren sus patios para actividades familiares de fin de semana",
    summary:
      "El plan piloto permite usar canchas y salones comunes con inscripción previa y supervisión de docentes voluntarios.",
    category: "actualidad",
    author: "Camila Soto",
    publishedAt: "2026-10-02T12:45:00-06:00",
    readingMinutes: 4,
    imageAlt: "Patio escolar con familias participando en actividades recreativas.",
    body: [
      "Tres escuelas públicas de la zona norte demo abrirán sus patios los sábados por la mañana para talleres, lectura y juegos familiares. La medida responde a solicitudes de espacios seguros cerca de casa.",
      "Las actividades serán gratuitas y tendrán cupo limitado para cuidar la limpieza y seguridad del inmueble. Cada familia deberá registrarse con anticipación y aceptar reglas de uso compartido.",
      "Docentes voluntarios coordinarán los primeros encuentros junto con organizaciones juveniles. La agenda incluye ajedrez, lectura en voz alta, dibujo y juegos cooperativos.",
      "La dirección escolar aclaró que el programa no reemplaza clases ni servicios de cuidado. Es una prueba de convivencia comunitaria que se evaluará con asistencia y encuestas breves.",
    ],
  }),
  article({
    id: "demo-actualidad-004",
    slug: "mesa-vecinal-transporte-nocturno",
    title: "Una mesa vecinal revisa opciones para mejorar el transporte nocturno",
    summary:
      "Usuarios, pilotos y comercios preparan un diagnóstico sobre rutas con baja frecuencia después de las ocho de la noche.",
    category: "actualidad",
    author: "Elena Morán",
    publishedAt: "2026-10-01T20:00:00-06:00",
    readingMinutes: 3,
    imageAlt: "Parada de autobús iluminada con personas esperando por la noche.",
    body: [
      "Una mesa de trabajo ficticia reunió a usuarios, pilotos y comercios para revisar la movilidad nocturna en tres corredores urbanos. El objetivo es mapear horarios críticos sin anunciar todavía cambios de tarifa o ruta.",
      "Los participantes recopilarán registros de espera y puntos con iluminación deficiente. También se incluirán testimonios de trabajadores que salen tarde de restaurantes, farmacias y centros de estudio.",
      "La coordinación insistió en que los datos no incluirán información personal. Cada reporte se registrará por tramo, hora aproximada y tipo de dificultad encontrada.",
      "El diagnóstico se entregará a finales de mes. Con esa base se discutirán ajustes piloto, como salidas coordinadas o paradas seguras en puntos con mayor demanda.",
    ],
  }),
  article({
    id: "demo-tecnologia-001",
    slug: "sensores-huertos-urbanos",
    title: "Jóvenes desarrollan sensores para cuidar los huertos urbanos",
    summary:
      "El prototipo mide humedad y temperatura con piezas de bajo costo para apoyar a grupos que cultivan en terrazas y patios.",
    category: "tecnologia",
    author: "Nadia Lemus",
    publishedAt: "2026-10-04T07:20:00-06:00",
    readingMinutes: 4,
    imageAlt: "Plantas en macetas junto a pequeños sensores electrónicos.",
    body: [
      "Un grupo de estudiantes demo presentó sensores sencillos para monitorear huertos urbanos. La propuesta nació de visitas a terrazas comunitarias donde el riego depende de turnos y experiencia manual.",
      "El dispositivo mide humedad del suelo y temperatura ambiente. Cuando detecta sequedad persistente, muestra una alerta local para que el equipo revise la planta antes de regar por costumbre.",
      "El proyecto prioriza piezas fáciles de conseguir y reparación abierta. Sus creadores preparan una guía para que otros grupos puedan ensamblarlo sin depender de una tienda especializada.",
      "La siguiente fase será probarlo durante un mes en cuatro huertos con condiciones distintas. Los resultados definirán si conviene agregar energía solar o una carcasa resistente a lluvia.",
    ],
  }),
  article({
    id: "demo-tecnologia-002",
    slug: "biblioteca-presta-tabletas",
    title: "Una biblioteca presta tabletas para cursos digitales de personas mayores",
    summary:
      "El programa acompaña a usuarios que quieren aprender trámites básicos, videollamadas y lectura en pantalla.",
    category: "tecnologia",
    author: "Óscar Vidal",
    publishedAt: "2026-10-03T10:15:00-06:00",
    readingMinutes: 3,
    imageAlt: "Persona mayor usando una tableta en una mesa de biblioteca.",
    body: [
      "La biblioteca central demo inició un préstamo interno de tabletas para talleres digitales dirigidos a personas mayores. Los dispositivos se usan dentro del edificio y cuentan con accesos simplificados.",
      "Las sesiones cubren videollamadas, búsqueda de información confiable y lectura de documentos. El personal evita tecnicismos y trabaja con grupos pequeños para resolver dudas frecuentes.",
      "El programa también enseña medidas básicas de seguridad, como reconocer mensajes sospechosos y no compartir códigos de verificación. Cada práctica se repite con ejemplos cotidianos.",
      "Si la asistencia se mantiene, la biblioteca ampliará horarios y convocará a voluntarios universitarios para acompañar a nuevos participantes.",
    ],
  }),
  article({
    id: "demo-tecnologia-003",
    slug: "mapa-calor-parques",
    title: "Un mapa ciudadano registra zonas de calor en parques urbanos",
    summary:
      "La herramienta permite comparar sombra, bancas y fuentes para priorizar mejoras en espacios públicos.",
    category: "tecnologia",
    author: "Marina Cifuentes",
    publishedAt: "2026-10-02T09:05:00-06:00",
    readingMinutes: 4,
    imageAlt: "Teléfono mostrando un mapa junto a árboles de un parque urbano.",
    body: [
      "Un colectivo de tecnología cívica demo lanzó un mapa para registrar puntos de calor en parques. La idea es combinar mediciones manuales con observaciones sobre sombra, descanso e hidratación.",
      "Los reportes se hacen por sectores y no requieren cuenta personal. Quienes participan pueden marcar si hay árboles, bancas, bebederos o superficies que aumentan la sensación térmica.",
      "El equipo aclara que el mapa no reemplaza estudios ambientales formales. Funciona como una señal temprana para orientar recorridos técnicos y conversaciones comunitarias.",
      "En noviembre se publicará una visualización abierta con los parques más reportados. Las recomendaciones buscarán soluciones simples, como sombra temporal y mantenimiento de fuentes.",
    ],
  }),
  article({
    id: "demo-tecnologia-004",
    slug: "laboratorio-audio-podcast-local",
    title: "Un laboratorio de audio enseña a producir podcasts locales",
    summary:
      "El espacio comunitario presta micrófonos y capacita a vecinos en guion, grabación y edición responsable.",
    category: "tecnologia",
    author: "Bruno Herrera",
    publishedAt: "2026-10-01T15:30:00-06:00",
    readingMinutes: 3,
    imageAlt: "Micrófonos y audífonos sobre una mesa de producción de audio.",
    body: [
      "Un centro cultural demo abrió un laboratorio de audio para vecinos interesados en contar historias locales. El espacio presta micrófonos, audífonos y una sala pequeña con tratamiento acústico básico.",
      "Los talleres empiezan con guion y verificación de datos antes de pasar a la edición. La coordinación busca evitar que la emoción por publicar eclipse la responsabilidad narrativa.",
      "Cada participante producirá una pieza breve sobre memoria barrial, oficios o cultura cotidiana. Las publicaciones deberán incluir autorización de voces grabadas.",
      "El laboratorio funcionará dos tardes por semana. Si el programa crece, se creará un archivo sonoro de acceso público con episodios seleccionados.",
    ],
  }),
  article({
    id: "demo-economia-001",
    slug: "mercado-digital-comunitario",
    title: "Pequeños comercios prueban un mercado digital comunitario",
    summary:
      "La plataforma piloto agrupa inventarios de tiendas cercanas para que compradores comparen disponibilidad antes de salir.",
    category: "economia",
    author: "Irene Paredes",
    publishedAt: "2026-10-04T06:50:00-06:00",
    readingMinutes: 4,
    imageAlt: "Puesto de mercado con productos frescos y una libreta de pedidos.",
    body: [
      "Treinta comercios demo participan en un mercado digital comunitario que muestra productos disponibles por barrio. La plataforma no procesa pagos; su primera meta es reducir viajes innecesarios.",
      "Cada tienda actualiza una lista sencilla de inventario destacado. Los clientes pueden revisar horarios, medios de contacto y notas sobre productos agotados antes de llamar o visitar.",
      "La cámara de comercio local acompañará la prueba con capacitación en fotografía básica y atención por mensajes. El reto principal será mantener información actualizada sin cargar de trabajo a los vendedores.",
      "El piloto durará ocho semanas. Si se confirma uso constante, el equipo evaluará pedidos reservados y métricas anónimas para entender qué categorías generan más consultas.",
    ],
  }),
  article({
    id: "demo-economia-002",
    slug: "cooperativas-compras-conjuntas",
    title: "Cooperativas organizan compras conjuntas para reducir costos logísticos",
    summary:
      "Productores de tres municipios coordinan entregas semanales y comparten transporte refrigerado de forma rotativa.",
    category: "economia",
    author: "Tomás Arévalo",
    publishedAt: "2026-10-03T13:00:00-06:00",
    readingMinutes: 4,
    imageAlt: "Cajas de productos agrícolas ordenadas para distribución local.",
    body: [
      "Tres cooperativas ficticias comenzaron a coordinar compras y entregas conjuntas para reducir costos de transporte. La iniciativa se centra en productos perecederos que requieren rutas constantes.",
      "El modelo reparte espacios en un vehículo refrigerado según volumen semanal. Cada cooperativa mantiene sus clientes, pero comparte horarios y puntos de entrega cuando las rutas coinciden.",
      "Los organizadores esperan ahorrar combustible y disminuir pérdidas por retrasos. También analizan crear etiquetas comunes para identificar lotes sin borrar la marca de cada productor.",
      "La prueba finalizará con una comparación de costos antes y después del esquema. Los resultados se discutirán en asamblea antes de decidir una operación permanente.",
    ],
  }),
  article({
    id: "demo-economia-003",
    slug: "talleres-presupuesto-hogares",
    title: "Talleres de presupuesto ayudan a hogares a ordenar gastos variables",
    summary:
      "La metodología usa sobres simbólicos y registros semanales para planificar compras, transporte y emergencias pequeñas.",
    category: "economia",
    author: "Valeria Nájera",
    publishedAt: "2026-10-02T18:20:00-06:00",
    readingMinutes: 3,
    imageAlt: "Cuaderno de presupuesto familiar con calculadora y recibos.",
    body: [
      "Una organización comunitaria demo inició talleres para que familias registren gastos variables sin depender de aplicaciones complejas. El método combina sobres simbólicos y revisiones semanales.",
      "Cada hogar define categorías propias, como transporte, alimentos fuera de casa o emergencias pequeñas. La dinámica evita juzgar decisiones y se concentra en detectar patrones repetidos.",
      "Facilitadores explican que el objetivo no es eliminar todos los gastos flexibles, sino anticiparlos. También se trabaja una reserva mínima para imprevistos de baja escala.",
      "El programa entregará plantillas impresas y una versión digital opcional. Al final, las familias podrán comparar cuatro semanas de registros y ajustar su plan mensual.",
    ],
  }),
  article({
    id: "demo-economia-004",
    slug: "feria-emprendimientos-reparacion",
    title: "Una feria de reparación impulsa oficios y consumo responsable",
    summary:
      "Zapateros, técnicos y costureras ofrecen diagnósticos gratuitos para extender la vida útil de objetos cotidianos.",
    category: "economia",
    author: "Renata Molina",
    publishedAt: "2026-10-01T11:40:00-06:00",
    readingMinutes: 3,
    imageAlt: "Mesa de reparación con herramientas, telas y objetos cotidianos.",
    body: [
      "Una feria demo reunió a oficios de reparación para promover consumo responsable y visibilizar pequeños negocios. La jornada incluyó diagnósticos gratuitos y presupuestos transparentes.",
      "Participaron zapateros, técnicos de electrodomésticos, costureras y reparadores de bicicletas. Cada puesto explicó qué casos podían resolverse en el día y cuáles requerían taller.",
      "La organización buscó que la actividad no compitiera por precio, sino por confianza y claridad. Las personas asistentes recibieron recomendaciones para cuidar objetos de uso diario.",
      "Los emprendedores evaluarán si conviene repetir la feria cada dos meses. También proponen un directorio barrial de reparación con horarios y especialidades verificadas.",
    ],
  }),
  article({
    id: "demo-cultura-001",
    slug: "ruta-lectura-aire-libre",
    title: "Bibliotecas de barrio abren una ruta de lectura al aire libre",
    summary:
      "La programación conecta plazas, parques y patios escolares con clubes de lectura breves para todas las edades.",
    category: "cultura",
    author: "Sofía Quintana",
    publishedAt: "2026-10-04T09:10:00-06:00",
    readingMinutes: 4,
    imageAlt: "Libros sobre una mesa en un espacio público con árboles.",
    body: [
      "Cinco bibliotecas demo lanzaron una ruta de lectura al aire libre que recorrerá plazas y parques durante octubre. La programación busca acercar libros a personas que no visitan salas tradicionales.",
      "Cada punto tendrá lecturas breves, intercambio de libros y recomendaciones por edad. Los clubes no exigirán inscripción previa para facilitar la participación espontánea.",
      "La selección incluye cuentos cortos, crónica urbana y poesía accesible. Mediadores de lectura acompañarán las conversaciones sin convertirlas en clases formales.",
      "La ruta terminará con una tarde de micrófono abierto para compartir textos propios. Las bibliotecas recopilarán sugerencias para mantener algunas paradas de forma permanente.",
    ],
  }),
  article({
    id: "demo-cultura-002",
    slug: "muralistas-pintan-historia-mercado",
    title: "Muralistas pintan la historia de un mercado en paredes recuperadas",
    summary:
      "El proyecto reúne bocetos de comerciantes veteranos y jóvenes artistas para narrar oficios, recetas y memoria local.",
    category: "cultura",
    author: "Diego Salvatierra",
    publishedAt: "2026-10-03T16:25:00-06:00",
    readingMinutes: 3,
    imageAlt: "Artistas pintando un mural colorido cerca de un mercado.",
    body: [
      "Un grupo de muralistas demo comenzó a intervenir paredes recuperadas alrededor de un mercado tradicional. Los diseños surgieron de conversaciones con comerciantes que llevan décadas en el lugar.",
      "Los bocetos incluyen escenas de carga temprana, recetas familiares y herramientas de oficios que han cambiado con el tiempo. Jóvenes artistas reinterpretaron esos relatos con una paleta común.",
      "El proyecto evita rostros identificables sin autorización y prioriza símbolos compartidos. Cada mural tendrá una placa breve con contexto y créditos de creación colectiva.",
      "La inauguración se realizará con recorridos guiados por los propios comerciantes. La organización espera que la intervención mejore el entorno sin desplazar la actividad diaria.",
    ],
  }),
  article({
    id: "demo-cultura-003",
    slug: "teatro-busca-publico-plazas",
    title: "Compañías de teatro llevan escenas cortas a plazas concurridas",
    summary:
      "Las funciones de quince minutos exploran convivencia urbana y buscan nuevos públicos fuera de las salas tradicionales.",
    category: "cultura",
    author: "Paula Méndez",
    publishedAt: "2026-10-02T19:15:00-06:00",
    readingMinutes: 3,
    imageAlt: "Actores interpretando una escena breve en una plaza pública.",
    body: [
      "Tres compañías demo estrenaron una serie de escenas cortas en plazas con alto tránsito peatonal. Cada función dura quince minutos y se repite en distintos horarios.",
      "Las historias abordan convivencia urbana, ruido, cuidado de espacios comunes y encuentros entre desconocidos. El formato permite que las personas se acerquen sin planificar una salida completa.",
      "Los elencos trabajan con escenografía mínima y sonido moderado para no saturar el entorno. Después de cada función se abre una conversación breve con quienes quieran quedarse.",
      "La iniciativa medirá asistencia aproximada y comentarios del público. Si funciona, las compañías prepararán una segunda temporada en estaciones de transporte y patios escolares.",
    ],
  }),
  article({
    id: "demo-cultura-004",
    slug: "archivo-fotografico-familias",
    title: "Un archivo fotográfico invita a familias a digitalizar recuerdos barriales",
    summary:
      "La convocatoria recopila imágenes domésticas con autorización para construir una memoria visual de calles y celebraciones.",
    category: "cultura",
    author: "Julia Castañeda",
    publishedAt: "2026-10-01T14:05:00-06:00",
    readingMinutes: 4,
    imageAlt: "Fotografías antiguas extendidas sobre una mesa de archivo.",
    body: [
      "Un archivo cultural demo abrió jornadas para digitalizar fotografías familiares relacionadas con la vida barrial. La convocatoria busca escenas de calles, fiestas, comercios y espacios ya transformados.",
      "Las familias conservan sus originales y deciden si autorizan consulta pública, uso educativo o solo preservación privada. El equipo registra contexto básico sin publicar datos sensibles.",
      "Cada imagen se escanea con resolución suficiente para futuras exposiciones. Voluntarios ayudan a identificar fechas aproximadas y lugares cuando los recuerdos no están completos.",
      "El archivo planea una muestra pequeña al final del proceso. La curaduría priorizará relatos cotidianos para evitar una memoria oficial demasiado estrecha.",
    ],
  }),
  article({
    id: "demo-deportes-001",
    slug: "liga-comunitaria-canchas",
    title: "Una liga comunitaria recupera las canchas del vecindario",
    summary:
      "Equipos mixtos organizan jornadas de limpieza, horarios compartidos y partidos breves para devolver actividad a espacios descuidados.",
    category: "deportes",
    author: "Andrés Luján",
    publishedAt: "2026-10-04T07:45:00-06:00",
    readingMinutes: 4,
    imageAlt: "Cancha comunitaria renovada con jóvenes preparando un partido.",
    body: [
      "Una liga deportiva demo inició jornadas para recuperar canchas vecinales con pintura, limpieza y acuerdos de uso. La propuesta combina mantenimiento básico con partidos cortos de fin de semana.",
      "Los equipos son mixtos y se organizan por cercanía, no por nivel competitivo. La idea es que más personas vuelvan a usar los espacios sin convertirlos en torneos cerrados.",
      "Cada jornada incluye una hora de cuidado de la cancha antes de jugar. También se establecieron horarios para niñas, niños y grupos de adultos mayores.",
      "La liga registrará asistencia y necesidades de reparación más grandes. Con esos datos solicitará apoyo para iluminación, redes y puntos de hidratación.",
    ],
  }),
  article({
    id: "demo-deportes-002",
    slug: "ciclistas-rutas-seguras-escuelas",
    title: "Ciclistas trazan rutas seguras para llegar a escuelas cercanas",
    summary:
      "Familias y docentes prueban recorridos acompañados que evitan cruces complejos y priorizan calles tranquilas.",
    category: "deportes",
    author: "Fernanda León",
    publishedAt: "2026-10-03T06:35:00-06:00",
    readingMinutes: 3,
    imageAlt: "Grupo de ciclistas familiares circulando por una calle tranquila.",
    body: [
      "Colectivos ciclistas demo diseñaron rutas acompañadas para estudiantes que viven cerca de sus escuelas. El plan busca identificar trayectos tranquilos antes de promover desplazamientos habituales.",
      "Las primeras salidas se realizan con familias, docentes y voluntarios. Se observan cruces difíciles, tramos sin sombra y lugares donde conviene caminar la bicicleta.",
      "La iniciativa no exige que todos cambien de transporte. Su meta inicial es ofrecer una alternativa segura para quienes ya desean pedalear algunos días.",
      "Al final del mes se publicará un mapa con recomendaciones por escuela. También se propondrán mejoras simples de señalización en los puntos más conflictivos.",
    ],
  }),
  article({
    id: "demo-deportes-003",
    slug: "natacion-adaptada-clubes",
    title: "Clubes locales abren horarios de natación adaptada",
    summary:
      "Entrenadores reciben capacitación para acompañar a personas con distintas necesidades de movilidad y aprendizaje.",
    category: "deportes",
    author: "Ricardo Solís",
    publishedAt: "2026-10-02T08:55:00-06:00",
    readingMinutes: 4,
    imageAlt: "Piscina comunitaria con carriles preparados para entrenamiento.",
    body: [
      "Dos clubes deportivos demo abrieron horarios de natación adaptada con cupos reducidos. La iniciativa se desarrolló después de reuniones con familias que pedían opciones recreativas inclusivas.",
      "Entrenadores recibieron capacitación en comunicación, seguridad y ajustes de actividad. Las sesiones priorizan confianza en el agua antes que rendimiento.",
      "Cada participante cuenta con una evaluación inicial para definir apoyos necesarios. Las familias pueden acompañar el proceso desde una zona cercana sin interferir con la clase.",
      "Los clubes revisarán avances cada seis semanas. Si la demanda crece, buscarán ampliar instructores y coordinar transporte comunitario para quienes viven lejos.",
    ],
  }),
  article({
    id: "demo-deportes-004",
    slug: "corredores-parque-nocturno",
    title: "Corredores organizan entrenamientos nocturnos con rutas iluminadas",
    summary:
      "La actividad reúne grupos de distintos niveles y promueve recorridos visibles, hidratación y registro voluntario de asistencia.",
    category: "deportes",
    author: "Marta Beltrán",
    publishedAt: "2026-10-01T21:10:00-06:00",
    readingMinutes: 3,
    imageAlt: "Personas corriendo de noche en un parque con iluminación pública.",
    body: [
      "Un grupo de corredores demo comenzó entrenamientos nocturnos en rutas iluminadas de un parque urbano. La actividad responde a personas que no pueden ejercitarse durante el día.",
      "Los recorridos se dividen por ritmo y distancia para evitar que principiantes queden rezagados. Cada salida incluye calentamiento, punto de agua y cierre grupal.",
      "La organización recomienda ropa visible y evita tramos aislados. El registro de asistencia es voluntario y se usa solo para estimar cuántos guías hacen falta.",
      "Después de cuatro semanas se evaluará si conviene sumar rutas alternas. El grupo también quiere coordinar charlas sobre prevención de lesiones y descanso.",
    ],
  }),
];

export function getCategoryLabel(category: CategoryId): string {
  const labels: Record<CategoryId, string> = {
    actualidad: "Actualidad",
    tecnologia: "Tecnología",
    economia: "Economía",
    cultura: "Cultura",
    deportes: "Deportes",
  };
  return labels[category];
}
