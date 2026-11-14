import json
import unittest
from src.agent import run_agent, ABSTENTION
from src.model import ModelError


def tool(query="question", cid="call1"):
    return {"message": {"role": "assistant", "content": None, "tool_calls": [{"id": cid, "type": "function",
        "function": {"name": "search", "arguments": json.dumps({"query": query})}}]},
        "finish_reason": "tool_calls", "usage": {}}


def final(status="answered", text="Answer [a]", citations=None):
    return {"message": {"role": "assistant", "content": json.dumps({"status": status,
        "claims": [{"text": text, "citations": ["a"] if citations is None else citations}]})}, "finish_reason": "stop", "usage": {}}


class FakeModel:
    def __init__(self, actions): self.actions, self.requests = iter(actions), []
    def complete(self, messages, **limits):
        self.requests.append((messages, limits))
        action = next(self.actions)
        if isinstance(action, Exception): raise action
        return action


class Retriever:
    def search(self, query, **kwargs):
        self.last = (query, kwargs)
        return [dict(id="a", text="Supporting evidence", source="doc.pdf", page=1, source_id="doc", metadata={}, score=1)]


class RealAgentLoopTests(unittest.TestCase):
    def test_quote_guard_requires_real_span_from_each_cited_chunk(self):
        for quote, expected in (("Supporting evidence", "answered"), ("Supporting\n evidence", "answered"), ("Invented evidence", "abstain")):
            reply = final(text="Supported fact")
            data = json.loads(reply["message"]["content"])
            data["claims"][0]["quotes"] = [{"chunk_id": "a", "text": quote}]
            reply["message"]["content"] = json.dumps(data)
            row = run_agent("q", FakeModel([tool(), reply]), Retriever(), require_quotes=True)
            self.assertEqual(row["status"], expected)

    def test_provider_stop_with_valid_tool_call_is_executed(self):
        action = tool()
        action["finish_reason"] = "stop"
        row = run_agent("q", FakeModel([action, final()]), Retriever())
        self.assertEqual(row["status"], "answered")

    def test_real_protocol_search_then_answer_and_trace(self):
        model, retriever = FakeModel([tool("changed"), final()]), Retriever()
        row = run_agent("question", model, retriever, filters={"chapter": "chapter_1"})
        self.assertEqual(row["status"], "answered")
        self.assertEqual(retriever.last[0], "question")
        self.assertEqual(retriever.last[1]["filters"], {"chapter": "chapter_1"})
        self.assertEqual(row["search_count"], 1)
        self.assertIn("Supporting evidence", model.requests[1][0][-1]["content"])

    def test_rejects_unknown_or_unlisted_inline_citation(self):
        for text, citations in (("Answer [unknown]", ["unknown"]), ("Answer [a] [invented]", ["a"]), ("Answer", [])):
            row = run_agent("q", FakeModel([tool(), final(text=text, citations=citations)]), Retriever())
            self.assertEqual(row["status"], "abstain")

    def test_renderer_attaches_model_selected_citations(self):
        row = run_agent("q", FakeModel([tool(), final(text="Supported fact")]), Retriever())
        self.assertEqual(row["answer"], "Supported fact [a]")

    def test_abstention_never_emits_speculative_raw_answer(self):
        row = run_agent("q", FakeModel([tool(), final("abstain", "Maybe 60 minutes", [])]), Retriever())
        self.assertEqual(row["answer"], ABSTENTION)
        self.assertEqual(row["citations"], [])

    def test_empty_context_and_budget(self):
        row = run_agent("q", FakeModel([tool(), final()]), Retriever(), budget=1)
        self.assertEqual(row["status"], "abstain")
        self.assertEqual(row["context"], "")

    def test_error_is_not_abstention(self):
        row = run_agent("q", FakeModel([ModelError("OpenAI chat HTTP 401")]), Retriever())
        self.assertEqual(row["status"], "error")
        self.assertEqual(row["answer"], "")

    def test_search_limit_and_bounded_context_messages(self):
        model = FakeModel([tool(cid="1"), tool(cid="2"), final()])
        row = run_agent("q", model, Retriever(), max_searches=2)
        self.assertEqual(row["status"], "answered")
        self.assertEqual(row["context_ids"], ["a"])
        self.assertEqual(len(model.requests[-1][0]), 4)
        self.assertEqual(model.requests[-1][1]["search_count"], 2)
        row = run_agent("q", FakeModel([tool(), tool()]), Retriever(), max_searches=1)
        self.assertEqual(row["status"], "error")


if __name__ == "__main__": unittest.main()
