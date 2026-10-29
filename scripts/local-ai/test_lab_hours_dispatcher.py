import unittest
from unittest.mock import Mock
from lab_hours_dispatcher import dispatch

class Store:
    def due(self): return [{"booking_id":"test-booking-01"}]

class DispatcherTests(unittest.TestCase):
    def test_dispatches_only_due_booking_to_fixed_runner(self):
        runner=Mock(); runner.return_value=Mock(returncode=0)
        value=dispatch(Store(),runner=runner)
        self.assertEqual(value["started"],["test-booking-01"])
        command=runner.call_args.args[0]
        self.assertIn("--unit=aster-lab-hours-booking-test-booking-01.service",command)
        self.assertEqual(command[-2:],("--booking-id","test-booking-01"))

if __name__=="__main__": unittest.main()
