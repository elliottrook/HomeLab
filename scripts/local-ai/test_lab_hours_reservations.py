import tempfile
import unittest
from pathlib import Path

from lab_hours_reservations import ReservationError, ReservationStore


class ReservationTests(unittest.TestCase):
    def store(self, tmp, now=1000):
        return ReservationStore(Path(tmp), clock=lambda: now)

    def test_reserve_claim_finish_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.store(tmp)
            value = store.reserve(booking_id="test-booking-01", owner="codex-owner-01",
                                  workload="accepted-9b-direct-control-smoke-v1",
                                  start_epoch=1100, end_epoch=1700)
            self.assertEqual(value["state"], "scheduled")
            store.clock = lambda: 1100
            claimed = store.claim("test-booking-01", claimant="dispatcher-01")
            self.assertEqual(claimed["state"], "claimed")
            final = store.finish("test-booking-01", claimant="dispatcher-01",
                                 success=True, result_code="COMPLETE")
            self.assertEqual(final["state"], "complete")

    def test_overlap_including_restore_buffer_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.store(tmp)
            store.reserve(booking_id="test-booking-01", owner="codex-owner-01",
                          workload="accepted-9b-direct-control-smoke-v1",
                          start_epoch=2000, end_epoch=2600)
            with self.assertRaisesRegex(ReservationError, "conflicts"):
                store.reserve(booking_id="test-booking-02", owner="codex-owner-02",
                              workload="accepted-9b-direct-control-smoke-v1",
                              start_epoch=3000, end_epoch=3600)

    def test_unregistered_workload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ReservationError, "not registered"):
                self.store(tmp).reserve(booking_id="test-booking-01",
                    owner="codex-owner-01", workload="arbitrary-shell",
                    start_epoch=1100, end_epoch=1700)

    def test_owner_loss_exercise_is_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=self.store(tmp).reserve(booking_id="test-booking-01",
                owner="codex-owner-01",workload="accepted-9b-owner-loss-exercise-v1",
                start_epoch=1100,end_epoch=1700)
            self.assertEqual(value["state"],"scheduled")

    def test_claim_is_once_and_time_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.store(tmp)
            store.reserve(booking_id="test-booking-01", owner="codex-owner-01",
                          workload="accepted-9b-direct-control-smoke-v1",
                          start_epoch=1100, end_epoch=1700)
            store.clock = lambda: 1100
            store.claim("test-booking-01", claimant="dispatcher-01")
            with self.assertRaises(ReservationError):
                store.claim("test-booking-01", claimant="dispatcher-02")

    def test_completion_keeps_restore_buffer_reserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self.store(tmp)
            store.reserve(booking_id="test-booking-01",owner="codex-owner-01",
                workload="accepted-9b-direct-control-smoke-v1",start_epoch=1100,end_epoch=1700)
            store.clock=lambda:1100; store.claim("test-booking-01",claimant="dispatcher-01")
            store.clock=lambda:1300; store.finish("test-booking-01",claimant="dispatcher-01",
                success=True,result_code="COMPLETE")
            store.clock=lambda:1301
            with self.assertRaisesRegex(ReservationError,"conflicts"):
                store.reserve(booking_id="test-booking-02",owner="codex-owner-02",
                    workload="accepted-9b-direct-control-smoke-v1",start_epoch=1400,end_epoch=2000)

    def test_cancelled_future_booking_releases_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self.store(tmp)
            store.reserve(booking_id="test-booking-01",owner="codex-owner-01",
                workload="accepted-9b-direct-control-smoke-v1",start_epoch=2000,end_epoch=2600)
            store.cancel("test-booking-01")
            value=store.reserve(booking_id="test-booking-02",owner="codex-owner-02",
                workload="accepted-9b-direct-control-smoke-v1",start_epoch=2000,end_epoch=2600)
            self.assertEqual(value["state"],"scheduled")


if __name__ == "__main__": unittest.main()
