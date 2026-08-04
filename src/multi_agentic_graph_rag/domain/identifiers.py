"""Deterministic UUIDv7 and SHA-256 identity functions."""

from __future__ import annotations

import json
import math
import unicodedata
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated
from uuid import RFC_4122, UUID

from pydantic import AfterValidator, Field
from uuid_utils.compat import uuid7

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


def _validate_uuid7(value: UUID) -> UUID:
    if value.version != 7 or value.variant != RFC_4122:
        raise ValueError("Identifier must be an RFC 4122 UUIDv7.")
    return value


UUID7 = Annotated[UUID, AfterValidator(_validate_uuid7)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def new_uuid7() -> UUID:
    """Create one time-ordered UUIDv7 for persistence and reuse."""
    return uuid7()


def deterministic_uuid7(*, timestamp: datetime, namespace: str, value: JsonValue) -> UUID:
    """Derive a stable UUIDv7 from UTC time, namespace, and canonical JSON."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("UUIDv7 timestamp must be timezone-aware.")
    timestamp_ms = int(timestamp.astimezone(UTC).timestamp() * 1000)
    if not 0 <= timestamp_ms < 1 << 48:
        raise ValueError("UUIDv7 timestamp is outside the 48-bit millisecond range.")
    material = canonical_json_bytes({"namespace": namespace, "value": value})
    value_bits = (timestamp_ms << 80) | int.from_bytes(sha256(material).digest()[:10])
    value_bits = (value_bits & ~(0xF << 76)) | (7 << 76)
    value_bits = (value_bits & ~(0x3 << 62)) | (0x2 << 62)
    return UUID(int=value_bits)


def canonical_json_bytes(value: JsonValue) -> bytes:
    """Encode normalized JSON deterministically as UTF-8 bytes."""
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def checksum_json(value: JsonValue) -> str:
    """Return the lowercase SHA-256 checksum of canonical JSON."""
    return sha256(canonical_json_bytes(value)).hexdigest()


def checksum_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 checksum of exact bytes."""
    return sha256(value).hexdigest()


def _normalize(value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical JSON does not allow non-finite numbers.")
        return value
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ValueError("Canonical JSON keys collide after Unicode normalization.")
            normalized[normalized_key] = _normalize(item)
        return normalized
    return value
