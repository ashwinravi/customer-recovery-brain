# Customer Recovery Brain

A local runnable hackathon prototype: connect synthetic customer records, explain conflicting risk signals, and draft a cited recovery plan with proposed owners and exit criteria.

## Run (Python 3.10+)

```bash
cd customer-recovery-brain
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` locally. Set `HYDRA_DB_API_KEY`, `LLM_API_KEY`, and `LLM_MODEL`. Choose `LLM_PROVIDER=openai` or `anthropic`. For an OpenAI-compatible endpoint set `LLM_BASE_URL` to its API base URL. Use a model available in your account; there is no assumed model default. Restart after changing settings.

```bash
python app.py
```

Open http://127.0.0.1:8080. Click **Index evidence**, then **Check status** until every source is `completed`. Uncheck **Local evidence preview**, then click **Analyze account**. Database provisioning and indexing can take several minutes. If a source is `errored`, inspect it in HydraDB; resolve the cause before proceeding. To retry ingestion after fixing a failed source, remove that source's local ID from `indexed_local_ids` in `data/runtime.json` and click Index evidence again. Do not remove your database.

Without keys or dependencies, `python app.py` still opens the UI and supports explicitly labeled local evidence preview. That mode only displays documents; it does not generate an AI answer or call HydraDB. Do not present it as live AI.

## Two-minute demo

1. Explain the problem: the September CRM record is Green, but newer customer signals are scattered.
2. Ask **Explain the risk**. Show cited evidence: open sync incident, 40% adoption decline, sponsor gap. Causality and cancellation remain unproven.
3. Ask **Draft recovery plan**. Show proposed actions with sourced owners, milestones, and sustained recovery criteria.
4. Save the suggested new customer note. Click Index evidence, wait for completed status, then ask: “What changed after the October 12 update, and which recovery actions remain necessary?”
5. Open graph evidence if returned. Empty graph arrays are possible; never claim relationships were found when absent. Export the brief.

## Submission copy

**Project:** Customer Recovery Brain

**Pitch:** CRM health scores can lag behind the customer story. Customer Recovery Brain connects account records, support incidents, adoption reports, customer meeting notes, and recovery playbooks to explain risk with evidence and draft an accountable recovery plan.

**How it works:** Synthetic documents are ingested into a dedicated HydraDB database and collection. Hybrid retrieval with optional graph context supplies evidence to a configured LLM. Answers cite retrieved passages, identify stale or conflicting sources, distinguish unknowns from inference, and propose recovery actions for human review. A new note can be indexed to refresh the assessment.

**Scope:** One synthetic account. Document ingestion represents source systems; live CRM, support, and analytics integrations are not implemented. No automatic external actions. Citation label validation checks existence, not factual entailment. This is a prototype, not a validated churn predictor.

## Technical notes

- UI and APIs run on localhost only. Keys remain in the Python process; `.env` is never served.
- `/api/ingest`, `/api/status`, `/api/ask`, `/api/note`, and `/api/config` provide the end-to-end workflow.
- New notes persist locally in `data/runtime.json` and reach HydraDB only after ingestion.
- UI screenshot facts describe the original synthetic snapshots; the generated assessment is what updates with new evidence.
- The graph toggle changes both graph context and HydraDB query mode (fast versus thinking); it is not a controlled graph-only benchmark.
- No deployment, authentication, tenancy, production access control, or service integrations are included.
- Official reference: https://hydradb.com/blog/build-company-brain-ai-agents and https://docs.hydradb.com/api-reference/v2/sdks
- Initial Devpost submission deadline supplied by organizers: 4 PM Pacific, October 12, 2026; final demo-video deadline: 10 PM Pacific. Submission itself is manual.

## Local validation

```bash
python -m unittest discover -s tests -v
```

Tests cover index readiness gating, citation validation, and retrieval isolation. Live HydraDB/LLM calls require your configured accounts and must be verified before the demo.

## Local model setup (Ollama)

Tested with `qwen3.5:9b` through Ollama's OpenAI-compatible endpoint:

```
LLM_PROVIDER=openai
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen3.5:9b
LLM_REASONING_EFFORT=none
```

`LLM_REASONING_EFFORT=none` disables qwen3.5 thinking mode. With thinking on, a full assessment exceeded the 90 s request timeout; with it off, a six-source assessment took ~63 s on Apple Silicon. Ollama loaded the model with a 32,768-token context, which fits the system prompt plus 12 retrieved passages.

## Live verification status (Oct 12, 2026)

- Passed: unit tests (6/6); real completion via Ollama `/v1`; cited assessment generated by qwen3.5:9b from the six synthetic sources (citation validation passed); HydraDB database creation and ingestion of all six sources (fixed: `title` moved into `additional_metadata`, which HydraDB v2 requires).
- Pending at initial commit: HydraDB indexing was still in `graph_creation` after ~12 min, so the HydraDB query → Ollama answer path, the three demo questions, and the new-note reindex had not yet been verified live.
