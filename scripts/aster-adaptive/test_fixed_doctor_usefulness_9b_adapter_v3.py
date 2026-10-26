import unittest
from unittest import mock

import fixed_doctor_usefulness_9b_adapter_v3 as adapter


class FixedDoctorUsefulness9BAdapterV3Tests(unittest.TestCase):
    def test_appends_exact_limitation_even_when_model_omits_it(self):
        with mock.patch.object(
            adapter.model_adapter, "invoke", return_value="The named check is warning."
        ):
            answer = adapter.invoke({}, "test-key")
        self.assertTrue(answer.endswith(adapter.LIMITATION))
        self.assertIn("cannot establish a cause or a repair", answer)
        self.assertIn("does not establish broader system health", answer)

    def test_does_not_accept_empty_model_answer(self):
        with mock.patch.object(adapter.model_adapter, "invoke", return_value="  "):
            with self.assertRaisesRegex(ValueError, "empty answer"):
                adapter.invoke({}, "test-key")

    def test_forwards_transport_boundary(self):
        opener = object()
        with mock.patch.object(
            adapter.model_adapter, "invoke", return_value="answer"
        ) as invoke:
            adapter.invoke({"id": "case"}, "test-key", timeout=12, opener=opener)
        invoke.assert_called_once_with(
            {"id": "case"}, "test-key", timeout=12, opener=opener
        )


if __name__ == "__main__":
    unittest.main()
