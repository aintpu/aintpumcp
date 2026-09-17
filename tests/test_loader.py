import unittest
from pathlib import Path

from app.loader import OFFICES, load_documents, office_counts


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


class LoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = load_documents(DATA_ROOT)

    def test_all_offices_have_documents(self):
        counts = office_counts(self.documents)
        self.assertEqual(set(counts), set(OFFICES))
        for office, count in counts.items():
            self.assertGreater(count, 0, office)

    def test_every_document_has_stable_public_metadata(self):
        for document in self.documents:
            self.assertEqual(len(document.source_id), 24)
            self.assertIn(document.office_code, OFFICES)
            self.assertTrue(document.title)
            self.assertTrue(document.text)
            self.assertTrue(document.source_file.startswith("crawler_data/"))
            self.assertNotIn("/Users/", document.source_file)
            self.assertEqual(len(document.content_hash), 64)


if __name__ == "__main__":
    unittest.main()

