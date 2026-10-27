import unittest

import full_aster_first_screen_recovery as recovery


def identity(**changes):
    value = dict(owner_id="aster-full-screen-owner-0123456789abcdef",
                 lease_id="aster-full-screen-owner-0123456789abcdef:123",
                 generation=1, cycle="2026-10-27",
                 model_sha256="c" * 64, binary_sha256="b" * 64,
                 unit_sha256="d" * 64)
    value.update(changes)
    return recovery.RecoveryIdentity(**value)


class Observer:
    def __init__(self, mount="exact", running=True, baseline=True,
                 candidate_absent=True):
        self.mount = mount; self.running = running; self.baseline = baseline
        self.absent = candidate_absent
    def candidate_absent(self): return self.absent
    def mount_state(self): return self.mount
    def guest_running(self): return self.running
    def exact_baseline_restored(self): return self.baseline


class RecoveryTests(unittest.TestCase):
    def test_exact_mount_is_removed_before_baseline_and_full_drain_rescue(self):
        observer = Observer()
        commands = []
        def run(command, _timeout):
            commands.append(tuple(command))
            if tuple(command) == recovery.shutdown_command(): observer.running = False
            if tuple(command) == recovery.delete_mount_command(): observer.mount = "absent"
            if tuple(command) == recovery.start_guest_command(): observer.running = True
        recovery.recover(identity=identity(), observer=observer, runner=run)
        self.assertEqual(commands[0], recovery.stop_command())
        self.assertIn(recovery.delete_mount_command(), commands)
        self.assertLess(commands.index(recovery.delete_mount_command()),
                        commands.index(recovery.start_guest_command()))
        self.assertEqual(commands[-1][3:5], ("--phase", "rescue"))

    def test_absent_mount_and_running_guest_do_not_restart_container(self):
        commands = []
        recovery.recover(identity=identity(), observer=Observer(mount="absent"),
                         runner=lambda command, timeout: commands.append(tuple(command)))
        self.assertNotIn(recovery.shutdown_command(), commands)
        self.assertNotIn(recovery.delete_mount_command(), commands)
        self.assertNotIn(recovery.start_guest_command(), commands)

    def test_foreign_mount_candidate_or_bad_baseline_fail_closed(self):
        for observer in (Observer(mount="foreign"), Observer(candidate_absent=False),
                         Observer(mount="absent", baseline=False)):
            with self.subTest(observer=observer), self.assertRaises(recovery.RecoveryError):
                recovery.recover(identity=identity(), observer=observer,
                                 runner=lambda command, timeout: None)

    def test_identity_and_commands_are_fixed(self):
        with self.assertRaises(recovery.RecoveryError): identity(generation=2).validate()
        self.assertEqual(recovery.delete_mount_command(),
                         ("pct", "set", "110", "--delete", "mp0"))
        command = recovery.full_drain_rescue_command(identity())
        self.assertIn("--effect-authorized", command)
        self.assertNotIn(recovery.HOST_MODEL, command)


if __name__ == "__main__":
    unittest.main()
