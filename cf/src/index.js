import { Container, getContainer } from "@cloudflare/containers";


const MCP_PATH = "/mcp";
const HEALTH_PATH = "/health";
const DOCUMENTS_PATH = "/documents/";


export class NtpuAiaMcpBackend extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";

  constructor(ctx, env) {
    super(ctx, env);
    this.envVars = {
      MCP_ALLOWED_HOSTS: "ntpu-aia-mcp-legacy.aintpu.workers.dev,aia.mcp.ntpu.ai,localhost:*,127.0.0.1:*",
      PYTHONUNBUFFERED: "1",
    };
  }
}


export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (
      url.pathname !== MCP_PATH &&
      url.pathname !== HEALTH_PATH &&
      !url.pathname.startsWith(DOCUMENTS_PATH)
    ) {
      return new Response("Not found", { status: 404 });
    }

    const backend = getContainer(env.BACKEND, "singleton");
    try {
      return await backend.fetch(request);
    } catch (error) {
      console.log(JSON.stringify({
        event: "proxy_error",
        severity: "ERROR",
        path: url.pathname,
        error: String(error),
      }));
      return Response.json(
        { status: "error", message: "MCP backend is temporarily unavailable." },
        { status: 503 },
      );
    }
  },
};
