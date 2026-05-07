from __future__ import annotations

from libs.common.config import get_settings
from libs.common.models import SearchHit
from online_runtime.retrieval.backend import BaseRetrievalBackend
from online_runtime.retrieval.backends import CompanyBackend, LocalKeywordBackend, LocalVectorBackend


def get_retrieval_backends(backend_ids: list[str] | None = None) -> list[BaseRetrievalBackend]:
    settings = get_settings()
    resolved = backend_ids or settings.retrieval_backends
    backends: list[BaseRetrievalBackend] = []
    for backend_id in resolved:
        if backend_id == "local_vector":
            backends.append(LocalVectorBackend())
        elif backend_id == "local_keyword":
            backends.append(LocalKeywordBackend())
        elif backend_id == "company":
            backends.append(CompanyBackend())
        else:
            raise ValueError(f"Unsupported retrieval backend: {backend_id}")
    return backends


def merge_search_hits(hit_groups: list[list[SearchHit]], top_k: int) -> list[SearchHit]:
    merged: dict[tuple[str, str], SearchHit] = {}
    for hits in hit_groups:
        for hit in hits:
            key = (hit.item_type, hit.item_id)
            if key not in merged or hit.score > merged[key].score:
                merged[key] = hit
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]
