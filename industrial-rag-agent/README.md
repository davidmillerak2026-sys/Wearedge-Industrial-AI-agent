# WearEdge Pro Industrial RAG Agent

Local-first industrial RAG agent for WearEdge Pro. It follows the same spirit as `choukha/industrial-ai-agents`: keep industrial data local, index manuals/SOPs/logs/quality plans, and answer operator questions with explicit evidence.

## What It Does

- Index industrial documents from folders or files.
- Retrieve relevant SOP, maintenance, quality, and safety evidence.
- Answer with citations and residual-risk notes.
- Run without cloud services by default through an extractive fallback.
- Optionally call Ollama or an OpenAI-compatible local/enterprise endpoint.
- Keep the retrieval layer isolated so it can later be replaced by Chroma, FAISS, or an MCP-backed knowledge service.

## Suggested Placement In WearEdge-Pro

Copy this folder into the repository root as:

```text
industrial-rag-agent/
```

Then commit it with the WearEdge-Pro README update or use it as the first reference implementation for the planned SOP application store.

## Quick Start

```bash
cd industrial-rag-agent
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m wear_edge_rag.cli index --source data/sample_knowledge --index .rag_index
python -m wear_edge_rag.cli ask "What should the operator do for drive alarm E-07?" --index .rag_index
```

The default provider is `extractive`, so the quick start works without a model server. For local LLM generation:

```bash
python -m wear_edge_rag.cli ask "Summarize the IQC visual check flow." --index .rag_index --provider ollama --model qwen2.5:7b
```

Ollama defaults to `http://localhost:11434`. You can override it:

```bash
set OLLAMA_BASE_URL=http://localhost:11434
```

For OpenAI-compatible endpoints:

```bash
set OPENAI_COMPATIBLE_BASE_URL=http://localhost:8000/v1
set OPENAI_COMPATIBLE_API_KEY=local-key
python -m wear_edge_rag.cli ask "What evidence is required before releasing a held lot?" --provider openai-compatible --model local-model
```

## Architecture

```text
operator query
    -> document retriever
    -> evidence bundle with citations
    -> prompt contract
    -> local/extractive/Ollama/OpenAI-compatible answer
    -> structured answer with cited source ids
```

Key modules:

- `documents.py`: loaders and chunking for text, markdown, JSON, and CSV.
- `retriever.py`: dependency-free sparse TF-IDF index with JSON persistence.
- `llm.py`: extractive fallback plus Ollama and OpenAI-compatible clients.
- `agent.py`: retrieval-to-answer orchestration and citation handling.
- `cli.py`: index and ask commands.

## Production Notes

- Use the sparse backend as the edge-safe baseline.
- Add Chroma or another vector backend behind the same `search(query)` contract when embeddings are available.
- Store original document ids, revision ids, and SOP/control-plan versions in metadata before using this for audit-sensitive decisions.
- Do not let the agent make final safety, quality, or maintenance decisions without a released rule or human approval path.

## Example Outputs

The answer contract is intentionally operator-oriented:

```text
Answer:
For drive alarm E-07, stop feeding new parts, keep the work order in hold state, verify cooling airflow, and inspect the inverter cabinet temperature.

Evidence:
[S1] sop_motor_drive_alarm.md - E-07 reaction plan
[S2] maintenance_log.csv - repeated E-07 after clogged filter

Residual risk:
If cabinet temperature remains high after airflow recovery, escalate to maintenance before restart.
```

