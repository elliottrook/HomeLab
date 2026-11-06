"""Undeployed recovery composition for the fixed candidate adapter.

The injected backend must own source-local custody, exact mount observations and
bounded effects. This module has no production backend, runner or activation.
Journal writes must be durable before returning; the same binding is required by
both owner and independent guardian. Synthetic implementations grant no authority.
"""
import hashlib
import json
import re


class CandidateRecoveryError(RuntimeError):
    pass


class CandidateRecovery:
    def __init__(self, command, *, entry_sha256, custody_sha256, backend, journal):
        for digest in (entry_sha256, custody_sha256):
            if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise CandidateRecoveryError('checkpoint identity required')
        booking = command['booking_id']
        if (command.get('schema') != 'b60-fixed-candidate-command.v1'
                or command.get('owned_unit') != 'b60-exclusive-trial-'+booking+'.service'):
            raise CandidateRecoveryError('candidate fence identity differs')
        self.binding = {
            'booking_id': booking, 'entry_sha256': entry_sha256,
            'custody_sha256': custody_sha256,
            'command_sha256': hashlib.sha256(json.dumps(command, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(),
        }
        self.backend, self.journal = backend, journal

    def _require(self, condition, message):
        if condition is not True:
            raise CandidateRecoveryError(message)

    def _intent(self, phase):
        # Durable intent is required even when resuming after an interrupted
        # prior effect; the observed backend state decides idempotent cleanup.
        self._require(self.journal.write({'schema':'b60-candidate-recovery.v1',
            'binding':dict(self.binding), 'phase':phase}), 'journal not durable')

    def restore(self):
        previous = self.journal.read()
        if previous is not None and (previous.get('schema') != 'b60-candidate-recovery.v1'
                or previous.get('binding') != self.binding
                or previous.get('phase') not in {'fence-intent','mount-cleanup-intent',
                    'custody-restore-intent','base-restore-intent','verified'}):
            raise CandidateRecoveryError('recovery journal binding differs')
        # The backend verifies shared owner/exclusion, entry/custody pins,
        # source identity and recovery time before even the first fence call.
        self._require(self.backend.validate_recovery(self.binding), 'recovery admission refused')
        self._intent('fence-intent')
        self._require(self.backend.fence_candidate(), 'candidate fence failed')
        self._require(self.backend.candidate_empty(), 'candidate tasks remain')
        observed = self.backend.mount_state()
        if observed not in {'absent', 'exact'}:
            raise CandidateRecoveryError('unknown mount retained')
        if observed == 'exact':
            self._intent('mount-cleanup-intent')
            self._require(self.backend.remove_exact_mount(), 'mount cleanup failed')
        self._require(self.backend.mount_state() == 'absent', 'candidate mount remains')
        self._intent('custody-restore-intent')
        self._require(self.backend.restore_custody(self.binding['custody_sha256']),
                      'staging custody restoration failed')
        self._require(self.backend.verify_custody(self.binding['custody_sha256']),
                      'staging custody differs')
        # Base adapter retains its own full production mount-identity check.
        # No base restart/release is reachable while candidate tasks, mount or
        # changed staging custody remain. Failure retains shared exclusion.
        self._intent('base-restore-intent')
        self._require(self.backend.restore_entry(self.binding['entry_sha256']),
                      'entry restoration failed')
        self._require(self.backend.verify_entry(self.binding['entry_sha256']),
                      'entry verification failed')
        self._intent('verified')
        return True  # Not a lease release, model result or live qualification.
