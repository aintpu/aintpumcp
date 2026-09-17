from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.loader import KnowledgeDocument, OFFICES, load_documents, office_counts
from app.models import (
    OfficeInfo,
    OfficeListResponse,
    Provenance,
    SearchItem,
    SearchResponse,
    SourceDocument,
    SourceResponse,
)


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    output: list[str] = []
    for part in TOKEN_RE.findall((text or "").lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", part):
            if len(part) <= 8:
                output.append(part)
            output.extend(part[index:index + 2] for index in range(max(0, len(part) - 1)))
        else:
            output.append(part)
    return output


def normalise(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", (text or "").lower())


class KnowledgeSearch:
    def __init__(self, data_root: Path):
        self.documents = load_documents(data_root)
        self.by_id = {document.source_id: document for document in self.documents}
        grouped: dict[str, list[KnowledgeDocument]] = defaultdict(list)
        grouped["all"] = list(self.documents)
        for document in self.documents:
            grouped[document.office_code].append(document)
        self.grouped = dict(grouped)
        self.bm25 = {
            office: BM25Okapi([
                tokenize(f"{document.title} {document.title} {document.text}")
                for document in documents
            ])
            for office, documents in self.grouped.items()
            if documents
        }

    def list_offices(self) -> OfficeListResponse:
        counts = office_counts(self.documents)
        return OfficeListResponse(
            offices=[
                OfficeInfo(code=code, name=name, document_count=counts[code])
                for code, name in OFFICES.items()
            ],
            total_documents=len(self.documents),
        )

    @staticmethod
    def _provenance(document: KnowledgeDocument) -> Provenance:
        return Provenance(
            source_id=document.source_id,
            source_unit=document.office_name,
            source_url=document.source_url,
            source_file=document.source_file,
            source_commit=document.source_commit,
            verified_at=document.verified_at,
            content_hash=document.content_hash,
        )

    def search(
        self,
        query: str,
        *,
        office: str | None = None,
        content_types: list[str] | None = None,
        limit: int = 5,
    ) -> SearchResponse:
        query = query.strip()
        if not query:
            raise ValueError("query 不可為空")
        if office is not None and office not in OFFICES:
            raise ValueError(f"不支援的處室代碼：{office}")
        limit = max(1, min(int(limit), 10))
        key = office or "all"
        documents = self.grouped.get(key, [])
        if not documents:
            return SearchResponse(query=query, office=office, items=[], count=0, provenance=[])

        query_tokens = tokenize(query)
        raw_scores = self.bm25[key].get_scores(query_tokens)
        query_norm = normalise(query)
        allowed_types = {item.lower() for item in content_types or []}
        ranked: list[tuple[float, KnowledgeDocument]] = []

        for raw_score, document in zip(raw_scores, documents):
            if allowed_types and document.content_type.lower() not in allowed_types:
                continue
            title_norm = normalise(document.title)
            text_norm = normalise(document.text)
            score = float(raw_score)
            if query_norm and query_norm == title_norm:
                score += 30.0
            elif query_norm and query_norm in title_norm:
                score += 16.0
            elif title_norm and title_norm in query_norm:
                score += 10.0
            if query_norm and query_norm in text_norm:
                score += 6.0
            if score > 0:
                ranked.append((score, document))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected: list[tuple[float, KnowledgeDocument]] = []
        seen: set[tuple[str, str | None]] = set()
        for score, document in ranked:
            dedupe_key = (document.title, document.page)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            selected.append((score, document))
            if len(selected) >= limit:
                break

        items = [
            SearchItem(
                source_id=document.source_id,
                office_code=document.office_code,
                office_name=document.office_name,
                title=document.title,
                content_type=document.content_type,
                page=document.page,
                published_at=document.published_at,
                excerpt=document.text[:1200],
                source_url=document.source_url,
                score=round(score, 4),
            )
            for score, document in selected
        ]
        provenance = [self._provenance(document) for _, document in selected]
        return SearchResponse(
            query=query,
            office=office,
            items=items,
            count=len(items),
            provenance=provenance,
        )

    def get_source(self, source_id: str) -> SourceResponse:
        document = self.by_id.get(source_id.strip())
        if document is None:
            raise ValueError("找不到公開來源；請先使用搜尋工具取得有效的 source_id")
        return SourceResponse(
            document=SourceDocument(
                source_id=document.source_id,
                office_code=document.office_code,
                office_name=document.office_name,
                title=document.title,
                content_type=document.content_type,
                page=document.page,
                published_at=document.published_at,
                text=document.text[:12000],
                source_url=document.source_url,
            ),
            provenance=self._provenance(document),
        )

