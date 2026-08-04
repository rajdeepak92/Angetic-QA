"""Classified application errors with sanitized public messages."""

from __future__ import annotations

from typing import ClassVar

from multi_agentic_graph_rag.domain.enums import ErrorCategory


class ApplicationError(Exception):
    """Base error whose text is safe to expose at an application boundary."""

    category: ClassVar[ErrorCategory]

    def __init__(self, safe_message: str) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message


class DomainValidationError(ApplicationError):
    """Input or domain state failed validation."""

    category = ErrorCategory.VALIDATION


class ConflictError(ApplicationError):
    """A requested change conflicts with existing state."""

    category = ErrorCategory.CONFLICT


class NotFoundError(ApplicationError):
    """A project-scoped record does not exist."""

    category = ErrorCategory.NOT_FOUND


class ProviderTransientError(ApplicationError):
    """A selected provider failed in a retryable way."""

    category = ErrorCategory.TRANSIENT_PROVIDER


class StoreTransientError(ApplicationError):
    """A selected store failed in a retryable way."""

    category = ErrorCategory.TRANSIENT_STORE


class ProviderPermanentError(ApplicationError):
    """A selected provider failed without a safe retry path."""

    category = ErrorCategory.PERMANENT_PROVIDER


class StorePermanentError(ApplicationError):
    """A selected store failed without a safe retry path."""

    category = ErrorCategory.PERMANENT_STORE


class DataIntegrityError(ApplicationError):
    """Persisted data or migration history violated an invariant."""

    category = ErrorCategory.INTEGRITY


class CancellationError(ApplicationError):
    """An operation was explicitly cancelled."""

    category = ErrorCategory.CANCELLATION
