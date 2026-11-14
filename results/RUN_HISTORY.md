# Retrieval dev runs

- `retrieval_dev_v1`: complete runner output; Dense/Hybrid have 2 network-dependent query errors each, BM25 succeeds on all 17. All 15 answerable queries run successfully for each method. No new embedding API requests succeeded.
- `retrieval_dev_v2`: incomplete run after explicit user permission to send the two new queries. Partial `retrieval.traces.json` records 36 query results, including 2 successful embedding API calls and 94 prompt tokens. A Windows output-write failure stopped the run; no summary was produced. Preserve this partial result for usage/error provenance.
- `retrieval_dev_v3`: authoritative complete retrieval comparison, 17/17 successes per method, zero errors. All embeddings cached, so new API requests/tokens in this run are zero. Full summary and separate raw/evaluated traces are present. Monetary API cost is unknown pending billing.

All runs use only dev queries, the unchanged Day 6 snapshot C and frozen benchmark. No agent answer/abstention benchmark or test retrieval has been run. Trace files contain corpus excerpts; verify redistribution rights before publishing.

## Agent runs (subsequent work)

- `agent_smoke_v1`: real provider connection succeeds, agent rejects a tool-call response carrying `finish_reason=stop`; fixed compatibility and added regression test. No retrieval completed in this smoke.
- `agent_smoke_v2` and `agent_smoke_v3`: real retrieval works; previous final-output schema produced citation arrays without inline citations, so output guard refuses those answers. Kept as dev integration failure evidence.
- `agent_smoke_v4`: final claim-based schema and renderer: q01 answered with citation, BCrypt absence question refused. Usage kept separately from main run.
- `agent_dev_v1`: complete main run with final code, 51/51 successful queries (17 per Dense/BM25/Hybrid); each outputs 15 cited answers and 2 refusals. Raw answer/citation correctness still requires review. Two Dense errors documented in `docs/AGENT_DEV_REVIEW.md`. Main-run model/embedding token usage is in summary; smoke usage is additional. No test evaluated.

The earlier statement about no agent benchmark describes the retrieval-only stage. The agent runs above were explicitly authorized later, including sending dev context to OpenAI; benchmark gold/test were not sent.

## Reviewed improvement experiments and pipeline freeze

- All 51 outputs in `agent_dev_v1` now have explicit answer/context/citation/abstention reviews and reasons in `reviews.json`.
- `agent_dev_dense_wide`: 17/17 completed, Dense k6/7000; context improves to 15/15 but two wrong-source citations lower grounded score to 26/30.
- `agent_dev_dense_wide_quotes`: 17/17 completed, quote checks on k6/7000; 25/30 grounded, two false refusals and one incomplete answer. Quote membership does not guarantee semantic correctness.
- Every new output reviewed (85 total across 5 configs), with per-citation reasons and original-PDF source checks. Each label includes the source comparison and a written reason.
- `configs/selected_pipeline.json` selects original BM25 k3/4000/max2 searches. `configs/pipeline_freeze.json` records hashes before any test evaluation. Full comparison: `results/dev_comparison.json` and `docs/DEV_SELECTION.md`. Test remains unevaluated.

## Frozen test evaluation (subsequent authorized work)

`agent_test_v1` is the first and only reported test run: fixed Dense baseline and selected BM25, all 7 frozen test inputs per method. User explicitly authorized sending test questions/queries/context to OpenAI; no gold or expected answers sent. Core pipeline and benchmark hashes verified before and after, unchanged; no test-driven tuning.

All 14 outputs have written answer/context/citation/abstention reviews. Each method: 5 fully grounded answers, 2 correct refusals, no false refusal or system error. Dense original-query Hit@1=4/5, BM25=5/5, both Hit@3/context=5/5. Full details: `docs/TEST_RESULTS.md`. Each label includes the source comparison and a written reason.
