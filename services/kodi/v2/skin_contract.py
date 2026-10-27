"""Fail-closed static checks for an installed or staged Kodi skin tree."""
from dataclasses import asdict, dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    value: str = ''


def _relative(root, path):
    return Path(path).relative_to(root).as_posix()


def audit_skin(root):
    """Return deterministic findings without changing the candidate tree."""
    root = Path(root).resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('skin-contract-root')

    findings = []
    xml_trees = {}
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
        if path.name.startswith('._'):
            findings.append(Finding('appledouble-metadata', relative))
            continue
        if path.suffix.lower() != '.xml':
            continue
        try:
            xml_trees[path] = ET.parse(path)
        except (ET.ParseError, OSError) as error:
            findings.append(Finding('invalid-xml', relative,
                                    error.__class__.__name__))

    font_path = root/'1080i'/'Font.xml'
    font_tree = xml_trees.get(font_path)
    if not font_path.is_file():
        findings.append(Finding('missing-font-catalogue', '1080i/Font.xml'))
    elif font_tree is not None:
        declared = {
            (node.text or '').strip()
            for node in font_tree.findall('.//font/name')
            if (node.text or '').strip()
        }
        for path, tree in sorted(xml_trees.items()):
            if path == font_path:
                continue
            for node in tree.findall('.//font'):
                value = (node.text or '').strip()
                if value and value not in declared:
                    findings.append(Finding('undefined-font',
                                            _relative(root, path), value))
    return tuple(findings)


def report(root):
    findings = audit_skin(root)
    codes = sorted({item.code for item in findings})
    return {
        'passed': not findings,
        'findings': [asdict(item) for item in findings],
        'counts': {code: sum(item.code == code for item in findings)
                   for code in codes},
    }


def require_clean_skin(root):
    findings = audit_skin(root)
    if findings:
        raise ValueError('skin-contract-not-clean')
    return True
