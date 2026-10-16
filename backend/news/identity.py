"""Identidad del administrador local compartida por publicación y chat."""

import hashlib

from bson import ObjectId


def admin_external_id(username: str) -> str:
    return f"local-admin:{username}"


def admin_author_id(username: str) -> ObjectId:
    # Conserva exactamente los ObjectId que ya utilizaba news.api.
    digest = hashlib.sha1(f"news-admin:{username}".encode()).hexdigest()
    return ObjectId(digest[:24])
