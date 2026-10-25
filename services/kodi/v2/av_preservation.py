"""Strict AV comparison with one evidenced HP-only derived-index remapping.

Kodi Omega SettingOptionsResolutionsFiller derives the numeric selector from
screenmode and enumerated modes. Do not overwrite the historical baseline or
treat arbitrary display/audio changes as harmless.
"""
import hashlib,json
def fingerprint(values):
    return dict(count=len(values),sha256=hashlib.sha256(json.dumps(sorted(values)).encode()).hexdigest())
def verify(values,baseline,screen):
    if fingerprint(values)==baseline:return dict(exact_values=len(values),resolution_index_rederived=False)
    current=dict(values)
    if not (len(current)==len(values)==68 and current.get('videoscreen.resolution')=='17'
        and current.get('videoscreen.screenmode')=='DESKTOP'
        and screen.get('System.ScreenWidth')=='3840' and screen.get('System.ScreenHeight')=='2160'
        and screen.get('System.ScreenResolution','').startswith('3840x2160 @ 30.00 Hz')):
        raise ValueError('av-preservation-mismatch')
    normalized=[(key,'16' if key=='videoscreen.resolution' else value) for key,value in values]
    if fingerprint(normalized)!=baseline:raise ValueError('av-preservation-mismatch')
    return dict(exact_values=67,resolution_index_rederived=True,
        resolution_index_before=16,resolution_index_now=17,stored_screenmode='DESKTOP',
        observed_screen='3840x2160 @ 30.00 Hz',original_baseline_retained=True)
