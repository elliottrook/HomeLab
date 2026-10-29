import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from lab_hours_doctor import diagnose
from lab_hours_reservations import ReservationStore

def okay(command, timeout):
    output='{"state":"ready"}' if command[0].endswith('local-ai-lease') else (' ' if command[0]=='ss' else 'active')
    return SimpleNamespace(returncode=0,stdout=output)

class DoctorTests(unittest.TestCase):
    def test_healthy_idle(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=diagnose(ReservationStore(Path(tmp),clock=lambda:1000),now=1000,runner=okay)
            self.assertEqual(value["state"],"healthy")
    def test_missed_reservation_is_unhealthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ReservationStore(Path(tmp),clock=lambda:1000)
            store.reserve(booking_id="test-booking-01",owner="codex-owner-01",
                workload="accepted-9b-direct-control-smoke-v1",start_epoch=1100,end_epoch=1700)
            value=diagnose(store,now=1300,runner=okay)
            self.assertIn("MISSED_RESERVATION",value["codes"])

if __name__=="__main__": unittest.main()
