import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from src.model import OpenAIChatModel, ModelError


class ModelAdapterTests(unittest.TestCase):
    def test_quote_schema_is_opt_in_and_does_not_mutate_baseline(self):
        quoted = OpenAIChatModel("secret", require_quotes=True)
        baseline = OpenAIChatModel("secret")
        get_claim = lambda m: m.final_format["json_schema"]["schema"]["properties"]["claims"]["items"]
        self.assertIn("quotes", get_claim(quoted)["required"])
        self.assertNotIn("quotes", get_claim(baseline)["properties"])

    def test_payload_tool_choice_usage_and_store_disabled(self):
        body = {"id": "resp1", "model": "snapshot", "choices": [{"message": {"role": "assistant", "content": "{}"},
                "finish_reason": "stop"}], "usage": {"prompt_tokens": 123, "completion_tokens": 45}}
        for searches, expected in ((0, {"type": "function", "function": {"name": "search"}}), (1, "auto"), (2, "none")):
            with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(body).encode())) as http:
                result = OpenAIChatModel("secret").complete([{"role": "user", "content": "q"}], search_count=searches, max_searches=2)
                payload = json.loads(http.call_args.args[0].data)
                self.assertEqual(payload["tool_choice"], expected)
                self.assertFalse(payload["store"])
                self.assertFalse(payload["parallel_tool_calls"])
                self.assertTrue(payload["tools"][0]["function"]["strict"])
                self.assertEqual(result["usage"]["prompt_tokens"], 123)

    def test_http_error_does_not_expose_raw_provider_body(self):
        with patch("urllib.request.urlopen", side_effect=HTTPError("url", 401, "secret leak", {}, None)):
            with self.assertRaisesRegex(ModelError, "^OpenAI chat HTTP 401$"):
                OpenAIChatModel("secret").complete([], search_count=0, max_searches=2)


if __name__ == "__main__": unittest.main()
