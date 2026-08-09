"""Deterministic document parsing and normalization."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock
from multi_agentic_graph_rag.ports.documents import DocumentReaderPort

_WHITESPACE = re.compile(r"[ \t]+")


def parse_document(
    content: bytes, *, extension: Literal[".pdf", ".docx"], reader: DocumentReaderPort
) -> tuple[DocumentBlock, ...]:
    """Extract and normalize one supported document through an injected reader."""
    if not content:
        raise ValueError("Document content must not be empty.")
    del extension
    blocks: list[DocumentBlock] = []
    for block in reader.read(content):
        text = normalize_text(block.text)
        if text:
            blocks.append(block.model_copy(update={"text": text}))
    return tuple(blocks)


def normalize_text(text: str) -> str:
    """Normalize Unicode and line whitespace without changing word order."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(_WHITESPACE.sub(" ", line).strip() for line in text.split("\n")).strip()
