from fastapi import FastAPI, HTTPException

from apps.api.schemas import BundleRequest, ExtractRequest, IndexRequest, ParseRequest, SearchRequest
from libs.common.config import get_settings
from libs.common.models import DocumentMeta
from offline_pipeline.extract.ko_extractor import extract_knowledge
from offline_pipeline.parse.doc_parser import parse_document
from online_runtime.export.bundle import build_evidence_bundle
from online_runtime.retrieval.factory import get_retrieval_backends, merge_search_hits

app = FastAPI(title="Personal Knowledge Base MVP", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "chat_provider": settings.chat_provider,
        "default_chat_model": settings.chat_model,
        "embedding_provider": settings.embedding_provider,
        "default_embed_model": settings.embedding_model,
        "retrieval_backends": ",".join(settings.retrieval_backends),
        "ollama_base_url": settings.ollama_base_url,
    }


@app.post("/parse")
def parse_endpoint(request: ParseRequest) -> dict:
    try:
        meta = DocumentMeta.from_inputs(
            doc_id=request.doc_id,
            doc_type=request.doc_type,
            dept=request.dept,
            year=request.year,
            source_path=request.file_path,
        )
        document = parse_document(file_path=request.file_path, text=request.text, meta=meta)
        return document.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/extract")
def extract_endpoint(request: ExtractRequest) -> dict:
    try:
        meta = DocumentMeta.from_inputs(
            doc_id=request.doc_id,
            doc_type=request.doc_type,
            dept=request.dept,
            year=request.year,
            source_path=request.file_path,
        )
        document = parse_document(file_path=request.file_path, text=request.text, meta=meta)
        extracted = extract_knowledge(
            document,
            chat_model=request.chat_model,
            chat_provider=request.chat_provider,
        )
        return {
            "document": document.model_dump(),
            "facts": [item.model_dump() for item in extracted.facts],
            "experiences": [item.model_dump() for item in extracted.experiences],
            "expressions": [item.model_dump() for item in extracted.expressions],
            "summary": extracted.summary.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/bundle")
def bundle_endpoint(request: BundleRequest) -> dict:
    try:
        meta = DocumentMeta.from_inputs(
            doc_id=request.doc_id,
            doc_type="input",
            dept=request.dept,
            year=request.year,
            source_path=request.file_path,
        )
        document = parse_document(file_path=request.file_path, text=request.text, meta=meta)
        bundle = build_evidence_bundle(
            document=document,
            task_id=request.task_id,
            task_type=request.task_type,
            dept=request.dept,
            year=request.year,
            outline=request.outline,
            chat_provider=request.chat_provider,
            chat_model=request.chat_model,
            embedding_provider=request.embedding_provider,
            embedding_model=request.embedding_model,
            retrieval_backends=request.retrieval_backends,
            persist_index=request.persist_index,
        )
        return bundle.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/index")
def index_endpoint(request: IndexRequest) -> dict:
    try:
        meta = DocumentMeta.from_inputs(
            doc_id=request.doc_id,
            doc_type=request.doc_type,
            dept=request.dept,
            year=request.year,
            source_path=request.file_path,
        )
        document = parse_document(file_path=request.file_path, text=request.text, meta=meta)
        extracted = extract_knowledge(
            document,
            chat_model=request.chat_model,
            chat_provider=request.chat_provider,
        )
        backend_instances = get_retrieval_backends(request.retrieval_backends)
        backend_results = []
        for backend in backend_instances:
            _, backend_info = backend.create_retriever(
                document=document,
                extracted=extracted,
                persist_index=True,
                embedding_provider=request.embedding_provider,
                embedding_model=request.embedding_model,
            )
            backend_results.append(backend_info)
        return {
            "doc_id": document.meta.doc_id,
            "backend_results": backend_results,
            "block_count": len(document.blocks),
            "knowledge_object_count": len(extracted.facts) + len(extracted.experiences),
            "expression_count": len(extracted.expressions),
            "summary": extracted.summary.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/search")
def search_endpoint(request: SearchRequest) -> dict:
    backend_instances = get_retrieval_backends(request.retrieval_backends)
    hit_groups = [
        backend.search(
            query=request.query,
            top_k=request.top_k,
            doc_id=request.doc_id,
            item_types=request.item_types,
        )
        for backend in backend_instances
    ]
    hits = merge_search_hits(hit_groups, top_k=request.top_k)
    return {"hits": [item.model_dump() for item in hits]}
