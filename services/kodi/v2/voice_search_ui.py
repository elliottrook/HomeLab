"""Pure presentation contract for explicit Aster voice search.

The view never starts capture.  It only turns a validated capability/session
into truthful copy and control state for the existing Search page.
"""
from dataclasses import dataclass

from voice_search import Capability, Session, STATES, VoiceUnavailable


@dataclass(frozen=True)
class VoiceView:
    title: str
    status: str
    action: str
    action_label: str
    action_enabled: bool
    cancel_visible: bool
    keyboard_visible: bool
    busy: bool


def present(capability, session):
    if (not isinstance(capability, Capability) or not isinstance(session, Session)
            or session.state not in STATES):
        raise VoiceUnavailable('voice-view-invalid')

    if session.state == 'listening':
        return VoiceView('Listening…', 'Speak now · Back cancels without saving audio',
                         'cancel', 'Cancel', True, True, False, True)
    if session.state == 'transcribing':
        return VoiceView('Working…', 'Recognizing speech on the local Aster service',
                         'cancel', 'Cancel', True, True, False, True)
    if session.state == 'results':
        return VoiceView('Voice search', 'Showing results for “'+session.query+'”',
                         'start', 'Search again', capability.state == 'ready',
                         False, True, False)
    if session.state == 'cancelled':
        return VoiceView('Voice search', 'Cancelled · no audio was retained',
                         'start', 'Try again', capability.state == 'ready',
                         False, True, False)
    if session.state == 'error':
        return VoiceView('Voice search', session.reason or 'Voice search unavailable',
                         'start', 'Try again', capability.state == 'ready',
                         False, True, False)

    if capability.state == 'ready':
        return VoiceView('Voice search', 'Press once, speak, then wait for results',
                         'start', 'Start listening', True, False, True, False)
    return VoiceView('Voice search', capability.reason,
                     'unavailable', 'Voice unavailable', False, False, True, False)
