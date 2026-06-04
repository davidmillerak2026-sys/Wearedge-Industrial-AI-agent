from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wear_edge_rag.llm import ExtractiveLLM


class ExtractiveLLMTests(unittest.TestCase):
    def test_extractive_response_uses_chinese_wrapper_when_requested(self) -> None:
        prompt = """You are WearEdge Pro's industrial RAG assistant.

Response language: Chinese

Question:
电机驱动器报警 E-07 应该如何处理？

Retrieved evidence:
[S1] sop_motor_drive_alarm.md
Text: Alarm E-07 means over-temperature or insufficient cooling airflow.
"""

        answer = ExtractiveLLM().generate(prompt)

        self.assertTrue(answer.startswith("回答:"))
        self.assertIn("最终动作应以已发布的 SOP/QMS 权限为准", answer)
        self.assertIn("[S1] sop_motor_drive_alarm.md", answer)


if __name__ == "__main__":
    unittest.main()
