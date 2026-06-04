from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wear_edge_rag.agent import IndustrialRAGAgent
from wear_edge_rag.documents import chunk_documents, load_documents
from wear_edge_rag.llm import ExtractiveLLM
from wear_edge_rag.retriever import SparseTfidfIndex
from wear_edge_rag.tools import KnowledgeToolCatalog
from wear_edge_rag.validators import evaluate_evidence


class WorkflowTests(unittest.TestCase):
    def test_agent_contract_exposes_named_workflow_stages(self) -> None:
        docs = load_documents([ROOT / "data" / "sample_knowledge"])
        chunks = chunk_documents(docs, max_chars=500, overlap=80)
        agent = IndustrialRAGAgent(
            retriever=SparseTfidfIndex(chunks),
            llm=ExtractiveLLM(),
            response_language="English",
        )

        result = agent.ask("drive alarm E-07 cooling airflow")

        stage_names = [stage["name"] for stage in result.contract["stages"]]
        self.assertEqual(
            stage_names,
            [
                "search_knowledge",
                "evidence_gate",
                "model_draft",
                "validate_contract",
                "action_gate",
            ],
        )
        self.assertEqual(result.contract["action_gate"]["status"], "requires_human_approval")

    def test_knowledge_tool_returns_bounded_result_envelope(self) -> None:
        docs = load_documents([ROOT / "data" / "sample_knowledge"])
        chunks = chunk_documents(docs, max_chars=500, overlap=80)
        tool = KnowledgeToolCatalog(SparseTfidfIndex(chunks))

        result = tool.search_knowledge("drive alarm E-07", top_k=2)
        envelope = result.as_dict()

        self.assertTrue(result.ok)
        self.assertEqual(result.tool_name, "search_knowledge")
        self.assertEqual(envelope["data_count"], len(result.data))
        self.assertLessEqual(envelope["metadata"]["result_count"], 2)

    def test_evidence_gate_warns_when_controlled_metadata_is_missing(self) -> None:
        docs = load_documents([ROOT / "data" / "sample_knowledge"])
        chunks = chunk_documents(docs, max_chars=500, overlap=80)
        hits = SparseTfidfIndex(chunks).search("drive alarm E-07", top_k=1)
        citations = [hits[0].to_citation("S1")]

        gate = evaluate_evidence(hits, citations)

        self.assertTrue(gate.ok)
        self.assertTrue(any("approval_status=released" in warning for warning in gate.warnings))
        self.assertTrue(any("revision" in warning for warning in gate.warnings))


if __name__ == "__main__":
    unittest.main()
