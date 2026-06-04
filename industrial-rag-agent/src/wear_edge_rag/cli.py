from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import IndustrialRAGAgent
from .config import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WearEdge Pro industrial RAG agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index industrial knowledge files")
    index_parser.add_argument("--source", action="append", required=True, help="File or folder to index")
    index_parser.add_argument("--index", default=".rag_index", help="Index output directory")
    index_parser.add_argument("--chunk-size", type=int, default=1200)
    index_parser.add_argument("--chunk-overlap", type=int, default=180)

    ask_parser = subparsers.add_parser("ask", help="Ask a retrieval-backed question")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--index", default=".rag_index", help="Index directory")
    ask_parser.add_argument("--settings", help="Optional SETTINGS JSON path")
    ask_parser.add_argument("--provider", choices=["extractive", "ollama", "openai-compatible"], help="LLM provider")
    ask_parser.add_argument("--model", help="Model name")
    ask_parser.add_argument("--top-k", type=int, help="Number of chunks to retrieve")
    ask_parser.add_argument("--prompt", help="Prompt template path")
    ask_parser.add_argument("--language", default=None, help="Response language")
    ask_parser.add_argument("--json", action="store_true", help="Emit JSON")

    args = parser.parse_args(argv)
    if args.command == "index":
        index = IndustrialRAGAgent.build_index(
            [Path(item) for item in args.source],
            index_dir=args.index,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        print(f"Indexed {len(index.chunks)} chunks into {args.index}")
        return 0

    settings = load_settings(args.settings)
    provider = args.provider or settings["provider"]
    model = args.model or settings.get("model")
    top_k = args.top_k or int(settings["top_k"])
    prompt_path = args.prompt or settings.get("prompt_path")
    language = args.language or settings.get("response_language", "English")

    agent = IndustrialRAGAgent.from_index(
        args.index,
        provider=provider,
        model=model,
        prompt_path=prompt_path,
        response_language=language,
    )
    result = agent.ask(args.question, top_k=top_k)
    if args.json:
        print(
            json.dumps(
                {
                    "answer": result.answer,
                    "structured": result.structured,
                    "provider": result.provider,
                    "confidence": result.confidence,
                    "citations": result.citations,
                    "contract": result.contract,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(result.answer)
        print("\nCitations:")
        for citation in result.citations:
            print(f"- [{citation['id']}] {citation['title']} ({citation['path']}) score={citation['score']}")
        print(
            f"\nProvider: {result.provider} | Confidence: {result.confidence} | "
            f"Contract: {result.contract.get('mode', 'unknown')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

