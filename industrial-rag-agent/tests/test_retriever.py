from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wear_edge_rag.documents import chunk_documents, load_documents
from wear_edge_rag.retriever import SparseTfidfIndex


class SparseRetrieverTests(unittest.TestCase):
    def test_sparse_retriever_finds_alarm_e07(self) -> None:
        docs = load_documents([ROOT / "data" / "sample_knowledge"])
        chunks = chunk_documents(docs, max_chars=500, overlap=80)
        index = SparseTfidfIndex(chunks)

        hits = index.search("drive alarm E-07 cooling airflow", top_k=3)

        self.assertTrue(hits)
        self.assertEqual(hits[0].chunk.title, "sop_motor_drive_alarm.md")
        self.assertGreater(hits[0].score, 0)


if __name__ == "__main__":
    unittest.main()
