from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OfficeInfo(StrictModel):
    code: str
    name: str
    document_count: int = Field(ge=0)


class OfficeListResponse(StrictModel):
    offices: list[OfficeInfo]
    total_documents: int = Field(ge=0)


class Provenance(StrictModel):
    source_id: str
    source_unit: str
    source_url: str | None = None
    source_file: str
    source_commit: str | None = None
    verified_at: str
    content_hash: str


class SearchItem(StrictModel):
    source_id: str
    office_code: str
    office_name: str
    title: str
    content_type: str
    page: str | None = None
    published_at: str | None = None
    excerpt: str
    source_url: str | None = None
    score: float


class SearchResponse(StrictModel):
    query: str
    office: str | None = None
    items: list[SearchItem]
    count: int = Field(ge=0)
    provenance: list[Provenance]


class SourceDocument(StrictModel):
    source_id: str
    office_code: str
    office_name: str
    title: str
    content_type: str
    page: str | None = None
    published_at: str | None = None
    text: str
    source_url: str | None = None


class SourceResponse(StrictModel):
    document: SourceDocument
    provenance: Provenance

