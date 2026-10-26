"""Pure transforms for Aster's opt-in reduced-motion skin setting."""
import xml.etree.ElementTree as ET


SETTING = 'Skin.HasSetting(AsterReducedMotion)'


def reduced_motion(raw):
    root = ET.fromstring(raw)
    for animation in root.iter('animation'):
        condition = (animation.get('condition') or '').strip()
        if SETTING in condition:
            continue
        animation.set('condition',
                      ('[' + condition + '] + !' + SETTING) if condition
                      else '!' + SETTING)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
