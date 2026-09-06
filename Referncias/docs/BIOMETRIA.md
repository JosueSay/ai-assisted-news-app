# Diseño de la fase biométrica

## Alcance actual

- En tablet compartida (`kiosk`), código + PIN identifican al colaborador.
- En teléfono personal (`personal`), `expo-local-authentication` agrega una confirmación local mediante huella o rostro fuerte.
- El servidor registra `pin`, porque una confirmación local no es una prueba biométrica verificable remotamente.
- GPT/OpenAI no interviene en identidad, puntualidad ni almacenamiento de imágenes.

## Por qué la huella integrada no identifica empleados

Android BiometricPrompt solo devuelve éxito o fracaso para el perfil del dispositivo. No entrega la huella, plantilla ni identidad enrolada. En una tablet con huellas de varias personas, la aplicación no puede distinguir cuál fue utilizada.

Opciones válidas:

1. Un teléfono vinculado a una sola persona, con sesión individual y biometría local.
2. Un lector de huella USB/Bluetooth que tenga SDK Android para identificación multiusuario.
3. Verificación facial propia con enrolamiento, plantilla y prueba de vida.

## Flujo facial recomendado para la tablet

Debe ser verificación 1:1, no vigilancia ni búsqueda automática continua:

1. El empleado declara su identidad con código, QR o NFC.
2. La cámara exige una sola cara, iluminación suficiente y posición correcta.
3. Una prueba de vida/PAD rechaza fotografías, pantallas y videos.
4. El módulo alinea el rostro y genera un embedding.
5. Compara únicamente contra la plantilla del empleado declarado.
6. Si supera el umbral calibrado, entrega un token firmado, de un solo uso y vida corta.
7. La Edge Function consume ese token y PostgreSQL registra la hora del servidor.

Una implementación nativa posible es VisionCamera + módulo Kotlin/C++ + OpenCV YuNet/SFace. ML Kit puede detectar una cara, pero no identificar a la persona. OpenCV por sí solo tampoco aporta una prueba de vida robusta.

## Datos mínimos que habría que agregar

- Dispositivos kiosco provisionados y revocables.
- Consentimiento biométrico, fecha, finalidad y versión del algoritmo.
- Plantillas cifradas en un esquema/bucket privado; nunca en tablas públicas.
- Verificaciones de un solo uso con empleado, dispositivo, acción, expiración y resultado.
- Auditoría de enrolamiento, reemplazo y eliminación.

No se deben conservar fotografías ordinarias de cada marcaje. Los frames se procesan en memoria y se descartan. Una baja laboral o retiro del consentimiento debe eliminar la plantilla.

## Criterios antes de producción

- Probar falsos positivos y falsos negativos en la tablet y condiciones reales de luz/altura.
- Evaluar PAD/liveness contra foto impresa, pantalla, video y máscara.
- Tener alternativa de PIN/QR y revisión administrativa; un fallo facial no crea automáticamente una falta.
- Definir quién puede enrolar y reemplazar una plantilla.
- Obtener revisión legal local para el tratamiento de datos biométricos.
- Para nómina o alto riesgo de fraude, preferir un SDK/PAD evaluado comercialmente.

Referencias: [Android biometrics](https://source.android.com/docs/security/features/biometric), [Expo LocalAuthentication](https://docs.expo.dev/versions/latest/sdk/local-authentication/), [OpenCV SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) y [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html).

