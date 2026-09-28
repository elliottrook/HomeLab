"""Build the standalone Authentik expression with a fixed activation epoch."""
import argparse
from pathlib import Path


def expression(policy_epoch: int) -> str:
    if type(policy_epoch) is not int or policy_epoch <= 0:
        raise ValueError('A positive fixed activation epoch is required')
    source = Path(__file__).with_name('companion_passkey.py').read_text()
    tail = '''
from authentik.events.signals import get_login_event
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from django.utils import timezone
try:
    if provider.client_id != "aster-companion" or provider.pk != 26:
        return {}
    if provider.authentication_flow.slug != "aster-companion-reauthentication":
        return {}
    stage = AuthenticatorValidateStage.objects.get(name="aster-companion-webauthn-validate")
    if (list(stage.device_classes) != ["webauthn"]
            or stage.webauthn_user_verification != "required"
            or stage.last_auth_threshold != "seconds=0"
            or stage.not_configured_action != "deny"):
        return {}
    if token.session is None:
        return {}
    event = get_login_event(token.session)
    return companion_passkey_claims(provider, token, user, event, POLICY_EPOCH, timezone.now().timestamp())
except (AttributeError, TypeError, ValueError, AuthenticatorValidateStage.DoesNotExist):
    return {}
'''
    return source + tail.replace('POLICY_EPOCH', str(policy_epoch))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--policy-epoch', type=int, required=True)
    args=parser.parse_args()
    print(expression(args.policy_epoch), end='')
