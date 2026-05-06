from fastapi import FastAPI, HTTPException

from apps.api.schemas import BundleRequest, ExtractRequest, ParseRequest
from libs.common.models import DocumentMeta
from offline_pipeline.extract.expression_extractor import get_default_expressions
from offline_pipeline.extract.fact_extractor import extract_facts
from offline_pipeline.extract.experience_extractor import extract_experiences
from offline_pipeline.parse.doc_parser import parse_document
from online_runtime.export.bundle import build_evidence_bundle

app = FastAPI(title="Personal Knowledge Base MVP", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
        facts = extract_facts(document)
        experiences = extract_experiences(document)
        expressions = get_default_expressions()
        return {
            "document": document.model_dump(),
            "facts": [item.model_dump() for item in facts],
            "experiences": [item.model_dump() for item in experiences],
            "expressions": [item.model_dump() for item in expressions],
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
        )
        return bundle.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

