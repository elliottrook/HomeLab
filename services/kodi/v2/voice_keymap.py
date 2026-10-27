"""Build the HP G20 voice-search keymap from the accepted v1 mapping."""
import xml.etree.ElementTree as ET


SELECT_CODE = '353'       # Linux KEY_SELECT
# Kodi translates Linux KEY_VOICECOMMAND scancode 0x246 to 0xF200.
VOICE_CODE = '61952'
SELECT_ACTION = 'RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'
VOICE_ACTION = 'RunScript(script.astervoice.v2lab)'


def build(raw):
    root = ET.fromstring(raw)
    keyboard = root.find('./global/keyboard')
    if keyboard is None:
        raise ValueError('voice-keymap-global-keyboard')
    symbolic = keyboard.findall('select')
    if len(symbolic) != 1 or symbolic[0].text != SELECT_ACTION:
        raise ValueError('voice-keymap-select-predecessor')
    symbolic[0].tag = 'key'
    symbolic[0].set('id', SELECT_CODE)
    if keyboard.findall("key[@id='" + VOICE_CODE + "']"):
        raise ValueError('voice-keymap-existing-voice')
    voice = ET.SubElement(keyboard, 'key', {'id': VOICE_CODE})
    voice.text = VOICE_ACTION
    for name in ('FullscreenVideo', 'FullscreenGame', 'Visualisation'):
        section = root.find('./' + name + '/keyboard')
        if section is None:
            raise ValueError('voice-keymap-context')
        context_select = section.findall('select')
        if len(context_select) != 1:
            raise ValueError('voice-keymap-context-select')
        context_select[0].tag = 'key'
        context_select[0].set('id', SELECT_CODE)
        blocked = ET.SubElement(section, 'key', {'id': VOICE_CODE})
        blocked.text = 'noop'
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
