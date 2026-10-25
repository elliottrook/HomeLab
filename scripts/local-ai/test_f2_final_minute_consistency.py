import unittest

import f2_observer_runner_candidate as observer
import f2_preflight_fixed_wrapper as wrapper


class F2FinalMinuteConsistencyTests(unittest.TestCase):
    def test_installed_path_dependency_closure_uses_corrected_sources(self):
        observer_path = "/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py"
        producer_path = "/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py"
        self.assertEqual(wrapper.EXPECTED_PINS[observer_path],
                         "3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858")
        self.assertEqual(wrapper.EXPECTED_PINS[producer_path],
                         "5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf")
        self.assertEqual(observer.PRODUCER_SHA256,
                         "5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf")


if __name__ == "__main__":
    unittest.main()
