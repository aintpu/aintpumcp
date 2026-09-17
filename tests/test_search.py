import unittest
from pathlib import Path

from app.search import KnowledgeSearch


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = KnowledgeSearch(DATA_ROOT)

    def test_tuition_question_routes_to_general_affairs_source(self):
        response = self.engine.search(
            "學雜費繳費單要去哪裡查詢與繳納？",
            office="oga",
            limit=3,
        )
        self.assertGreater(response.count, 0)
        self.assertEqual(response.items[0].office_code, "oga")
        self.assertIn("學雜費繳費單", response.items[0].title)
        self.assertIn("tuition-fees", response.items[0].source_url or "")

    def test_office_filter_prevents_cross_office_results(self):
        response = self.engine.search("差勤系統故障", office="hr", limit=5)
        self.assertGreater(response.count, 0)
        self.assertTrue(all(item.office_code == "hr" for item in response.items))

    def test_bundled_hr_document_uses_new_isolated_domain(self):
        response = self.engine.search(
            "職員及無線上請假權限人員差勤系統新增變更註銷請示假單",
            office="hr",
            limit=5,
        )
        urls = [item.source_url or "" for item in response.items]
        self.assertTrue(any(
            url.startswith("https://aia.mcp.ntpu.ai/documents/hr/")
            for url in urls
        ))

    def test_get_source_uses_search_source_id(self):
        result = self.engine.search("差勤系統故障", office="hr", limit=1)
        source = self.engine.get_source(result.items[0].source_id)
        self.assertEqual(source.document.source_id, result.items[0].source_id)
        self.assertEqual(source.document.office_code, "hr")

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.search(" ", office="oga")


if __name__ == "__main__":
    unittest.main()
