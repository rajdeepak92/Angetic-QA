"""Deterministic identity and checksum tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from multi_agentic_graph_rag.domain.identifiers import (
    canonical_json_bytes,
    checksum_json,
    deterministic_uuid7,
    new_uuid7,
)


def test_deterministic_uuid7_has_stable_known_value() -> None:
    """Canonical content and an injected timestamp produce one stable UUIDv7."""
    timestamp = datetime(2026, 1, 2, 3, 4, 5, 678000, tzinfo=UTC)
    identifier = deterministic_uuid7(
        timestamp=timestamp,
        namespace="run",
        value={"b": "e\u0301", "a": 1},
    )

    assert str(identifier) == "019b7ca9-8f2e-7973-addd-d2d6d32828d9"
    assert identifier.version == 7


def test_canonical_json_normalizes_unicode_and_key_order() -> None:
    """Equivalent JSON values have identical bytes and SHA-256 checksums."""
    first = {"z": [True, None], "name": "e\u0301"}
    second = {"name": "é", "z": [True, None]}

    assert canonical_json_bytes(first) == b'{"name":"\xc3\xa9","z":[true,null]}'
    assert checksum_json(first) == checksum_json(second)

    with pytest.raises(ValueError, match="non-finite"):
        checksum_json({"invalid": float("nan")})


def test_new_identifier_is_uuid7() -> None:
    """Fresh persisted identities use the authorized UUIDv7 implementation."""
    assert new_uuid7().version == 7
