#!/bin/sh
# Run as root inside the NetBox LXC after installing the report service files.
set -eu

container=netbox-netbox-1
manage=/opt/netbox/netbox/manage.py
python=/opt/netbox/venv/bin/python
container_token=/tmp/aster-netbox-report-token
host_token=/etc/aster-netbox-report/token
header_file=/run/aster-netbox-report-header

install -d -o root -g aster-netbox-report -m 0750 /etc/aster-netbox-report

if [ ! -s "$host_token" ]; then
    docker exec -e ASTER_TOKEN_PATH="$container_token" "$container" "$python" "$manage" shell -c '
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from users.models import ObjectPermission, Token

username = "aster-readonly"
permission_name = "Aster sanitized inventory read only"
models = {
    ("dcim", "device"), ("dcim", "devicerole"), ("dcim", "devicetype"),
    ("dcim", "manufacturer"), ("dcim", "site"), ("dcim", "location"),
    ("dcim", "rack"), ("virtualization", "virtualmachine"),
    ("virtualization", "cluster"), ("ipam", "vlan"), ("ipam", "prefix"),
    ("ipam", "ipaddress"),
}
User = get_user_model()
user, created = User.objects.get_or_create(
    username=username,
    defaults={"is_active": True, "is_superuser": False},
)
if created:
    user.set_unusable_password()
    user.save(update_fields=["password"])
if not user.is_active or user.is_superuser or user.has_usable_password():
    raise SystemExit("NetBox Aster account does not match the restricted profile")
permission, created = ObjectPermission.objects.get_or_create(
    name=permission_name,
    defaults={"description": "View-only fields used by the sanitized Aster inventory report", "enabled": True, "actions": ["view"], "constraints": None},
)
if permission.actions != ["view"] or not permission.enabled or permission.constraints is not None:
    raise SystemExit("NetBox Aster permission does not match the view-only profile")
types = ContentType.objects.filter(app_label__in={a for a, _ in models}, model__in={m for _, m in models})
actual = set(types.values_list("app_label", "model"))
if actual != models:
    raise SystemExit("NetBox content type set is incomplete")
permission.object_types.set(types)
user.object_permissions.add(permission)
if Token.objects.filter(user=user, description="Aster sanitized inventory report").exists():
    raise SystemExit("NetBox Aster token already exists without a host token file")
token = Token(user=user, description="Aster sanitized inventory report", write_enabled=False)
token.save()
Path(__import__("os").environ["ASTER_TOKEN_PATH"]).write_text(token.get_auth_header_prefix() + token.token + "\n", encoding="utf-8")
' >/dev/null
    docker cp "$container:$container_token" "$host_token" >/dev/null
    docker exec "$container" rm -f "$container_token"
    chown root:aster-netbox-report "$host_token"
    chmod 0640 "$host_token"
fi

docker exec "$container" "$python" "$manage" shell -c '
from django.contrib.auth import get_user_model
from users.models import Token
u = get_user_model().objects.get(username="aster-readonly")
p = u.object_permissions.get(name="Aster sanitized inventory read only")
t = Token.objects.get(user=u, description="Aster sanitized inventory report")
assert u.is_active and not u.is_superuser and not u.has_usable_password()
assert p.enabled and p.actions == ["view"] and p.constraints is None
assert t.enabled and not t.write_enabled
' >/dev/null

umask 077
printf 'Authorization: ' > "$header_file"
sed -n '1p' "$host_token" >> "$header_file"
printf '\n' >> "$header_file"
trap 'rm -f "$header_file"' EXIT HUP INT TERM
status=$(curl -sS -o /dev/null -w '%{http_code}' \
    -H "@$header_file" http://127.0.0.1:8000/api/dcim/devices/?limit=1)
rm -f "$header_file"
trap - EXIT HUP INT TERM
[ "$status" = 200 ] || {
    echo "NetBox read-only token verification failed" >&2
    exit 1
}
echo "source=netbox identity=aster-readonly permission=view token_write_enabled=false status=verified"
