from typing import Any

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    file_path: str | None = Field(default=None, description="Absolute or workspace-relative path")
    text: str | None = None
    doc_id: str | None = None
    doc_type: str | None = None
    dept: str | None = None
    year: int | None = None


class ExtractRequest(BaseModel):
    file_path: str | None = None
    text: str | None = None
    doc_id: str | None = None
    doc_type: str | None = None
    dept: str | None = None
    year: int | None = None


class SlotInput(BaseModel):
    slot_id: str
    title: str
    focus_types: list[str] = Field(default_factory=list)


class BundleRequest(BaseModel):
    file_path: str | None = None
    text: str | None = None
    doc_id: str | None = None
    task_id: str = "demo_task"
    task_type: str = "通用写作任务"
    dept: str | None = None
    year: int | None = None
    outline: list[SlotInput] | None = None


class JsonResponse(BaseModel):
    data: dict[str, Any]

