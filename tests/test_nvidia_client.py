import io
import json
import base64
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request

from ifba_ai.nvidia import (
    API_URL,
    CancellationToken,
    GenerationCancelled,
    MAX_RESPONSE_BYTES,
    MAX_SSE_LINE_BYTES,
    MULTIMODAL_MODEL,
    MODEL_ENDPOINTS,
    NvidiaClient,
    NvidiaError,
    RejectRedirectHandler,
    bounded_context,
    open_without_redirects,
)
from ifba_ai.model_registry import DEFAULT_MODEL


class FakeResponse:
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        return iter(self.chunks)

    def close(self):
        self.closed = True


class ReadableFakeResponse(FakeResponse):
    def __init__(self, chunks):
        super().__init__(chunks)
        self.stream = io.BytesIO(b"".join(chunks))
        self.maximum_read_size = 0

    def readline(self, size=-1):
        self.maximum_read_size = max(self.maximum_read_size, size)
        return self.stream.readline(size)


class ClientTests(unittest.TestCase):
    def test_authenticated_client_refuses_redirects(self):
        self.assertIs(NvidiaClient().opener, open_without_redirects)
        request = Request(API_URL, data=b"{}", method="POST", headers={"Authorization": "Bearer test-secret"})
        with self.assertRaises(HTTPError) as raised:
            RejectRedirectHandler().redirect_request(
                request, io.BytesIO(b""), 302, "Found", {}, "https://attacker.invalid/collect"
            )
        self.assertEqual(raised.exception.code, 302)
        self.assertNotIn("attacker.invalid", str(raised.exception))
        self.assertTrue(raised.exception.fp.closed)

    def test_streaming_uses_nvidia_endpoint_and_never_logs_key(self):
        response = ReadableFakeResponse([
            b'data: {"choices":[{"delta":{"content":"Ola"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" mundo"}}]}\n\n',
            b'data: [DONE]\n\n',
        ])
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["auth"] = request.get_header("Authorization")
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode())
            return response

        secret = "test-secret-never-print"
        output = list(NvidiaClient(opener=opener).stream_chat(
            secret, "deepseek-ai/deepseek-v4.1-flash", [{"role": "user", "content": "Oi"}], 256
        ))
        self.assertEqual(output, ["Ola", " mundo"])
        self.assertEqual(captured["url"], API_URL)
        self.assertEqual(captured["auth"], "Bearer " + secret)
        self.assertEqual(captured["timeout"], 45)
        self.assertTrue(captured["body"]["stream"])
        self.assertNotIn(secret, repr(captured["body"]))
        self.assertTrue(response.closed)

    def test_oversized_sse_line_is_rejected_with_bounded_reads(self):
        response = ReadableFakeResponse([b"data: " + b"x" * MAX_SSE_LINE_BYTES])
        client = NvidiaClient(opener=lambda *_args, **_kwargs: response)

        with self.assertRaisesRegex(NvidiaError, "excedeu o limite"):
            list(client.stream_chat("secret", DEFAULT_MODEL, [], 100))

        self.assertEqual(response.maximum_read_size, MAX_SSE_LINE_BYTES + 1)
        self.assertTrue(response.closed)

    def test_oversized_line_is_also_rejected_from_iterable_response_objects(self):
        response = FakeResponse([b"data: " + b"x" * (MAX_SSE_LINE_BYTES + 1)])
        client = NvidiaClient(opener=lambda *_args, **_kwargs: response)

        with self.assertRaisesRegex(NvidiaError, "excedeu o limite"):
            list(client.stream_chat("secret", DEFAULT_MODEL, [], 100))

        self.assertTrue(response.closed)

    def test_oversized_total_response_is_rejected(self):
        delta_bytes = 100 * 1024
        event = (b'data: {"choices":[{"delta":{"content":"'
                 + b"a" * delta_bytes + b'"}}]}\n')
        lines = [event] * (MAX_RESPONSE_BYTES // delta_bytes + 2)
        response = ReadableFakeResponse(lines)
        client = NvidiaClient(opener=lambda *_args, **_kwargs: response)

        with self.assertRaisesRegex(NvidiaError, "excedeu o limite"):
            list(client.stream_chat("secret", DEFAULT_MODEL, [], 32768))

        self.assertTrue(response.closed)

    def test_reasoning_deltas_are_never_exposed_as_chat_text(self):
        response = FakeResponse([
            b'data: {"choices":[{"delta":{"reasoning_content":"private thought","content":"Public answer"}}]}\n\n',
            b'data: [DONE]\n\n',
        ])
        output = list(NvidiaClient(opener=lambda *_a, **_k: response).stream_chat(
            "secret", DEFAULT_MODEL, [{"role": "user", "content": "Oi"}], 256
        ))
        self.assertEqual(output, ["Public answer"])
        self.assertNotIn("private thought", "".join(output))

    def test_unsupported_reasoning_parameter_retries_once_without_it(self):
        calls = []
        response = FakeResponse([b'data: {"choices":[{"delta":{"content":"Resposta"}}]}\n', b'data: [DONE]\n'])

        def opener(request, timeout):
            calls.append(json.loads(request.data.decode("utf-8")))
            if len(calls) == 1:
                raise HTTPError(API_URL, 400, "invalid", {}, io.BytesIO(b"Unsupported reasoning_effort"))
            return response

        output = list(NvidiaClient(opener=opener).stream_chat(
            "secret", DEFAULT_MODEL, [{"role": "user", "content": "Oi"}], 256,
            reasoning_level="high",
        ))
        self.assertEqual(output, ["Resposta"])
        self.assertIn("reasoning_effort", calls[0])
        self.assertNotIn("reasoning_effort", calls[1])
        self.assertIn("apresente conclusões", calls[1]["messages"][0]["content"])
        self.assertEqual(len(calls), 2)

    def test_unauthorized_key_has_safe_error(self):
        secret = "a-secret-test-value"

        def opener(*_args, **_kwargs):
            raise HTTPError(API_URL, 401, "unauthorized", {}, io.BytesIO(secret.encode()))

        with self.assertRaisesRegex(NvidiaError, "recusou a chave") as raised:
            list(NvidiaClient(opener=opener, retries=0).stream_chat(secret, DEFAULT_MODEL, [], 100))
        self.assertNotIn(secret, str(raised.exception))

    def test_billing_and_model_access_errors_are_explained(self):
        for code, phrase in ((402, "saldo disponível"), (403, "permissão")):
            def opener(*_args, **_kwargs):
                raise HTTPError(API_URL, code, "denied", {}, io.BytesIO(b"private response body"))
            with self.subTest(status=code), self.assertRaisesRegex(NvidiaError, phrase):
                list(NvidiaClient(opener=opener, retries=0).stream_chat("secret", DEFAULT_MODEL, [], 100))

    def test_rate_limit_retries_are_bounded_and_honor_retry_after(self):
        calls = []

        def opener(*_args, **_kwargs):
            calls.append(1)
            raise HTTPError(API_URL, 429, "rate", {"Retry-After": "1"}, io.BytesIO())

        client = NvidiaClient(opener=opener, retries=2)
        # HTTP retry backoff uses the token's wait; keep the test immediate.
        class ImmediateToken:
            def is_set(self):
                return False

            def wait(self, _delay):
                return False

        with self.assertRaisesRegex(NvidiaError, "Limite de uso"):
            list(client.stream_chat("secret", DEFAULT_MODEL, [], 100, ImmediateToken()))
        self.assertEqual(len(calls), 3)

    def test_network_error_retries_then_reports_unavailable(self):
        calls = []

        def opener(*_args, **_kwargs):
            calls.append(1)
            raise URLError("offline")

        client = NvidiaClient(opener=opener, retries=1)
        class ImmediateToken:
            def is_set(self):
                return False

            def wait(self, _delay):
                return False
        with self.assertRaisesRegex(NvidiaError, "Verifique a internet"):
            list(client.stream_chat("secret", DEFAULT_MODEL, [], 100, ImmediateToken()))
        self.assertEqual(len(calls), 2)

    def test_invalid_model_and_missing_key_are_rejected_before_network(self):
        calls = []
        client = NvidiaClient(opener=lambda *_a, **_k: calls.append(1))
        with self.assertRaises(NvidiaError):
            list(client.stream_chat("secret", "bad model", [], 100))
        with self.assertRaises(NvidiaError):
            list(client.stream_chat(None, DEFAULT_MODEL, [], 100))
        self.assertEqual(calls, [])

    def test_context_is_bounded_and_keeps_recent_messages(self):
        history = [
            {"role": "user", "content": "a" * 100},
            {"role": "assistant", "content": "b" * 100},
            {"role": "user", "content": "c" * 100},
        ]
        selected = bounded_context(history, max_chars=150)
        self.assertEqual(sum(len(message["content"]) for message in selected), 150)
        self.assertEqual(selected[-1]["role"], "user")

    def test_cancel_token_closes_attached_response(self):
        response = FakeResponse([])
        token = CancellationToken()
        token.attach(response)
        token.cancel()
        self.assertTrue(response.closed)
        self.assertTrue(token.is_set())
        with self.assertRaises(GenerationCancelled):
            list(NvidiaClient(opener=lambda *_a, **_k: response).stream_chat(
                "secret", DEFAULT_MODEL, [], 100, token
            ))

    def test_documented_multimodal_model_receives_inline_user_image(self):
        response = FakeResponse([b'data: [DONE]\n'])
        captured = {}
        image = base64.b64encode(b"fake-jpeg-data").decode("ascii")

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return response

        context = {"application": "Eclipse", "controls": [{"id": "control-1", "role": "button",
                                                               "name": "Create Class"}]}
        with self.assertRaisesRegex(NvidiaError, "sem conteúdo"):
            list(NvidiaClient(opener=opener).stream_chat(
                "secret", MULTIMODAL_MODEL,
                [{"role": "user", "content": "Onde crio uma classe?"}], 100,
                image_data_url="data:image/jpeg;base64," + image, visual_context=context,
            ))
        self.assertEqual(captured["url"], API_URL)
        user_message = captured["payload"]["messages"][-1]
        self.assertEqual(user_message["content"][0]["text"], "Onde crio uma classe?")
        self.assertEqual(user_message["content"][1]["image_url"]["url"], "data:image/jpeg;base64," + image)
        self.assertIn("conteúdo não confiável", captured["payload"]["messages"][0]["content"].lower())

    def test_screenshot_is_rejected_for_text_model_and_when_too_large(self):
        calls = []
        client = NvidiaClient(opener=lambda *_a, **_k: calls.append(1))
        context = {"application": "Eclipse", "controls": []}
        with self.assertRaisesRegex(NvidiaError, "modelo NVIDIA listado"):
            list(client.stream_chat("secret", "unlisted-model", [], 100,
                                    image_data_url="data:image/jpeg;base64,YQ==", visual_context=context))
        huge = base64.b64encode(b"x" * (180 * 1024 + 1)).decode("ascii")
        with self.assertRaisesRegex(NvidiaError, "excede o limite"):
            list(client.stream_chat("secret", MULTIMODAL_MODEL, [{"role": "user", "content": "help"}], 100,
                                    image_data_url="data:image/jpeg;base64," + huge, visual_context=context))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
