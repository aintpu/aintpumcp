from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.models import OfficeListResponse, SearchResponse, SourceResponse
from app.search import KnowledgeSearch


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.getenv("NTPU_AIA_DATA_ROOT", BASE_DIR / "data"))

engine = KnowledgeSearch(DATA_ROOT)


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

mcp = FastMCP(
    "NTPU AIA Public Knowledge",
    instructions=(
        "Search verified public National Taipei University administrative knowledge. "
        "Choose the office-specific search tool when the office is known; otherwise use "
        "search_all_offices. Use get_source for the full selected excerpt. Cite source_url "
        "and do not infer facts that are absent from returned text. All tools are read-only."
    ),
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_csv_env(
            "MCP_ALLOWED_HOSTS",
            "aia.mcp.ntpu.ai,localhost:*,127.0.0.1:*,testserver",
        ),
        allowed_origins=_csv_env("MCP_ALLOWED_ORIGINS", ""),
    ),
)


def _search(
    office: str | None,
    query: str,
    content_types: list[str] | None,
    limit: int,
) -> SearchResponse:
    return engine.search(
        query,
        office=office,
        content_types=content_types,
        limit=limit,
    )


@mcp.tool(annotations=READ_ONLY)
def list_offices() -> OfficeListResponse:
    """List supported NTPU offices and the number of public searchable excerpts."""
    return engine.list_offices()


@mcp.tool(annotations=READ_ONLY)
def search_sports_office(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 體育室 public news, FAQs, pages, regulations, and forms."""
    return _search("ope", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_general_education(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 通識教育中心 public news, FAQs, pages, and regulations."""
    return _search("ge", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_language_center(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 語言中心 public courses, tests, news, FAQs, staff pages, and regulations."""
    return _search("lc", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_academic_affairs(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 教務處 public academic regulations, including registration and credits."""
    return _search("oaa", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_student_affairs(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 學務處 public student-life, counseling, housing, aid, and related regulations."""
    return _search("osa", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_human_resources(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 人事室 public attendance, leave, labor-law FAQs, and contingency forms."""
    return _search("hr", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_general_affairs(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search 總務處 public maintenance, procurement, property, cashier, parking, safety, and document FAQs."""
    return _search("oga", query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def search_all_offices(
    query: str,
    content_types: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    """Search all supported NTPU offices when the responsible office is unknown."""
    return _search(None, query, content_types, limit)


@mcp.tool(annotations=READ_ONLY)
def get_source(source_id: str) -> SourceResponse:
    """Return the full public excerpt and provenance for a source_id from a search result."""
    return engine.get_source(source_id)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    counts = engine.list_offices()
    return JSONResponse({
        "status": "ok",
        "service": "ntpu-aia-mcp",
        "documents": counts.total_documents,
        "offices": len(counts.offices),
    })


app = mcp.streamable_http_app()
app.mount(
    "/documents",
    StaticFiles(directory=DATA_ROOT / "documents"),
    name="documents",
)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
