import unittest

from ifba_ai.model_registry import MODELS, request_options


class ModelRegistryTests(unittest.TestCase):
    def test_official_models_have_model_specific_reasoning_options(self):
        self.assertEqual(len(MODELS), 5)
        self.assertEqual(request_options("deepseek-ai/deepseek-v4.1-flash", "medium"),
                         {"reasoning_effort": 60})
        self.assertEqual(request_options("minimaxai/minimax-m3.1-flash", "medium"),
                         {"reasoning_effort": "medium"})
        self.assertEqual(request_options("nvidia/nemotron-3.5-super-vl-120b-a12b", "high"),
                         {"reasoning_effort": "high"})
        self.assertEqual(request_options("mistralai/mistral-large-4-1t-a52b", "off"),
                         {"reasoning_effort": "none"})
        self.assertEqual(request_options("moonshotai/kimi-k3.1-pro", "low"),
                         {"reasoning_effort": "low"})

    def test_reasoning_off_omits_optional_parameter_when_model_does_not_document_none(self):
        self.assertEqual(request_options("moonshotai/kimi-k3.1-pro", "off"), {})

    def test_unknown_model_and_reasoning_level_are_rejected(self):
        with self.assertRaises(ValueError):
            request_options("unlisted/model", "off")
        with self.assertRaises(ValueError):
            request_options("moonshotai/kimi-k3.1-pro", "xhigh")


if __name__ == "__main__":
    unittest.main()
