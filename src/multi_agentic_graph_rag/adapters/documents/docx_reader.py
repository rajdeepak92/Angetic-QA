"""python-docx DOCX extraction adapter."""

from __future__ import annotations

from io import BytesIO

from docx import Document

from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock


class DocxReader:
    """Extract non-empty paragraphs while retaining paragraph order."""

    def read(self, content: bytes) -> tuple[DocumentBlock, ...]:
        """Extract paragraphs from DOCX bytes."""
        blocks: list[DocumentBlock] = []
        for paragraph_index, paragraph in enumerate(Document(BytesIO(content)).paragraphs):
            text = paragraph.text.strip()
            if text:
                blocks.append(
                    DocumentBlock(
                        block_index=len(blocks), text=text, paragraph_index=paragraph_index
                    )
                )
        return tuple(blocks)
