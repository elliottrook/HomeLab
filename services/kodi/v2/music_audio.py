"""Quiet factual source-format labels; never infer receiver/output fidelity."""
import re

LABELS=('MusicPlayer.Codec','MusicPlayer.SampleRate','MusicPlayer.BitsPerSample',
        'MusicPlayer.Channels','MusicPlayer.Bitrate')


def source_summary(labels):
    if not isinstance(labels,dict):return ''
    def value(key):
        text=labels.get('MusicPlayer.'+key,'')
        return text.strip() if isinstance(text,str) and len(text)<=40 else ''
    parts=[];codec=value('Codec')
    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._+/-]{0,19}',codec):parts.append(codec.upper())
    rate=value('SampleRate')
    match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(k?Hz)?',rate,re.I)
    if match:
        number=float(match[1])
        # Kodi 21.3 MusicGUIInfo.cpp emits this unlabelled value in kHz:
        # https://github.com/xbmc/xbmc/blob/21.3-Omega/xbmc/guilib/guiinfo/MusicGUIInfo.cpp#L472-L478
        if not match[2] or match[2].lower()=='khz':number*=1000
        if 8000<=number<=768000:parts.append(f'{number/1000:g} kHz')
    bits=value('BitsPerSample')
    if bits.isdigit() and 8<=int(bits)<=64:parts.append(str(int(bits))+'-bit')
    channels=value('Channels')
    if re.fullmatch(r'(?:[1-9]|[12][0-9]|3[0-2])(?:\.[0-9])?',channels):parts.append(channels+' ch')
    bitrate=value('Bitrate')
    match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:kbps|kb/s|kbit/s)?',bitrate,re.I)
    if match and 1<=float(match[1])<=100000:parts.append(f'{float(match[1]):g} kb/s')
    return 'Source: '+' · '.join(parts) if parts else ''


def read_source(rpc):
    try:
        values=rpc('XBMC.GetInfoLabels',{'labels':list(LABELS)})
    except Exception:return ''
    return source_summary(values)


def read_details(rpc):
    source=read_source(rpc) or 'Source format unavailable'
    configured='Configured output unavailable'
    try:
        result=rpc('Settings.GetSettingValue',{'setting':'audiooutput.audiodevice'})
        value=result.get('value') if isinstance(result,dict) else None
        if isinstance(value,str) and len(value)<=500:
            upper=value.upper()
            if 'HDMI' in upper:configured='Configured output: HDMI'+(' (ALSA)' if upper.startswith('ALSA:') else '')
            elif upper.startswith('ALSA:'):configured='Configured output: ALSA audio device'
            elif value:configured='Configured output: system audio device'
    except Exception:pass
    return source+'\n\n'+configured+'\n\nSource format describes the audio stream. Output is the configured device, not a measurement of the receiver or a bit-perfect guarantee.'
