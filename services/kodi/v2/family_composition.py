"""Static release-composition audit for an accepted Aster runtime tree."""
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re


STAGING = re.compile(rb'/storage/\.aster-staging/([A-Za-z0-9._-]+)')
TEXT_SUFFIXES = frozenset(('.json', '.py', '.service', '.sh', '.timer', '.xml'))


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    value: str = ''


def _relative(root, path):
    return Path(path).relative_to(root).as_posix()


def is_debris(path):
    path = Path(path)
    return (path.name.startswith('._') or path.suffix == '.pyc'
            or '__pycache__' in path.parts or '.pre-' in path.name)


def audit_tree(root):
    root = Path(root).resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('family-composition-root')
    findings = []
    for path in sorted(root.rglob('*')):
        relative = _relative(root, path)
        if path.is_symlink():
            findings.append(Finding('linked-path', relative))
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            findings.append(Finding('special-path', relative))
            continue
        if is_debris(path):
            findings.append(Finding('runtime-debris', relative))
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in ('addon.xml',):
            raw = path.read_bytes()
            for stage in sorted(set(match.decode('ascii') for match in STAGING.findall(raw))):
                findings.append(Finding('staging-runtime-reference', relative, stage))
    return tuple(findings)


def clean_manifest(root):
    root = Path(root).resolve()
    findings = audit_tree(root)
    if findings:
        raise ValueError('family-composition-not-clean')
    rows = []
    for path in sorted(item for item in root.rglob('*') if item.is_file()):
        raw = path.read_bytes()
        rows.append(dict(path=_relative(root, path), bytes=len(raw),
                         sha256=hashlib.sha256(raw).hexdigest()))
    return rows


def report(root):
    findings = audit_tree(root)
    return dict(passed=not findings, findings=[asdict(item) for item in findings],
                staging_dependencies=sorted({item.value for item in findings
                                             if item.code == 'staging-runtime-reference'}),
                counts={code: sum(item.code == code for item in findings)
                        for code in sorted({item.code for item in findings})})
