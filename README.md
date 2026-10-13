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
5. Show the recovery plan's **Staged actions** (draft customer email and proposed CRM update, marked DRAFT, NOT SENT, requiring human approval). Open graph evidence if returned: relationships are listed with their source document, with raw JSON below. Empty graph arrays are possible; never claim relationships were found when absent. Export the brief.

## Submission copy

**Project:** Customer Recovery Brain

**Pitch:** CRM health scores can lag behind the customer story. Customer Recovery Brain connects account records, support incidents, adoption reports, customer meeting notes, and recovery playbooks to explain risk with evidence and draft an accountable recovery plan.

**How it works:** Synthetic documents are ingested into a dedicated HydraDB database and collection. Hybrid retrieval with optional graph context supplies evidence to a configured LLM. An agent step then plans up to two follow-up HydraDB searches for evidence the first retrieval missed (for example root cause or renewal status) and answers once from the merged evidence. Answers cite retrieved passages, identify stale or conflicting sources, distinguish unknowns from inference, and propose recovery actions for human review. A new note can be indexed to refresh the assessment.

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

Tests cover index readiness gating, citation validation and retry, retrieval isolation, and follow-up search planning and merging. Live HydraDB/LLM calls require your configured accounts and must be verified before the demo.

## Model setup

The LLM is configured entirely in `.env`; no code changes are needed to switch.

### Demo: hosted OpenAI model (fast)

```
LLM_PROVIDER=openai
LLM_API_KEY=            # or set OPENAI_API_KEY
LLM_MODEL=gpt-5.4-mini
LLM_BASE_URL=
LLM_REASONING_EFFORT=low
LLM_MAX_WORDS=
```

With graph context on and no length limit, each answer takes ~10–12 s end to end. Retrieved synthetic evidence is sent to OpenAI.

### Private option: local model via Ollama

For privacy, run generation on your own hardware so account evidence never leaves the machine. Tested with `qwen3.5:9b` through Ollama's OpenAI-compatible endpoint:

```
LLM_PROVIDER=openai
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen3.5:9b
LLM_REASONING_EFFORT=none
LLM_MAX_WORDS=350
```

Speed depends on hardware. On an Apple Silicon laptop answers took ~70 s at `LLM_MAX_WORDS=350` (78–146 s unlimited); faster GPUs or larger memory bandwidth reduce this. Notes from testing:

- `LLM_REASONING_EFFORT=none` disables qwen3.5 thinking mode; with thinking on, answers exceeded the 90 s request timeout.
- `LLM_MAX_WORDS` is a soft answer-length limit in the system prompt. At 250 words answers took 56–76 s, but recovery plans sometimes omitted owner citations or invented dates.
- Nearly all latency is local generation; HydraDB retrieval takes 0.5–2 s. Graph context adds ~10K prompt tokens (~35 s locally) for the same retrieved documents.
- Ollama loaded the model with a 32,768-token context, which fits the system prompt, retrieved passages, and graph context.

## Live verification status (Oct 12, 2026)

- Passed: unit tests (7/7); real completion via Ollama `/v1`; HydraDB database creation and ingestion of all six sources (fixed: `title` moved into `additional_metadata`, which HydraDB v2 requires).
- HydraDB indexing of the six sources took ~37 min, mostly in `graph_creation`.
- Passed live through the running server (HydraDB hybrid retrieval with graph context → qwen3.5:9b → validated citations): **Explain the risk** (134 s), **Draft recovery plan** (128 s), **What are we missing?** (78 s). Each retrieved six sources and returned graph context.
- Fixed: qwen3.5:9b intermittently cited a nonexistent label (e.g. `[S7]`). Generation now lists the allowed labels and retries once on an invalid citation.
- Passed: new October 12 note saved, ingested, and indexed (~45 min, mostly `graph_creation`). **"What changed after the October 12 update, and which recovery actions remain necessary?"** (146 s) retrieved 7 sources, ranked the new note first, and cited it for the staging-verified / production-pending fix and the still-missing sponsor.
- Note: HydraDB graph indexing is slow (~37–45 min per batch); the app correctly refuses to answer until every source is `completed`. Plan demo recordings around this.
- Passed on OpenAI `gpt-5.4-mini` (reasoning effort low, graph context on, no length limit): all four questions above in 9.8–12.3 s, each citing all 7 retrieved sources; the October 12 note was cited in the "what changed" answer. `gpt-4.1-mini` failed the citation check in a comparison run.
- Added: recovery plans end with staged actions (draft customer email from the sourced CSM and a cited proposed CRM update, all marked DRAFT, NOT SENT); the graph panel lists HydraDB relationships with source documents. Re-verified live on `gpt-5.4-mini`: all four questions passed in 7.5–9.7 s, 22 graph relationships shown, no answer claimed anything was sent.

## Improvements after the demo (branch `improvements`)

- **Richer evidence:** six more synthetic Cedar Labs sources (billing and renewal, Q3 survey, draft incident review, internal escalation thread, August QBR, customer ops lead email), 13 sources in total. HydraDB indexed them in ~4 min.
- **Agentic follow-up search:** after the first retrieval (8 passages), the LLM plans up to `AGENT_MAX_FOLLOWUPS` (default 2, `0` disables) targeted queries for missing evidence; HydraDB fast-mode results are de-duplicated and merged before one cited answer is generated. The UI lists each follow-up query and how many new sources it added.
- **Readable answers:** answers render as Markdown (headings, lists, tables, highlighted `[S#]` citations) using DOM nodes only, so quoted source text cannot inject HTML. Export still downloads the raw Markdown.
- Verified live on `gpt-5.4-mini` with graph context: all four demo questions passed in 11.5–15 s; follow-up searches added up to 3 new sources per question (e.g. the draft incident review and the customer ops lead email), which were then cited. 10 unit tests pass.
