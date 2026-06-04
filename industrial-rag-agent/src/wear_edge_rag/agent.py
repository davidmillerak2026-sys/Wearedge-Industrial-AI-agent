from __future__ import annotations

from pathlib import Path

from .documents import chunk_documents, load_documents
from .llm import LLMClient, create_llm
from .prompts import load_prompt_template
from .retriever import SparseTfidfIndex
from .schemas import AgentAnswer
from .tools import KnowledgeToolCatalog
from .workflow import RAGWorkflow


class IndustrialRAGAgent:
    def __init__(
        self,
        *,
        retriever: SparseTfidfIndex,
        llm: LLMClient,
        prompt_template: str | None = None,
        response_language: str = "English",
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.prompt_template = prompt_template or load_prompt_template(None)
        self.response_language = response_language
        self.tools = KnowledgeToolCatalog(retriever)

    @classmethod
    def build_index(
        cls,
        sources: list[str | Path],
        *,
        index_dir: str | Path,
        chunk_size: int = 1200,
        chunk_overlap: int = 180,
    ) -> SparseTfidfIndex:
        documents = load_documents(sources)
        chunks = chunk_documents(documents, max_chars=chunk_size, overlap=chunk_overlap)
        index = SparseTfidfIndex(chunks)
        index.save(index_dir)
        return index

    @classmethod
    def from_index(
        cls,
        index_dir: str | Path,
        *,
        provider: str = "extractive",
        model: str | None = None,
        prompt_path: str | Path | None = None,
        response_language: str = "English",
    ) -> "IndustrialRAGAgent":
        retriever = SparseTfidfIndex.load(index_dir)
        return cls(
            retriever=retriever,
            llm=create_llm(provider, model=model),
            prompt_template=load_prompt_template(prompt_path),
            response_language=response_language,
        )

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        metadata_filter: dict[str, str] | None = None,
    ) -> AgentAnswer:
        workflow = RAGWorkflow(
            tools=self.tools,
            llm=self.llm,
            prompt_template=self.prompt_template,
            response_language=self.response_language,
        )
        return workflow.run(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )

