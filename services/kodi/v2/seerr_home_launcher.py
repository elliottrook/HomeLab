"""Pure transformation for Aster Media's Seerr Requests destination."""

import re


class LauncherError(ValueError):
    pass


def _group_bounds(raw, identity='23'):
    marker = '<control type="group" id="' + identity + '">'
    start = raw.find(marker)
    if start < 0 or raw.find(marker, start + 1) >= 0:
        raise LauncherError('seerr-home-group-missing')
    token = re.compile(r'<control\b|</control>')
    depth = 0
    for match in token.finditer(raw, start):
        if match.group() == '<control':
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start, match.end()
    raise LauncherError('seerr-home-group-unclosed')


def _button(identity, left, width, label, onclick, left_id, right_id, down):
    return f'''            <control type="button" id="{identity}">
                <left>{left}</left><top>31</top><width>{width}</width><height>46</height>
                <label>{label}</label><font>font20</font><align>center</align><aligny>center</aligny>
                <textcolor>00000000</textcolor><focusedcolor>00000000</focusedcolor>
                <texturefocus border="18" colordiffuse="ff005c46">special://skin/media/ui-panel.png</texturefocus>
                <texturenofocus border="18" colordiffuse="99000000">special://skin/media/ui-panel.png</texturenofocus>
                <onleft>{left_id}</onleft><onright>{right_id}</onright><onup>{identity}</onup><ondown>{down}</ondown>
                <enable>!Player.HasMedia</enable><onclick>{onclick}</onclick>
            </control>'''


def _visible_label(identity, left, width, label, icon=''):
    icon_xml = ''
    label_left, label_width, align = left + 10, width - 20, 'center'
    if icon:
        icon_xml = (f'<control type="image"><left>{left + 10}</left><top>40</top><width>28</width><height>28</height>'
                    f'<texture>{icon}</texture><aspectratio>keep</aspectratio></control>')
        label_left, label_width, align = left + 48, width - 58, 'left'
    return (icon_xml + f'<control type="label"><left>{label_left}</left><top>31</top>'
            f'<width>{label_width}</width><height>46</height><label>{label}</label><font>font20</font>'
            f'<textcolor>fff3eee5</textcolor><align>{align}</align><aligny>center</aligny><truncate>true</truncate>'
            f'<visible>Control.IsVisible({identity})</visible></control>'
            f'<control type="image"><left>{left - 1}</left><top>30</top><width>{width + 2}</width><height>48</height>'
            f'<texture border="18" colordiffuse="fff3eee5">special://skin/media/ui-compact-card-ring.png</texture>'
            f'<visible>Control.HasFocus({identity})</visible></control>')


def requests_group():
    rows = (
        (135, 350, 170, 'Search',
         'RunScript(script.asterruntime,aster-global-search-ui22,default)', 136, 130, 121, ''),
        (130, 540, 140, 'TV Shows',
         'ActivateWindow(Videos,special://skin/playlists/tv-shows.xsp,return)', 135, 131, 120,
         'special://skin/media/07-tv.png'),
        (131, 690, 125, 'Movies',
         'ActivateWindow(Videos,special://skin/playlists/movies.xsp,return)', 130, 132, 120,
         'special://skin/media/08-film.png'),
        (132, 825, 150, 'Archive TV',
         'ActivateWindow(Videos,special://skin/playlists/archive-tv.xsp,return)', 131, 133, 120,
         'special://skin/media/09-archive-tv.png'),
        (133, 985, 185, 'Archive Movies',
         'ActivateWindow(Videos,special://skin/playlists/archive-film.xsp,return)', 132, 134, 120,
         'special://skin/media/10-archive-film.png'),
        (134, 1180, 150, 'Collections',
         'ActivateWindow(Videos,videodb://movies/sets/,return)', 133, 137, 120,
         'special://skin/media/19-movie-collections-128.png'),
        (137, 1340, 145, 'Requests', 'RunScript(script.asterseerr)', 134, 136, 121,
         'special://skin/media/aster-compass-128.png'),
        (136, 1495, 155, 'YouTube',
         'ActivateWindow(Videos,&quot;plugin://plugin.video.youtube/&quot;,return)', 137, 135, 121,
         'special://skin/media/33-aster-youtube-128.png'),
    )
    buttons = '\n'.join(_button(*row[:8]) for row in rows)
    labels = ''.join(_visible_label(row[0], row[1], row[2], row[3], row[8]) for row in rows)
    return f'''<control type="group" id="23">
            <control type="image"><left>532</left><top>23</top><width>1126</width><height>62</height><texture border="18" colordiffuse="52000000">special://skin/media/ui-panel.png</texture></control>
            <control type="image"><left>348</left><top>29</top><width>174</width><height>50</height><texture border="18" colordiffuse="ffad8a4d">special://skin/media/ui-compact-card-ring.png</texture></control>
            <animation effect="fade" start="100" end="0" time="0" condition="[Control.HasFocus(8999) | Control.HasFocus(9001) | Control.HasFocus(9002) | Control.HasFocus(9003) | Control.HasFocus(9004) | Control.HasFocus(9005) | Control.HasFocus(9007)] + !Skin.HasSetting(AsterReducedMotion)">Conditional</animation>
{buttons}
            {labels}
        </control>'''


def add_requests(raw):
    if not isinstance(raw, str) or raw.count('RunScript(script.asterseerr)'):
        raise LauncherError('seerr-home-already-transformed')
    start, end = _group_bounds(raw)
    result = raw[:start] + requests_group() + raw[end:]
    if result.count('RunScript(script.asterseerr)') != 1 or result.count('id="137"') != 1:
        raise LauncherError('seerr-home-transform-failed')
    return result
