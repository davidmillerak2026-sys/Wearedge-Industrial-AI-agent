from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wear_edge_rag.agent import IndustrialRAGAgent
from wear_edge_rag.llm import ExtractiveLLM


class IndustrialRAGAgentContractTests(unittest.TestCase):
    def test_extractive_agent_returns_structured_contract_and_audit_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index = IndustrialRAGAgent.build_index(
                [ROOT / "data" / "sample_knowledge"],
                index_dir=Path(temp_dir) / "rag_index",
                chunk_size=500,
                chunk_overlap=80,
            )
            agent = IndustrialRAGAgent(
                retriever=index,
                llm=ExtractiveLLM(),
                response_language="English",
            )

            result = agent.ask("What should the operator do for drive alarm E-07?", top_k=3)

        self.assertEqual(result.contract["mode"], "structured")
        self.assertIsNotNone(result.structured)
        self.assertIn("direct_answer", result.structured)
        self.assertTrue(result.structured["citations"])
        self.assertTrue(result.citations)
        self.assertIn("document_id", result.citations[0])
        self.assertIn("revision", result.citations[0])
        self.assertIn("approval_status", result.citations[0])


if __name__ == "__main__":
    unittest.main()
