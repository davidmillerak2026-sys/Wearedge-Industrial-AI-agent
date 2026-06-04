from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wear_edge_rag.agent import IndustrialRAGAgent
from wear_edge_rag.contracts import check_rag_answer_contract
from wear_edge_rag.documents import chunk_documents, load_documents
from wear_edge_rag.retriever import SparseTfidfIndex


class BadLLM:
    provider = "bad-test"

    def generate(self, prompt: str) -> str:
        return "I cannot follow the requested contract."


class RAGContractTests(unittest.TestCase):
    def test_contract_accepts_required_json_shape(self) -> None:
        answer = json.dumps(
            {
                "direct_answer": "Follow the released SOP evidence before restarting the drive.",
                "measured_facts": ["The SOP mentions alarm E-07 and cooling airflow."],
                "inference": ["The alarm response is related to temperature or airflow."],
                "missing_evidence": ["Confirm current cabinet temperature."],
                "residual_risk": "Restarting without airflow recovery could repeat the alarm.",
                "safe_next_step": "Stop feeding new parts and inspect cooling airflow before restart.",
                "citations": ["S1"],
                "requires_human_approval": True,
            }
        )

        check = check_rag_answer_contract(answer, allowed_citations=["S1"])

        self.assertTrue(check.ok)
        self.assertIsNotNone(check.structured)
        self.assertEqual(check.structured.citations, ["S1"])

    def test_contract_rejects_unknown_citation(self) -> None:
        answer = json.dumps(
            {
                "direct_answer": "Use the cited evidence.",
                "measured_facts": ["A fact."],
                "inference": ["An inference."],
                "missing_evidence": [],
                "residual_risk": "Risk remains.",
                "safe_next_step": "Escalate.",
                "citations": ["S9"],
                "requires_human_approval": True,
            }
        )

        check = check_rag_answer_contract(answer, allowed_citations=["S1"])

        self.assertFalse(check.ok)
        self.assertTrue(any("unknown citation" in violation for violation in check.violations))

    def test_contract_rejects_non_string_list_items(self) -> None:
        answer = json.dumps(
            {
                "direct_answer": "Use the cited evidence.",
                "measured_facts": [123],
                "inference": ["An inference."],
                "missing_evidence": [],
                "residual_risk": "Risk remains.",
                "safe_next_step": "Escalate.",
                "citations": ["S1"],
                "requires_human_approval": True,
            }
        )

        check = check_rag_answer_contract(answer, allowed_citations=["S1"])

        self.assertFalse(check.ok)
        self.assertTrue(any("measured_facts must contain" in violation for violation in check.violations))

    def test_agent_returns_degraded_contract_when_model_refuses_shape(self) -> None:
        docs = load_documents([ROOT / "data" / "sample_knowledge"])
        chunks = chunk_documents(docs, max_chars=500, overlap=80)
        agent = IndustrialRAGAgent(
            retriever=SparseTfidfIndex(chunks),
            llm=BadLLM(),
            response_language="English",
        )

        result = agent.ask("drive alarm E-07 cooling airflow")

        self.assertEqual(result.contract["mode"], "degraded")
        self.assertTrue(result.contract["repaired"])
        self.assertIsNotNone(result.structured)
        self.assertTrue(result.structured["requires_human_approval"])
        self.assertTrue(result.citations)

    def test_agent_returns_degraded_contract_without_evidence(self) -> None:
        agent = IndustrialRAGAgent(
            retriever=SparseTfidfIndex([]),
            llm=BadLLM(),
            response_language="English",
        )

        result = agent.ask("unknown problem")

        self.assertEqual(result.contract["mode"], "degraded")
        self.assertEqual(result.contract["reason"], "no retrieved evidence matched the question")
        self.assertEqual(result.citations, [])
        self.assertEqual(result.confidence, "low")


if __name__ == "__main__":
    unittest.main()
