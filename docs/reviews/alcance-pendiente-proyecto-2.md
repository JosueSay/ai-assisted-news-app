# Alcance pendiente del Proyecto 2 — tareas por completar

Actualizado: 2026-10-20. Referencia de código revisada: `ee9cc00`.

Este documento reúne los **ocho puntos seleccionados por el usuario** y las tareas
concretas para completarlos. Los puntos 2–4 se implementaron en el Loop 11; queda
pendiente una revisión visual manual en dispositivos/navegadores reales señalada en el punto 4.

La guía que antes ocupaba este archivo se conserva completa en
[Firebase: configuración y verificación](firebase-auth-configuracion.md). Firebase
ya tiene implementación en el código actual; su pendiente es configurar y comprobar
la integración real, no volver a implementar el login local anterior.

Los puntos restantes describen trabajo futuro. El Loop 11 implementó los puntos 2–4
sin cambiar la estructura de datos ni credenciales; las reglas aprobadas quedaron
registradas en [criterios de personalización](../design/database/03-criterios-de-personalizacion.md).

## Resumen del trabajo pendiente

| Punto | Estado actual | Qué hay que completar |
| --- | --- | --- |
| 1. Firebase Authentication | Integrado en código; falta comprobación real. | Configuración Firebase/Google, autorización admin y verificación de los accesos reales. |
| 2. Feed personalizado | Implementado en Loop 11; falta validación manual con cuentas reales. | Perfil compartido, ubicación/temas por cuenta, ranking servidor e integración frontend. |
| 3. Aprendizaje de intereses | Implementado en Loop 11; señales y fórmula cubiertas por pruebas controladas. | Medición de aperturas/lecturas, inferencia gradual e impacto posterior en el feed. |
| 4. Prominencia y diversidad | Implementado en Loop 11; queda revisión visual manual web/móvil. | Composición determinista, destacados según ranking y exposición a otros ámbitos. |
| 5. Imagen desde administración | URL manual o placeholder. | Obtención o generación dentro del formulario, previsualización y selección humana. |
| 6. Identificación de imágenes IA | Campos/validaciones existentes; portal fuerza fotografía. | Tipo y disclosure desde administración hasta tarjetas y detalle. |
| 7. Verificación editorial | Estado elegible; fuentes opcionales y revisión automática. | Política de revisión, fuentes suficientes y comunicación efectiva de incertidumbre. |
| 8. Chat como pantalla inicial | Entrada normal al feed. | Chat en móvil, feed para invitado web y panel para administrador web. |

## 1. Firebase Authentication

### Lo que se tiene actualmente

- [googleAuth.ts](../../frontend/src/services/googleAuth.ts) utiliza Firebase para
  Google y para invitados mediante Anonymous Authentication.
- [firebaseClient.ts](../../frontend/src/services/firebaseClient.ts) inicializa la
  sesión. La API resuelve el usuario en `GET /auth/me` a partir del token verificado.
- [firebase_auth.py](../../backend/news/firebase_auth.py) verifica ID tokens y el
  Project ID. La publicación requiere rol `admin` obtenido de MongoDB.
- El chat news usa el mismo UID verificado. El cliente ya no declara su identidad
  en el cuerpo como antes. Los perfiles provisionales existentes se mantienen separados.
- El [handoff de Firebase](../../backend/loops/handoffs/firebase-auth-preparation-result.md)
  documenta pruebas con verificadores simulados y deja pendiente el login real.

### Lo que falta y tareas que hay que realizar

- [ ] Configurar el proyecto Firebase y habilitar Google y Anonymous siguiendo la
  [guía conservada](firebase-auth-configuracion.md).
- [ ] Registrar/configurar las aplicaciones web, Android e iOS, sus dominios y las
  huellas de las firmas Android que realmente se utilicen.
- [ ] Completar la configuración pública local y comprobar que frontend, API y
  chatbot apuntan al mismo Project ID, sin compartir tokens ni secretos.
- [ ] Reconstruir los servicios/builds que consumen esa configuración y verificar
  login Google, acceso invitado, restauración y cierre de sesión.
- [ ] Iniciar sesión con la cuenta administradora, verificar su UID y asignar el
  rol mediante una operación humana autorizada. No promover cuentas por email o nombre.
- [ ] Comprobar que una cuenta normal no publica y que un token inválido, vencido
  o de otro proyecto no accede a rutas protegidas.
- [ ] Verificar que dos cuentas no comparten preferencias ni sesiones de chat.

### Alcance

Completar la integración existente en móvil, web, API y chat. La lectura pública
permanece disponible y el invitado usa su identidad Firebase anónima. Se conserva
`users.role` como origen de permisos y `users.firebaseUid` como UID externo único.
No se fusionan cuentas antiguas ni se modifica el esquema para cerrar este punto.

### Cómo abordarlo

Primero resolver configuración y correspondencia del proyecto; después probar una
cuenta común de extremo a extremo y finalmente la cuenta administradora. Ante un
fallo, localizar si es de configuración, intercambio de credencial, verificación
backend o autorización; no rehacer el acceso entero sin esa evidencia.

### Resultado esperado para considerarlo terminado

Una cuenta real de Google puede entrar en iPhone, Android y web y llega al mismo
usuario verificado. El invitado recibe una identidad aislada. Solo la cuenta con
rol administrativo puede publicar; salir, volver a entrar y renovar la sesión
funciona. Las pruebas reales pendientes quedan registradas con su resultado.

## 2. Feed personalizado

### Lo que se tiene actualmente

- [La API `/news`](../../backend/news/api.py) puntúa todas las publicaciones, aplica
  el perfil Firebase verificado cuando se envía y compone hasta 50 resultados.
- [newsService.ts](../../frontend/src/services/newsService.ts) conserva el orden del
  servidor; la portada usa las tres primeras posiciones como principal/secundarias.
- Ubicación y temas se guardan en el perfil Mongo autenticado y se comparten con el
  selector del chat; el invitado usa su UID anónimo, aislado por Firebase.

### Lo que falta y tareas que hay que realizar

- [x] Compartir la ubicación del usuario entre chat y feed, guardándola por identidad
  y evitando mezclar preferencias de cuentas distintas en el mismo dispositivo.
- [x] Incorporar selección inicial y cambio de ubicación manual, sin GPS, y selección
  de temas usando `onboarding.selectedTopics`.
- [x] Definir una regla explicable de ranking con ubicación, temas, intereses
  inferidos y actualidad. Documentar pesos/desempates antes de fijarlos en código.
- [x] Recuperar candidatos pertinentes antes de recortar resultados; no limitar la
  personalización a las 50 publicaciones globales más recientes si eso excluye las locales.
- [x] Resolver el perfil desde la identidad verificada del backend, incluyendo el
  caso invitado anónimo, y devolver el resultado personalizado al frontend.
- [x] Evitar que el cliente reordene por fecha un ranking ya calculado por el servidor.
- [x] Actualizar el feed al cambiar ubicación/preferencias y definir qué mostrar
  para una cuenta nueva o sin coincidencias.
- [x] Añadir pruebas con dos perfiles y dos ubicaciones sobre las mismas noticias.

### Alcance

Selección y orden personalizados de noticias `published`, con ubicación manual
coherente con el chat y preferencias declaradas para el inicio sin historial.
Se emplea el catálogo real disponible, inicialmente de países. El algoritmo se
ejecuta por código; no se añade un campo de importancia editable por el autor ni
se requiere un LLM para ordenar.

### Cómo abordarlo

Loop 11: habilitar perfil/catálogo manual, puntuar candidatos completos en backend,
preservar ese orden en frontend y refrescarlo al cambiar preferencias. La lectura
actualiza señales con eventos deduplicados y el feed reserva posiciones diversas.

### Resultado esperado para considerarlo terminado

Dos personas con ubicación o intereses distintos reciben diferencias justificables
en selección u orden. Cambiar de país modifica el feed y las consultas regionales
del chat de manera coherente. Una cuenta sin historial obtiene una experiencia
útil, sin noticias inventadas, y las publicaciones generales importantes siguen accesibles.

## 3. Aprendizaje de intereses

### Lo que se tiene actualmente

- `POST /news/{slug}/interactions/{opened|read}` persiste señales verificadas y conserva
  contexto de ubicación/posición; la pantalla mide visibilidad de contenido y tiempo activo.
- La regla aprobada actualiza `inferredInterests` en rango 0–1 y alimenta el ranking;
  está documentada en [criterios de personalización](../design/database/03-criterios-de-personalizacion.md).

### Lo que falta y tareas que hay que realizar

- [x] Registrar `opened` al entrar a una noticia, con identidad, noticia, ubicación
  y posición que correspondían a esa apertura.
- [x] Medir progreso y tiempo activo, pausándolo al salir de la noticia o mandar
  la app a segundo plano.
- [x] Registrar `read` al alcanzar el 90 %; si el cuerpo cabe completo en el viewport,
  exigir 5 segundos activos con 90 % visible.
- [x] Definir y aplicar control de reintentos, renders y relecturas para no multiplicar
  señales o puntajes por errores de envío.
- [x] Definir una regla determinista que convierta apertura, lectura y tiempo en
  cambios de `inferredInterests`, preservando puntuaciones entre 0 y 1.
- [x] Actualizar `updatedAt` y mantener separados los temas elegidos por la persona
  de los temas inferidos por comportamiento.
- [x] Usar los intereses calculados en el ranking del feed.
- [x] Probar aperturas breves, lecturas sostenidas, pausas, reintentos y
  aislamiento entre usuarios con datos y reloj controlados.

### Alcance

Aprendizaje a partir de las interacciones aprobadas de apertura y lectura.
Los favoritos no se convierten en otro tipo de interacción sin decisión de diseño.
No se requiere un servicio de ML: una regla pequeña y comprobable satisface el
objetivo si el comportamiento realmente modifica la personalización.

### Cómo abordarlo

Loop 11: instrumentar el detalle, pausar el tiempo con la app en segundo plano,
registrar lectura al 90 %, deduplicar por usuario/noticia/tipo con el índice vigente,
y aplicar la regla incremental documentada sin alterar campos ni índices.

### Resultado esperado para considerarlo terminado

Lecturas sostenidas de tecnología aumentan gradualmente ese interés y alteran el
feed posterior según la regla acordada. Una apertura breve no equivale a una
lectura completa, los reintentos no inflan el aprendizaje y las cuentas permanecen aisladas.

## 4. Prominencia y diversidad

### Lo que se tiene actualmente

- [ArticleCard](../../frontend/src/components/ArticleCard.tsx) conserva variantes
  destacada, secundaria, estándar y compacta, y muestra la razón recibida de la API.
- La portada alinea principal, secundarias y noticias siguientes con la composición
  determinista enviada por el backend.
- La política reserva las posiciones 4 y 9 (cuando hay oferta) para noticias
  internacionales o de otra ubicación, y rellena escasez por ranking.

Correcciones posteriores al Loop 11: las reservas eligen las noticias diversas más
recientes, independientemente de la afinidad temática. El feed se consulta de nuevo
al salir del detalle, después del envío del tiempo activo; también incorpora lecturas
que terminan de guardarse tras volver al listado. Ver el
[handoff de correcciones](../../backend/loops/handoffs/12-feed-recency-refresh-result.md).

### Lo que falta y tareas que hay que realizar

- [x] Definir cómo se seleccionan principal, secundarias y secciones a partir de
  la relevancia del punto 2.
- [x] Acordar una política de exposición a información importante local, nacional
  e internacional aunque no coincida con los intereses aprendidos.
- [x] Definir posiciones/segmentos reservados y qué ocurre si no hay contenido
  suficiente de un ámbito; no inventar noticias para llenar espacios.
- [x] Conectar selección y composición del backend con las variantes visuales del
  frontend para que no destaquen artículos distintos por órdenes incompatibles.
- [x] Definir razones comprensibles para el lector cuando se explique una selección,
  como «por tu ubicación», sin atribuirle razones que la regla no usó.
- [x] Probar perfiles concentrados en un tema, empates y escasez de contenido diverso.
- [ ] Revisar visualmente la jerarquía y los avisos de selección en tarjetas móviles y web.

### Alcance

Relacionar prominencia visual con relevancia y preservar exposición a otros ámbitos.
La política usa los campos aprobados; no añade `importance` ni prioridad manual
del autor. El catálogo/dataset canónico actual cubre países: ampliar cobertura
real de ciudades, regiones o fixtures internacionales requiere un cambio explícito,
no asumir que esos datos ya existen por estar permitidos en el modelo.

### Cómo abordarlo

Política aprobada e implementada en Loop 11: ranking compuesto y posiciones diversas
4/9 antes de presentar el resultado en las tarjetas. Queda la revisión visual manual
de la interfaz en viewport móvil y web.

### Resultado esperado para considerarlo terminado

Una noticia pertinente puede aparecer más arriba y con mayor prominencia para una
persona que para otra, y se puede explicar por qué. La concentración en un interés
no elimina las publicaciones de otros ámbitos previstas por la política; la falta
de oferta se resuelve sin espacios engañosos ni contenido inventado.

## 5. Imagen desde administración

### Lo que se tiene actualmente

- El formulario administrativo permite pegar URL y escribir alt, crédito y derechos.
- Sin imagen, la API guarda tipo `none` y
  [ArticleImage](../../frontend/src/components/ArticleImage.tsx) muestra un placeholder.
- No hay una acción integrada que obtenga o genere una imagen para la noticia.

### Lo que falta y tareas que hay que realizar

- [ ] Elegir una vía inicial para obtener una imagen: selección de una biblioteca
  autorizada, búsqueda con derechos adecuados o generación. El PDF no obliga a implementar todas.
- [ ] Definir procedencia, derechos y cómo conservar una URL utilizable de la imagen
  sin asumir que ya existe infraestructura de almacenamiento.
- [ ] Añadir una acción «Obtener imagen» o equivalente dentro de la noticia en edición.
- [ ] Mostrar estados de carga, candidatos/resultado, previsualización, selección
  y cancelación sin perder el texto del formulario.
- [ ] Adjuntar la imagen aceptada y sus metadatos a los campos existentes de `news.image`.
- [ ] Exigir revisión humana de pertinencia y representación: una ilustración no
  debe presentarse como documentación real del acontecimiento.
- [ ] Integrar el etiquetado del punto 6 y permitir continuar como borrador si la
  obtención falla o no hay una imagen adecuada.
- [ ] Probar éxito, falta de resultados, cancelación y fallo con proveedores/datos controlados.

### Alcance

Resolver una noticia sin imagen dentro del flujo administrativo, incluyendo revisión
y adjunto. Una obtención sin IA puede cumplir el requisito; no se selecciona un
proveedor externo ni se añade almacenamiento o credenciales por este documento.
Si se elige generación real, debe respetar el registro de uso y auditoría ya
definido para esa acción, sin añadir otro frente al alcance seleccionado.

### Cómo abordarlo

Elegir una sola vía mínima viable y verificar sus derechos/condiciones antes de
integrarla. Conectar formulario → obtención → previsualización → aceptación → noticia.
Preparar el contrato de tipo/disclosure del punto 6 antes de permitir resultados IA.
Las nuevas dependencias o credenciales se deciden en el loop de implementación y
se sincronizan con configuración, bootstrap y documentación cuando correspondan.

### Resultado esperado para considerarlo terminado

Una persona que está creando una noticia sin imagen puede conseguir una desde el
mismo formulario, revisarla y publicarla con descripción, crédito, derechos y tipo
correctos. Cancelar o fallar conserva su trabajo y ninguna imagen engañosa se adjunta automáticamente.

## 6. Identificación de imágenes IA

### Lo que se tiene actualmente

- [Image](../../backend/news/models/news.py) admite fotografía, ilustración, generada
  con IA, alterada con IA y ausencia de imagen. Los tipos IA exigen `aiDisclosure`.
- El contrato de lectura transporta esos campos y el detalle muestra disclosure cuando existe.
- El formulario no expone tipo/disclosure; la API administrativa sigue clasificando
  cualquier URL como fotografía. Las tarjetas no presentan un aviso de IA.

### Lo que falta y tareas que hay que realizar

- [ ] Añadir al formulario el tipo de imagen y la declaración que debe acompañarla.
- [ ] Incorporar esos datos al request administrativo y conservarlos al crear la noticia.
- [ ] Reutilizar validaciones canónicas: rechazar tipos IA sin disclosure en backend,
  además de informar el problema en la interfaz.
- [ ] Mantener coherentes `image.type`, `image.aiDisclosure` y `aiAssistance.imageGenerated`
  según el modelo vigente; este último corresponde específicamente a `ai_generated`.
- [ ] Mostrar un aviso visible y accesible para imágenes generadas o alteradas en
  tarjetas compactas, destacadas y detalle, junto con crédito/derechos pertinentes.
- [ ] Hacer que la obtención del punto 5 conserve el origen conocido, sin deducirlo
  únicamente de la URL o la apariencia.
- [ ] Probar guardado/lectura de los cinco tipos, metadatos incompletos y avisos visibles.
- [ ] Definir el tratamiento de imágenes antiguas sin procedencia; no reclasificarlas
  automáticamente como reales o IA sin evidencia.

### Alcance

Declaración y presentación de la naturaleza visual para imágenes manuales y obtenidas.
Se conservan los tipos y reglas existentes, incluido URL/alt nulos para `none`.
No se construye un detector automático que prometa determinar el origen de cualquier imagen.

### Cómo abordarlo

Primero completar contrato/formulario y validaciones; después usar una presentación
consistente en las superficies del frontend. Verificar el recorrido administrativo
hasta lectura de la noticia con DB temporal y casos visuales controlados. La
obtención de imágenes debe consumir este mismo contrato, no inventar otro.

### Resultado esperado para considerarlo terminado

Una imagen generada o alterada no se guarda como fotografía por defecto y el lector
reconoce su naturaleza antes de interpretarla como evidencia, tanto en feed como
en detalle. Guardar y recuperar mantiene tipo, declaración y procedencia.

## 7. Verificación editorial

### Lo que se tiene actualmente

- Existen estados `confirmed`, `developing`, `insufficient_sources` y `conflicting_sources`.
- El modelo permite varias fuentes, su procedencia y la afirmación que respaldan.
- El formulario recoge una fuente opcional, parte de `published`/`confirmed` por
  defecto y la creación marca revisión humana automáticamente.
- El detalle y el chat comunican parte de la verificación/incertidumbre; las tarjetas
  del feed no muestran esos avisos.

### Lo que falta y tareas que hay que realizar

- [ ] Definir una política editorial con ejemplos de los cuatro estados: qué
  respaldo permite confirmar y qué hacer ante ausencia, insuficiencia o contradicción.
- [ ] Permitir registrar varias fuentes y utilizar `supports`/notas para explicar
  qué afirmación está respaldada y qué sigue sin resolverse.
- [ ] Quitar la confirmación implícita como decisión editorial: solicitar revisión
  explícita antes de publicar como confirmada, según la política acordada.
- [ ] Distinguir guardar borrador de publicar y aplicar la política también en servidor,
  evitando que pueda omitirse al enviar el request directamente.
- [ ] Guardar autor/revisor reales y registrar `humanReviewed` solo cuando corresponda
  a una revisión efectuada; declarar aportes IA de resumen/temas/imagen cuando existan.
- [ ] Mostrar estados inciertos, fuentes y declaraciones pertinentes en feed y detalle;
  mantener citas solo de publicaciones y confianza basada en datos en el chat.
- [ ] Probar fuente primaria suficiente, respaldo insuficiente, fuentes contradictorias,
  noticia en desarrollo y contenido asistido por IA.

### Alcance

Proceso humano de comprobación y su reflejo en administración, API, feed, lectura
y chat. Se conservan `draft` y `published` como únicos estados de publicación;
la verificación es una dimensión diferente. El PDF no impone exactamente dos
fuentes: la política del equipo debe justificar cuándo el respaldo es suficiente.
No se convierte una opinión del modelo en prueba de verdad ni se añade un estado
de revisión o un servicio automático de fact-checking sin otra decisión.

### Cómo abordarlo

Acordar primero la política y sus ejemplos; convertirlos en casos de aceptación.
Después ampliar fuentes/notas y revisión explícita en el formulario, aplicar las
reglas en backend y reflejar el resultado en tarjetas/detalle/chat. Usar los campos
aprobados y la identidad Firebase ya integrada. Si la política permite publicar
incertidumbre, exigir comunicación clara en vez de cambiar el estado a confirmada.

### Resultado esperado para considerarlo terminado

Cada publicación tiene un estado justificable y una revisión humana trazable.
La información insuficiente o contradictoria recibe el tratamiento definido y
comunica lo no confirmado. El lector ve el aviso antes de asumir certeza y una
respuesta fluida del chat no eleva automáticamente la confianza de la noticia.

## 8. Chat como pantalla inicial

### Lo que se tiene actualmente

- [App.tsx](../../frontend/src/App.tsx) resuelve el acceso y muestra la experiencia de noticias.
- `getInitialRoute` de
  [NewsFeedScreen](../../frontend/src/features/news/NewsFeedScreen.tsx) inicia en `home`
  en móvil y en web sin hash específico.
- Chat, feed, lectura y creación administrativa ya tienen rutas; abrir el chat desde
  una noticia conserva contexto. Falta cambiar la política de entrada normal.

### Lo que falta y tareas que hay que realizar

- [ ] Resolver la entrada según plataforma real y tipo de usuario una vez que se
  haya restaurado/completado Firebase Authentication.
- [ ] Abrir chat en iPhone/Android, incluido invitado si se mantiene ese acceso.
- [ ] Mantener feed para invitado web y abrir el panel existente para administrador web.
- [ ] Conservar feed para usuario común web como propuesta de continuidad, sin
  tratar un navegador estrecho como aplicación nativa.
- [ ] Definir precedencia de enlaces directos: propuesta de conservar la ruta válida
  y autorizada y usar el inicio por plataforma/rol cuando no exista una ruta explícita.
- [ ] Evitar redirecciones repetidas que devuelvan al chat al navegar, redimensionar
  o recibir una respuesta; resolver la entrada nuevamente al cambiar de cuenta.
- [ ] Revisar que una carga general del feed no bloquee innecesariamente la entrada al chat.
- [ ] Probar iOS, Android, invitado/admin/usuario común web, navegador estrecho,
  enlace a noticia, recarga y cambio de identidad.

### Alcance

Solo inicio posterior al acceso y conservación de la navegación existente. El login
puede aparecer primero. El panel web reutiliza la creación administrativa actual;
no exige construir un dashboard nuevo. La entrada móvil viene del PDF; las reglas
de invitado web y administrador web fueron acordadas con el usuario.

### Cómo abordarlo

Concentrar la política en un punto pequeño del routing con entradas claras de
plataforma, permisos y ruta disponible. Respetar enlaces válidos/autorizados según
la regla acordada. Aplicarlo al completar el acceso y comprobar que feed, chat
contextual, lectura y navegación normal siguen siendo utilizables.

### Resultado esperado para considerarlo terminado

Tras acceder normalmente, el móvil abre chat, el invitado web abre feed y el
administrador web abre su panel. Un enlace directo útil no se pierde y navegar
después no activa bucles o regresos involuntarios al inicio.

## Secuencia de trabajo recomendada

1. Cerrar configuración y comprobación real de Firebase (1), aprovechando la integración existente.
2. Implementar la entrada por plataforma (8); es acotada y no depende del ranking.
3–4. Implementados en Loop 11 por autorización expresa del usuario: unificar
    ubicación/preferencias, personalizar feed, aprender intereses y componer diversidad.
5. Completar revisión editorial (7) y contrato/avisos de imagen (6).
6. Integrar una vía de obtención de imágenes (5) compatible con esa revisión y etiquetado.

Cada implementación debe definir su loop, pruebas pertinentes y handoff. Las
decisiones de política, fórmula de relevancia, origen de imágenes o cambios de DB
se resuelven antes de construir lo que dependa de ellas. La suite normal usa datos
controlados y no depende de credenciales reales.

## Condición de cierre y mantenimiento

Un punto se cierra cuando sus tareas y el resultado esperado se comprueban, no
cuando solo hay modelos o documentación. Registrar comandos, resultados y límites;
actualizar este archivo sin eliminar el alcance de los otros puntos al trabajar uno.

Si cambia DB, sincronizar modelos, validators, índices, seeders, pruebas, Makefile,
README y [diagrama](../design/database/07-diagrama.md) según corresponda. Si cambian
credenciales requeridas, mantener sincronizados configuración, `setup-keys` y
documentación. Los agentes no leen contenidos de `keys/`.
