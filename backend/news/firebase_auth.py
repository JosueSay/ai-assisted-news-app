"""Verificación de Firebase ID tokens para los servicios de noticias."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import time


class FirebaseAuthenticationError(RuntimeError):
    """Credencial Firebase ausente o inválida (HTTP 401)."""


class FirebaseConfigurationError(RuntimeError):
    """No se puede verificar Firebase por configuración/infraestructura (HTTP 503)."""


@dataclass(frozen=True)
class FirebaseIdentity:
    uid: str
    email: str = ""
    display_name: str = ""
    photo_url: str = ""


def _verify_with_google_auth(token: str, project_id: str) -> dict:
    """Verifica firma y claims estándar con los certificados públicos de Firebase.

    La comprobación de firma/audience no requiere una cuenta de servicio ni ADC.
    """
    try:
        from google.auth import exceptions
        from google.auth.transport.requests import Request
        from google.oauth2.id_token import verify_firebase_token
    except ImportError as error:
        raise FirebaseConfigurationError(
            "Falta instalar google-auth en el backend."
        ) from error

    try:
        transport = Request()

        def request_certificates(url, method="GET", body=None, headers=None, **kwargs):
            return transport(
                url,
                method=method,
                body=body,
                headers=headers,
                timeout=5,
                **kwargs,
            )

        return verify_firebase_token(token, request_certificates, audience=project_id)
    except exceptions.TransportError as error:
        raise FirebaseConfigurationError(
            "No fue posible consultar los certificados públicos de Firebase."
        ) from error
    except Exception as error:
        raise FirebaseAuthenticationError("Firebase ID token inválido o vencido.") from error


def verify_firebase_bearer(
    authorization: str | None,
    project_id: str,
    *,
    verifier: Callable[[str, str], dict] | None = None,
) -> FirebaseIdentity:
    """Valida un Bearer token Firebase y devuelve solo claims de identidad.

    Se verifica firma, audiencia, issuer y expiración. El rol nunca se obtiene de
    claims aportados por el cliente: se resuelve desde el usuario MongoDB.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise FirebaseAuthenticationError("Se requiere autenticación Firebase.")
    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise FirebaseAuthenticationError("Se requiere autenticación Firebase.")
    normalized_project_id = project_id.strip()
    if not normalized_project_id:
        raise FirebaseConfigurationError("NEWS_FIREBASE_PROJECT_ID no está configurado.")

    verify = verifier or _verify_with_google_auth
    try:
        claims = verify(token, normalized_project_id)
    except (FirebaseAuthenticationError, FirebaseConfigurationError):
        raise
    except Exception as error:
        # No propagar detalles del proveedor ni contenido del token a clientes/logs.
        raise FirebaseAuthenticationError("Firebase ID token inválido.") from error

    expected_issuer = f"https://securetoken.google.com/{normalized_project_id}"
    if claims.get("iss") != expected_issuer or claims.get("aud") != normalized_project_id:
        raise FirebaseAuthenticationError("Firebase ID token emitido para otro proyecto.")
    uid = str(claims.get("sub") or "").strip()
    if not uid or len(uid) > 128:
        raise FirebaseAuthenticationError("Firebase ID token sin UID válido.")
    try:
        auth_time = int(claims["auth_time"])
    except (KeyError, TypeError, ValueError) as error:
        raise FirebaseAuthenticationError("Firebase ID token sin auth_time válido.") from error
    if auth_time <= 0 or auth_time > int(time()) + 60:
        raise FirebaseAuthenticationError("Firebase ID token con auth_time inválido.")
    return FirebaseIdentity(
        uid=uid,
        email=str(claims.get("email") or "").strip(),
        display_name=str(claims.get("name") or "").strip(),
        photo_url=str(claims.get("picture") or "").strip(),
    )
