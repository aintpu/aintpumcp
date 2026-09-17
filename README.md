# NTPU AIA MCP

Independent, read-only Model Context Protocol server for public National Taipei
University administrative knowledge. This repository is intentionally separate
from `aintpu/ntpu-ai-assistant` and contains no web chat frontend.

## Endpoint

Planned production endpoint:

```text
https://aia.mcp.ntpu.ai/mcp
```

The server uses MCP Streamable HTTP and exposes office-specific search tools for:

- 體育室 (`ope`)
- 通識教育中心 (`ge`)
- 語言中心 (`lc`)
- 教務處 (`oaa`)
- 學務處 (`osa`)
- 人事室 (`hr`)
- 總務處 (`oga`)

It also exposes `search_all_offices`, `list_offices`, and `get_source`. Every
search result includes a stable `source_id`, official URL when available, source
file, source commit, verification time, and content hash.

The four bundled Human Resources source attachments are served read-only under
`https://aia.mcp.ntpu.ai/documents/hr/`, so clients can open the cited original
PDF or DOCX directly.

## Design

The MCP server returns retrieved evidence, not a second AI-generated answer. It
uses deterministic Chinese/English tokenization, BM25 ranking, exact FAQ/title
boosting, office metadata filters, and bounded excerpts. The calling AI model is
responsible for writing the final answer from returned evidence.

## Local development

Python 3.11 or newer:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
uvicorn app.server:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

## Refresh approved public data

The sync script only reads the source checkout and copies an explicit allowlist:

```bash
python scripts/sync_from_aia.py /path/to/ntpu-ai-assistant
python -m unittest discover -s tests -v
```

Review `data/manifest.json` and the Git diff before committing a refresh.

## Add to Codex

```bash
codex mcp add ntpu-aia --url https://aia.mcp.ntpu.ai/mcp
```

The URL must be registered as an MCP server; pasting it into a normal chat does
not install the tools.

## Deployment isolation

Cloudflare configuration is under `cf/` and creates only these new resources:

- Worker: `ntpu-aia-mcp`
- Durable Object/Container class: `NtpuAiaMcpBackend`
- Custom domain: `aia.mcp.ntpu.ai`

Deployment is manual through the `Deploy isolated MCP to Cloudflare` workflow.
It does not reference or update the existing `ntpu-aia-api` or AI4X MCP Worker.

Required repository secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Before the first deployment, verify that the Worker name and custom domain are
unused. Never deploy over an existing resource.
