import unittest

from ifba_ai.visual import VisualContextError, capture_active_window, validate_visual_result


class VisualValidationTests(unittest.TestCase):
    def setUp(self):
        self.context = {"controls": [{"id": "control-1", "name": "New Class"}]}

    def test_accepts_structured_result_only_for_known_control(self):
        result = validate_visual_result(
            '{"explanation":"Abra o menu File.","next_step":"Escolha New Class.",'
            '"target_id":"control-1","confidence":0.82,"needs_confirmation":true}', self.context)
        self.assertEqual(result["target_id"], "control-1")
        self.assertEqual(result["confidence"], 0.82)

    def test_rejects_model_invented_control_and_invalid_confidence(self):
        base = '{"explanation":"ok","next_step":"ok","target_id":"control-999",'
        with self.assertRaises(VisualContextError):
            validate_visual_result(base + '"confidence":0.9,"needs_confirmation":true}', self.context)
        with self.assertRaises(VisualContextError):
            validate_visual_result(
                '{"explanation":"ok","next_step":"ok","target_id":null,'
                '"confidence":4,"needs_confirmation":true}', self.context)

    def test_rejects_invalid_json(self):
        with self.assertRaises(VisualContextError):
            validate_visual_result("not json", self.context)

    def test_blocks_password_or_login_window_before_capture(self):
        for context in ({"title": "Sign in", "has_password_control": False},
                        {"title": "Eclipse", "has_password_control": True}):
            with self.subTest(context=context), self.assertRaisesRegex(VisualContextError, "bloqueada"):
                capture_active_window(context=context, display_factory=lambda: self.fail("must not open display"))


if __name__ == "__main__":
    unittest.main()
