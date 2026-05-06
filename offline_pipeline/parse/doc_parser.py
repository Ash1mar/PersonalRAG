from __future__ import annotations

from pathlib import Path

from libs.common.ids import make_block_id
from libs.common.models import Block, Document, DocumentMeta


def parse_document(file_path: str | None, text: str | None, meta: DocumentMeta) -> Document:
    raw_text = _load_text(file_path=file_path, text=text)
    blocks = _split_into_blocks(raw_text=raw_text, doc_id=meta.doc_id)
    return Document(meta=meta, blocks=blocks, raw_text=raw_text)


def _load_text(file_path: str | None, text: str | None) -> str:
    if text and text.strip():
        return text.strip()
    if not file_path:
        raise ValueError("Either text or file_path is required.")

    path = Path(file_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        raise ValueError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".md", ".txt"}:
        raise ValueError("Current MVP only supports .md and .txt files.")
    return path.read_text(encoding="utf-8").strip()


def _split_into_blocks(raw_text: str, doc_id: str) -> list[Block]:
    lines = raw_text.splitlines()
    blocks: list[Block] = []
    current_heading: list[str] = []
    current_chunk: list[str] = []
    order = 1

    def flush_chunk() -> None:
        nonlocal order
        content = "\n".join(current_chunk).strip()
        if not content:
            current_chunk.clear()
            return
        blocks.append(
            Block(
                block_id=make_block_id(doc_id, order),
                doc_id=doc_id,
                page_no=1,
                order=order,
                heading_path=current_heading.copy(),
                text=content,
            )
        )
        order += 1
        current_chunk.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_chunk()
            continue
        if stripped.startswith("#"):
            flush_chunk()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            current_heading = current_heading[: max(level - 1, 0)]
            current_heading.append(title)
            continue
        current_chunk.append(stripped)

    flush_chunk()
    return blocks

