"""Bounded tool-calling agent; no benchmark labels accepted by this interface."""
import json
import re
import time
import unicodedata
from .model import SYSTEM_PROMPT, ModelError
from .retrieval import pack_context, validate_search

ABSTENTION = "Không đủ bằng chứng trong dữ liệu truy xuất để trả lời câu hỏi này."


def run_agent(question, model, retriever, *, filters=None, max_searches=3, top_k=3, budget=4000, require_quotes=False):
    validate_search(question, filters, top_k)
    if type(max_searches) is not int or max_searches < 1 or type(budget) is not int or budget < 1:
        raise ValueError("Invalid agent limits")
    start = time.perf_counter()
    events, candidates, calls = [], [], []
    context, ids, searches = "", [], 0
    messages = [{"role": "system", "content": getattr(model, "system_prompt", SYSTEM_PROMPT)},
                {"role": "user", "content": json.dumps({"question": question, "scope_filter": filters,
                    "max_searches": max_searches}, ensure_ascii=False)}]

    def finish(status, answer, citations, reason):
        events.append({"event": "finish", "reason": reason})
        return {"status": status, "answer": answer, "citations": citations, "events": events,
                "model_calls": calls, "search_count": searches, "model_call_count": len(calls),
                "context": context, "context_ids": ids, "elapsed_ms": (time.perf_counter() - start) * 1000}

    try:
        for _ in range(max_searches + 1):
            reply = model.complete(messages, search_count=searches, max_searches=max_searches)
            calls.append({"request_messages": messages, **reply})
            message = reply["message"]
            if message.get("refusal"):
                return finish("abstain", ABSTENTION, [], "provider_refusal")
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                if reply["finish_reason"] not in ("tool_calls", "stop") or len(tool_calls) != 1 or searches >= max_searches:
                    raise ValueError("Invalid or excessive tool calls")
                call = tool_calls[0]
                if call["type"] != "function" or call["function"]["name"] != "search":
                    raise ValueError("Unsupported tool")
                args = json.loads(call["function"]["arguments"])
                if set(args) != {"query"}:
                    raise ValueError("Unexpected tool arguments")
                requested_query = args["query"]
                # First retrieval is always the original query for comparable baselines.
                query = question if searches == 0 else requested_query
                validate_search(requested_query, filters, top_k)
                search_start = time.perf_counter()
                results = retriever.search(query, filters=filters, top_k=top_k)
                if len(results) > top_k or len({r["id"] for r in results}) != len(results):
                    raise ValueError("Invalid retriever result IDs/count")
                searches += 1
                # Same earlier-first cumulative policy for all configs; no gold-based prioritization.
                candidates.extend(results)
                context, ids = pack_context(candidates, budget)
                events.append({"event": "search", "tool": "search", "tool_call_id": call["id"],
                    "requested_query": requested_query, "query": query, "filter": filters,
                    "top_k": top_k, "results": results, "context": context, "context_ids": ids,
                    "elapsed_ms": (time.perf_counter() - search_start) * 1000})
                # Rebuild bounded history: only latest cumulative context is sent, older raw results are trace-only.
                messages = messages[:2] + [{"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls},
                    {"role": "tool", "tool_call_id": call["id"], "content": json.dumps({
                        "context": context, "context_ids": ids, "searches_used": searches,
                        "searches_remaining": max_searches - searches,
                        "previous_queries": [e["query"] for e in events if e["event"] == "search"]}, ensure_ascii=False)}]
                continue
            if reply["finish_reason"] != "stop" or searches == 0:
                raise ValueError("Incomplete answer or no search")
            answer = json.loads(message["content"])
            if set(answer) != {"status", "claims"} or answer["status"] not in ("answered", "abstain") or not isinstance(answer["claims"], list):
                raise ValueError("Invalid final schema")
            if answer["status"] == "abstain":
                return finish("abstain", ABSTENTION, [], "model_insufficient_evidence")
            blocks, citations = [], []
            if not answer["claims"]:
                return finish("abstain", ABSTENTION, [], "empty_claims")
            for claim in answer["claims"]:
                if set(claim) != ({"text", "citations", "quotes"} if require_quotes else {"text", "citations"}):
                    raise ValueError("Invalid claim schema")
                text, refs = claim["text"], claim["citations"]
                if not isinstance(text, str) or not isinstance(refs, list) or any(not isinstance(c, str) for c in refs):
                    raise ValueError("Invalid claim/citations")
                if not text.strip() or not refs or any(c not in ids for c in refs) or len(set(refs)) != len(refs):
                    return finish("abstain", ABSTENTION, [], "invalid_or_missing_citations")
                if require_quotes:
                    normalize = lambda s: " ".join(unicodedata.normalize("NFC", s).split())
                    current = {c["id"]: c for c in candidates if c["id"] in ids}
                    quotes = claim["quotes"]
                    valid = isinstance(quotes, list) and bool(quotes)
                    quote_ids = set()
                    if valid:
                        for quote in quotes:
                            if (not isinstance(quote, dict) or set(quote) != {"chunk_id", "text"}
                                    or not isinstance(quote["chunk_id"], str) or quote["chunk_id"] not in refs
                                    or not isinstance(quote["text"], str) or not normalize(quote["text"])
                                    or normalize(quote["text"]) not in normalize(current[quote["chunk_id"]]["text"])):
                                valid = False
                                break
                            quote_ids.add(quote["chunk_id"])
                    if not valid or quote_ids != set(refs):
                        return finish("abstain", ABSTENTION, [], "invalid_or_missing_supporting_quote")
                blocks.append(text.strip() + " " + " ".join(f"[{c}]" for c in refs))
                citations.extend(c for c in refs if c not in citations)
            text = "\n".join(blocks)
            inline = re.findall(r"\[([^\[\]\n]+)\]", text)
            if (not text.strip() or not citations or len(set(citations)) != len(citations)
                    or set(inline) != set(citations) or any(c not in ids for c in citations)):
                return finish("abstain", ABSTENTION, [], "invalid_or_missing_citations")
            return finish("answered", text, citations, "model_answer")
        return finish("abstain", ABSTENTION, [], "search_limit")
    except Exception as exc:
        events.append({"event": "error", "error_type": type(exc).__name__,
                       "error_message": str(exc) if isinstance(exc, ModelError) else "Agent or retrieval error; inspect stage and trace"})
        return finish("error", "", [], "system_error")
