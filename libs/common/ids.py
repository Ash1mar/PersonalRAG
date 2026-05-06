from __future__ import annotations

from uuid import uuid4


def make_doc_id(prefix: str = "doc") -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def make_block_id(doc_id: str, order: int) -> str:
    return f"{doc_id}#b{order:03d}"


def make_ko_id(kind: str, block_index: int, sentence_index: int) -> str:
    kind_prefix = {"fact": "F", "experience": "E"}.get(kind, "K")
    return f"KO_{kind_prefix}_{block_index:03d}_{sentence_index:02d}"

