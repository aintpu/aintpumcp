import json
import unittest

from starlette.testclient import TestClient

from app.server import app


def decode_response(response):
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    data_lines = [
        line[6:] for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    if not data_lines:
        raise AssertionError(response.text)
    return json.loads(data_lines[-1])


class McpProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        cls.headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-03-26",
        }

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def post(self, payload):
        response = self.client.post("/mcp", headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return decode_response(response)

    def test_initialize_and_list_tools(self):
        initialized = self.post({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "tests", "version": "1.0"},
            },
        })
        self.assertIn("result", initialized)
        listed = self.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertIn("search_general_affairs", names)
        self.assertIn("search_human_resources", names)
        self.assertIn("get_source", names)

    def test_call_general_affairs_tool(self):
        called = self.post({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_general_affairs",
                "arguments": {"query": "學雜費繳費單", "limit": 3},
            },
        })
        structured = called["result"]["structuredContent"]
        self.assertGreater(structured["count"], 0)
        self.assertEqual(structured["items"][0]["office_code"], "oga")

    def test_bundled_source_document_is_served(self):
        response = self.client.get(
            "/documents/hr/form-11-attendance-leave-request.pdf"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
