# Retrieval Day 7

> **Phạm vi thời điểm:** Tài liệu này ghi giai đoạn retrieval-only trên dev. Agent và test đã hoàn tất; xem [kết quả test](TEST_RESULTS.md) và [bản nộp cuối](../SUBMISSION_FINAL.md). Các câu “chưa chạy test/chưa chọn agent” bên dưới mô tả thời điểm thí nghiệm retrieval, không phải trạng thái hiện tại.

## Implementation

`src/retrieval.py` implements a shared `search(query, filters=None, top_k=3)` interface. All methods use the same 65 chunks of Day 6 strategy C and the same explicit chapter filters from frozen dev inputs. Original queries are used unchanged; no gold-derived filters, expansion or rewriting.

- Dense: reuse the real Day 6 embedding adapter (`text-embedding-3-small`, 1536 dimensions, no prefix) and read-only pgvector exact cosine search. Check database snapshot against frozen chunk text/metadata and dimensions before running.
- BM25: k1=1.5, b=0.75, positive Robertson IDF `log(1+(N-df+0.5)/(df+0.5))`. NFC normalization, casefold, Unicode word tokens, unique query terms, no stopword removal or Vietnamese word segmentation. IDF/average length use the whole corpus; filter only restricts eligible results. Return positive-score matches only; ties resolve by ID.
- Hybrid: equal-weight RRF `sum(1/(60+rank))`, up to 20 candidates per component, then output top-3. No addition of unnormalized lexical/dense scores. Trace each returned chunk's component ranks/scores. A failed component causes an explicit query error, not silent fallback.
- Context: ranked whole chunks, deduplication, 4000-character budget including ID/source/page headers and separators; skip blocks that do not fit. This is a fixed single-search context comparison, not an agent final context yet.

## Run dev only

```powershell
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/benchmark_retrieval_dev.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output results/retrieval_dev_new
```

Use an unused output directory; existing results are never overwritten. Database/key are read from environment or Day 6 dotenv; not printed. Only dev questions are sent for embedding. Previously cached dev vectors are copied into ignored `data/local/query_cache`, so Day 6 is not changed. The script checks frozen test file hashes without parsing test questions or gold. Retrieval completes before dev gold is loaded for scoring.

Outputs: raw retrieval traces (no gold labels), separate evaluated traces, summary with n/N/rate, errors, latency, configuration/code/input hashes and new API usage. Labels use strict normalized full gold span + source/page; equivalent semantic evidence requires additional recorded review. Unanswerable queries are run but excluded from retrieval denominators. Finding related chunks does not establish answerability or correct abstention.

## Dev results and run history

Run `results/retrieval_dev_v1` completed all 15 answerable queries for each method. Dense/Hybrid each had two embedding errors on the new unanswerable queries under network restrictions; BM25 completed 17/17. Keep this failed-run evidence rather than reporting full success.

After explicit user permission to send the two new BCrypt/JWT queries to OpenAI embeddings, run v2 created the missing query vectors (2 API requests, 94 prompt tokens recorded in its partial trace) but failed while writing a trace file on Windows. It contains 36 completed trace records and no summary; it is not the final benchmark. Run `results/retrieval_dev_v3` completed 51/51 retrieval attempts (17 per method), zero errors. V3 reused all query vectors from cache, therefore its own new API usage is zero. Do not interpret this as zero total API usage for preparing the benchmark; monetary cost remains unknown.

The table below is unchanged between v1 and the complete v3 run, because the additional queries are unanswerable and excluded from retrieval denominators. Authoritative complete results: `results/retrieval_dev_v3/summary.json`; raw and evaluated traces are alongside it.

| Method | Hit@1 | Evidence Hit@3 | Context Evidence Rate (single-search) |
|---|---|---|---|
| Dense | 10/15 (66.7%) | 14/15 (93.3%) | 14/15 (93.3%) |
| BM25 | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| Hybrid RRF | 13/15 (86.7%) | 15/15 (100%) | 15/15 (100%) |

V3 median retrieval latency: Dense 40.50 ms, BM25 0.82 ms, Hybrid 47.48 ms. All query embeddings were cached; timings include database access for Dense/Hybrid and are a single sequential run, not a latency benchmark across machines or cold starts.

These are retrieval scores on a small, same-document dev set, not agent answer scores or evidence of generalization. BM25 currently matches the wording particularly well. Do not select the final agent configuration from these numbers alone; the frozen policy prioritizes grounded answers, which have not been measured yet.

## Dev error analysis

1. **q13, tie between repeated course attempts.** Dense top-1 is an image caption on page 56 referring to choosing the highest score; top-2 on page 49 describes CPA selection generally. Neither contains the required tie-break by newer academic year/semester, so this is not merely an exact-string false negative. The complete rule chunk is BM25 rank 1 and Hybrid rank 2; Hybrid recovers strict Hit@3/context from 0 to 1 for this query. Hypothesis: lexical terms retrieve the detailed rule while dense favors a short semantically similar caption. A later context/rerank experiment can prefer complete rule-bearing paragraphs; no index/gold modification is made here.
2. **q08, JWT header.** Dense top-1 on page 26 explains JWT signatures but omits the requested header/format; correct page-27 chunk is rank 2. BM25 and Hybrid promote it to rank 1. Hypothesis: semantic topic similarity alone does not distinguish introductory JWT text from the exact transport rule.
3. **q14, HTML filenames.** Dense ranks a generic project description (page 14) above the precise five-filename list (page 57). BM25 puts the list first. Hybrid ties the two candidates on RRF score and the deterministic ID tie-break puts the generic description first, so Hybrid does not improve this case. A weighted fusion/rerank is a plausible later dev experiment, not yet implemented or selected.

## Timing/cost limits and current scope

Single sequential run with dense before hybrid and a shared query cache. Do not claim hybrid is intrinsically faster from these latencies; it can reuse vectors created/loaded earlier. BM25 has no model API calls, but CPU time is still recorded. Report actual token/request counters; leave monetary cost unknown until billing or a documented pricing calculation is available.

No agent model calls, generated answers, citation support or abstention scores are included. This retrieval-only run preceded agent/test evaluation; the frozen test was subsequently evaluated with the selected pipeline (see TEST_RESULTS.md).
