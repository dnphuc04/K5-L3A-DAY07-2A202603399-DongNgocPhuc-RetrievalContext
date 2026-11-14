# Benchmark Day 7 - frozen before retrieval experiments

## Scope and split

- Corpus: snapshot C Day 6, 65 paragraph chunks, 33 selected physical PDF pages, same embedding/index for all methods.
- Dev: reuse 15 Day 6 answerable questions plus 2 new unanswerable questions (17 total).
- Test: 5 new answerable questions plus 2 new unanswerable questions (7 total). None reuses the answer sought by Day 6 dev/test; semantic overlap was reviewed with AI assistance. Some topics/pages overlap because this is a single-document benchmark.
- New test topics: JSON content header, authentication versus authorization, Entity storage types, rename-timetable endpoint, tools/permissions required for file reading.
- New test was authored with access to corpus and old benchmark, before Day 7 retrieval implementation/runs. This is held out from tuning, not independently authored or blind to the benchmark author.

## Input isolation

`dev.inputs.json` and `test.inputs.json` contain only id/question/optional user scope filter. Model/retriever runners must load only these inputs and corpus. `*.gold.json`, absence notes, validator output and old traces must never be supplied to model, query rewriting, filters, context selection or ranking.

Do not load test inputs during dev tuning. Freeze hashes detect edits, not access. If test results inform modifications, create a new test and record the contamination. Do not copy old test scores into Day 7 metrics.

## Evidence and absence review

Gold alternatives are OR: one complete gold span at the correct source/page is sufficient. Current questions each require a single complete chunk, not multi-hop. Whitespace and Unicode NFC normalization are allowed; ranking remains independent of gold. Semantic equivalents require recorded review against the PDF, not only string equality.

The five new answerable questions were checked visually on original PDF pages 18, 25, 49, 52 and 33. For the endpoint question, the PUT/matching route/function occupy the same row of Table 2.5-1. All 20 answerable gold spans must also match original PDF extraction and a snapshot C chunk. Inherited dev labels remain AI-assisted; this work does not claim an independent human review.

Unanswerable means absent from the 33 indexed pages, not necessarily every image or excluded page of the 84-page PDF. Questions explicitly state this scope. All selected page text was read with AI assistance and relevant sections rechecked: BCrypt cost (26), JWT lifetime (26-27), Excel upload size (49/53), measured concurrency (67/79). The report discusses these topics but supplies no requested numeric configuration or load result. Keyword scans of all 33 PDF pages are saved as supporting evidence; zero keyword hits alone never establishes absence. Do not answer from library defaults or outside knowledge. No OCR/independent human absence audit is claimed.

## Scoring and selection policy

- Retrieval: Hit@1, Evidence Hit@3, same cutoff, source/page/support definition and 15 answerable dev queries; exclude unanswerable queries from denominator. Also report query-original ranking separately from rewritten/multi-hop pipeline ranking.
- Context Evidence Rate: sufficient valid evidence in final context / answerable questions. Record budget/unit, candidate count and final size. Review baseline and selected config on all 5 answerable test questions: 0 absent, 1 incomplete conditions/source, 2 sufficient evidence/source.
- Answer grades: 0 wrong/unsupported/refused answerable question, 1 partially correct, 2 correct and complete. Compare with expected answer and grading notes; record reasons. All five test answerable questions and both unanswerable questions are reviewed for baseline and selected configuration.
- Citation validity: citation in context AND supports associated claim / all citations. No citations: 0/0 not applicable. Also report answered-query citation coverage.
- Abstention: correct refusal without invented facts / unanswerable questions, plus false refusal / answerable questions.
- Tool use: successful queries with retrieval / successful queries; distribution of calls. Report system errors separately, do not silently drop them; show successful/attempted coverage alongside quality metrics.
- Report n/N and percentage, grade distributions and mean /2, latency, tokens and actual/estimated cost with units and provenance. Never invent cost when unavailable.

Selection policy fixed now: rank dev configs by mean grounded-answer grade, then Context Evidence Rate, citation validity, correct abstentions, Evidence Hit@3, then lower median end-to-end latency, then lower measured cost where available. N/A citation/cost does not win a tie; if unresolved, prefer fewer model calls, then baseline. Explicitly inspect false abstentions and errors before accepting any config. Keep corpus/model/prompt/scoring consistent; record all changes. At least two improvement configs and two dev error analyses are required. Freeze the selected pipeline config separately after dev and before running baseline/selected on test.

## Reproduce

Use the Day 6 venv Python (pypdf installed):

```powershell
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/validate_benchmark.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering'
```

`freeze.json` records hashes of inputs, gold, benchmark policy and corpus provenance. `--freeze` is for the initial freeze only and refuses to replace an existing freeze. No retrieval/model API calls occur during validation.
