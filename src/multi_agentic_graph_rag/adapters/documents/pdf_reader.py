"""PyMuPDF PDF extraction adapter."""

from __future__ import annotations

from io import BytesIO

import pymupdf as fitz

from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock


class PdfReader:
    """Extract non-empty PDF text blocks in page and layout order."""

    def read(self, content: bytes) -> tuple[DocumentBlock, ...]:
        """Extract blocks from PDF bytes."""
        blocks: list[DocumentBlock] = []
        with fitz.open(  # type: ignore[no-untyped-call]
            stream=BytesIO(content), filetype="pdf"
        ) as document:
            for page_number, page in enumerate(document, start=1):
                for raw_block in page.get_text("blocks", sort=True):
                    text = raw_block[4].strip()
                    if text:
                        blocks.append(
                            DocumentBlock(
                                block_index=len(blocks), text=text, page_number=page_number
                            )
                        )
        return tuple(blocks)
