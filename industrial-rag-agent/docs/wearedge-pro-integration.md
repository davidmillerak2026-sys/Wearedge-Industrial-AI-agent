# WearEdge-Pro Integration Notes

This module is designed as an add-on for the current WearEdge-Pro concept repo.

## Recommended Repository Layout

```text
WearEdge-Pro/
  README.md
  industrial-rag-agent/
    README.md
    pyproject.toml
    src/wear_edge_rag/
    data/sample_knowledge/
    prompts/
    docs/
    tests/
```

## How It Fits WearEdge-Pro

- AR glasses or mobile edge device sends an operator question, alarm code, or captured defect context.
- The RAG agent retrieves SOPs, maintenance logs, quality plans, and safety rules.
- The answer returns cited evidence for audio narration or AR overlay.
- TriggerFlow can run visual comparison, RAG retrieval, and safety checks as parallel branches, then merge the result for rendering.

## TriggerFlow Boundary

Keep this RAG module as a deterministic service boundary:

- Input: `question`, optional `station_id`, `lot_id`, `alarm_code`, `image_id`.
- Retrieval output: top evidence chunks with source ids and scores.
- Generation output: answer, citations, confidence, residual risk.
- Write side effects: none by default.

If later connected to MES/QMS, put writes behind explicit tools such as `record_defect`, `place_quality_hold`, or `submit_disposition`.

## Data Governance

- Keep production SOPs and logs out of public commits.
- Index local copies at deployment time.
- Store document revision and approval metadata alongside every source file.
- Treat the agent answer as decision support, not final release authority.

