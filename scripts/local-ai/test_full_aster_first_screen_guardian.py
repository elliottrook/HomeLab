import json
from pathlib import Path
import tempfile
import unittest

import full_aster_first_screen_guardian as guardian


def screen_state():
    return {"schema":"aster-full-path-first-screen-live.v1", "phase":"mounted",
            "owner_id":"aster-full-screen-owner-0123456789abcdef",
            "owner_unit":"aster-full-screen-owner-0123456789abcdef.scope",
            "cycle":"2026-10-27", "model_sha256":"c"*64,
            "binary_sha256":"b"*64, "unit_sha256":"d"*64,
            "admission_sha256":"a"*64}


def drain_state():
    return {"owner_id":"aster-full-screen-owner-0123456789abcdef",
            "lease_id":"aster-full-screen-owner-0123456789abcdef:123",
            "generation":1}


class GuardianTests(unittest.TestCase):
    def test_absent_state_at_cutoff_exits_without_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            result=guardian.run_guardian(state_path=root/"screen", drain_state_path=root/"drain",
                owner_unit="aster-full-screen-owner-0123456789abcdef.scope",
                rescue_at=10, hard_deadline=910, clock=lambda:10,
                sleep=lambda _:None, fence=lambda _: (_ for _ in ()).throw(AssertionError()),
                recoverer=lambda _: (_ for _ in ()).throw(AssertionError()))
            self.assertEqual(result["effects"], "not-attempted")

    def test_fences_owner_then_recovers_exact_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); screen=root/"screen"; drain=root/"drain"
            events=[]
            ticks=iter((0,0,10,10))
            def arm(_seconds):
                screen.write_text(json.dumps(screen_state())); drain.write_text(json.dumps(drain_state()))
            def recover(identity):
                events.append(("recover", identity.lease_id)); screen.unlink(); drain.unlink()
            result=guardian.run_guardian(state_path=screen, drain_state_path=drain,
                owner_unit="aster-full-screen-owner-0123456789abcdef.scope",
                rescue_at=10, hard_deadline=910, clock=lambda:next(ticks),
                sleep=arm, fence=lambda budget: events.append(("fence",budget)) or True,
                recoverer=recover)
            self.assertEqual(events[0], ("fence",900))
            self.assertEqual(events[1][0], "recover")
            self.assertEqual(result["effects"], "restored")

    def test_foreign_state_or_failed_fence_is_terminal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); screen=root/"screen"; drain=root/"drain"
            ticks=iter((0,0,10,10))
            def arm(_seconds):
                screen.write_text(json.dumps(screen_state())); drain.write_text(json.dumps(drain_state()))
            with self.assertRaises(guardian.GuardianError):
                guardian.run_guardian(state_path=screen, drain_state_path=drain,
                    owner_unit="aster-full-screen-owner-0123456789abcdef.scope",
                    rescue_at=10, hard_deadline=910, clock=lambda:next(ticks),
                    sleep=arm, fence=lambda _:False, recoverer=lambda _:None)
            screen.unlink(); drain.unlink(); ticks=iter((0,0,10,10))
            def arm_bad(_seconds):
                bad=screen_state(); bad["extra"]=True
                screen.write_text(json.dumps(bad)); drain.write_text(json.dumps(drain_state()))
            with self.assertRaises(guardian.GuardianError):
                guardian.run_guardian(state_path=screen, drain_state_path=drain,
                    owner_unit="aster-full-screen-owner-0123456789abcdef.scope",
                    rescue_at=10, hard_deadline=910, clock=lambda:next(ticks),
                    sleep=arm_bad, fence=lambda _:True, recoverer=lambda _:None)


if __name__ == "__main__": unittest.main()
