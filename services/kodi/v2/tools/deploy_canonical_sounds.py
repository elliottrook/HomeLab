"""Bounded canonical WAV adoption on the two approved boxes; run inside Kodi."""
import hashlib,json,os,shutil,sys,time,wave
from pathlib import Path
import xbmc

BASE=Path('/storage/.aster-staging/aster-canonical-pcm32-20261025')
LIVE=Path('/storage/.kodi/addons/resource.uisounds.asterhome/resources')
CHECKPOINT=Path('/storage/.aster-checkpoints/aster-canonical-pcm32-20261025')
SOURCE_COMMIT='4c283eaf0a35f34cf9018d06c27304cd09c760a5'
CUE_COUNT=4
MOVEMENT='227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8'
MASTER_EXPECTED={**{n:MOVEMENT for n in ('nav-left.wav','nav-right.wav','nav-up.wav','nav-down.wav')},
    'back.wav':'33b9852ee00869cefd0040ce6a65573ec1a5606a87352917e7654d7b36348a54',
    'select.wav':'a95d8c2a2d874a0f04b5ab82fb11d0a7a1d850562849de3c86cbf1050edb2910',
    'notify.wav':'57f108306b772252095811c9827dd6667c58f53e9c80f7f733976467057de6f6'}
EXPECTED={**{n:'76cc78bb5b1c2901a0ceabd25c337daa51a4f1d04e828f94b8cc74e0f69c58ac' for n in ('nav-left.wav','nav-right.wav','nav-up.wav','nav-down.wav')},
    'back.wav':'9966043bb9601362f15e3f11f0272c78bad7f2c7201aee7952200c1c0aaef9a8',
    'select.wav':'19ffc9a9ea3d74e69c9e1b8a5ea3ca10ef8c6af8de47629b919609379226ad3e',
    'notify.wav':'5c9f60ac6e86b93beae0801646b9ba8b342e001a9b5fb47cfde3873786dcba80'}
ORIGINALS={
    'AsterTV':dict(zip(('back.wav','nav-down.wav','nav-left.wav','nav-right.wav','nav-up.wav','notify.wav','select.wav'),(
        '1afe1ce5b910832b41af976a78298f7253a56810581ef614b84a987dacf449d8',
        'cc517c2401a0889befd031e6d21608b448805f3272d454e8f7d94ff1bc93a224',
        '1e0ef44a936bf304907e83a88347318924444ed111e64db82c7e732aa3476329',
        '4f916f4049a0d849eaca39f6315206b9c858c24d208bdb29f966e8ebe5176741',
        '79750a0533a86c828eb9d284e911b2bef4295270bea3fdc9a49f59a51059ae75',
        '8fa5141a4bc70478a969e927539b560fda930976821a0d7a4c140d4b665352b6',
        '5b9c7b4348ca1df78c7e86b4b3484b68777f2ee28ea7bec0d268da58de0dfa69'))),
    'AsterTVProd':dict(zip(('back.wav','nav-down.wav','nav-left.wav','nav-right.wav','nav-up.wav','notify.wav','select.wav'),(
        '7c4c070068c691b46cf08de2cfc17de6e6f9d7304d5ca44b087fe8e4c79422d1',
        'b688fb29a1953aabdb22c501cf4184ef82e88509311d9f741bc169cb4d73f666',
        '2abf2b4bc4ff931157208b65eed88eacfbb9b272b961c5a3639ad133ebb7e40d',
        '21a439960a942a8202487763030f9d4960427b6864552b18e7cd13129ef568a6',
        'ff89697938f654a426368264aaddd5c744dda9d7af52d8cf333e17b00845a8df',
        '6cdb92d90a684e05d7e5cd98d613a13312488f1cdf849abe144deaab233c5545',
        'b48ec3f8cd9135053624edb472f2e9b8a5c8d896b23e2ca93b5dc8a57750b785')))}

def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Settings.GetSettings','Settings.SetSettingValue'),'rpc-boundary')
    if method=='Settings.SetSettingValue':
        require(params['setting']=='lookandfeel.soundskin' and params['value'] in ('','resource.uisounds.asterhome'),'sound-theme-only')
    response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in response,'rpc-'+method);return response['result']
def settings():return {r['id']:r.get('value') for r in rpc('Settings.GetSettings')['settings']}
def replace(source,target):
    temporary=target.with_suffix('.wav.canonical-tmp');shutil.copyfile(source,temporary);os.replace(str(temporary),str(target))
def reload_theme():
    for value in ('','resource.uisounds.asterhome'):
        require(rpc('Settings.SetSettingValue',dict(setting='lookandfeel.soundskin',value=value)) is True,'theme-reload-failed')
def snapshot():return {name:sha(LIVE/name) for name in EXPECTED}
def main(mode='inspect'):
    host=os.uname().nodename;require(host in ORIGINALS,'known-host-required')
    before=settings();require(before.get('lookandfeel.soundskin')=='resource.uisounds.asterhome','unexpected-theme')
    report=dict(kind='aster-canonical-ui-sounds.v1',host=host,theme='resource.uisounds.asterhome',idle=not rpc('Player.GetActivePlayers'),assets=snapshot())
    require(mode in ('inspect','deploy','rollback','verify'),'mode')
    if mode=='inspect':return report
    if mode=='verify':
        evidence=json.loads((CHECKPOINT/'verified.json').read_text())
        require(report['assets']==EXPECTED==evidence['assets'],'canonical-assets-drift')
        require(all(sha(CHECKPOINT/name)==digest for name,digest in ORIGINALS[host].items()),'original-checkpoint-drift')
        report.update(verified=True,unique_assets=CUE_COUNT,checkpoint_verified=True);return report
    require(report['idle'],'playback-active-no-change')
    original=ORIGINALS[host]
    if mode=='rollback':
        require(snapshot()==EXPECTED,'installed-drift')
        require(all(sha(CHECKPOINT/name)==digest for name,digest in original.items()),'recovery-drift')
        for name in EXPECTED:replace(CHECKPOINT/name,LIVE/name)
        reload_theme();require(snapshot()==original and settings()==before,'rollback-verification')
        report.update(rolled_back=True,settings_unchanged=True);return report
    require(not CHECKPOINT.exists(),'existing-checkpoint-do-not-repeat')
    require(report['assets']==original,'predecessor-drift')
    for name,digest in EXPECTED.items():
        source=BASE/'resources'/name;require(sha(source)==digest,'canonical-master-drift')
        require(sha(BASE/'masters'/name)==MASTER_EXPECTED[name],'source-master-drift')
        with wave.open(str(source),'rb') as sound:
            require(sound.getparams()[:3]==(2,4,48000) and sound.getnframes()<24000,'canonical-format')
            runtime=sound.readframes(sound.getnframes())
        with wave.open(str(BASE/'masters'/name),'rb') as master:
            raw=master.readframes(master.getnframes())
        require(len(runtime)*3==len(raw)*4 and all(
            int.from_bytes(runtime[j*4:j*4+4],'little',signed=True)==
            int.from_bytes(raw[j*3:j*3+3],'little',signed=True)<<8
            for j in range(len(raw)//3)),'lossless-promotion-required')
    CHECKPOINT.mkdir(mode=0o700,parents=True)
    for name in EXPECTED:
        shutil.copyfile(LIVE/name,CHECKPOINT/name)
        require(sha(CHECKPOINT/name)==original[name],'checkpoint-verification')
    shutil.copyfile(Path(__file__),CHECKPOINT/'deploy_canonical.py')
    mapping=sha(LIVE/'sounds.xml')
    require(not rpc('Player.GetActivePlayers'),'playback-started-no-change')
    try:
        for name in EXPECTED:replace(BASE/'resources'/name,LIVE/name)
        reload_theme()
        require(snapshot()==EXPECTED,'installed-verification')
        require(settings()==before and sha(LIVE/'sounds.xml')==mapping,'preservation-failed')
    except Exception:
        for name in EXPECTED:replace(CHECKPOINT/name,LIVE/name)
        reload_theme();require(snapshot()==original and settings()==before,'automatic-rollback-failed')
        raise
    report.update(installed=True,assets=snapshot(),unique_assets=CUE_COUNT,settings_unchanged=True,mapping_unchanged=True,
        source_commit=SOURCE_COMMIT,
        checkpoint=str(CHECKPOINT),restart_required=False,timing_and_pcm_unchanged=True,
        encoding='PCM32-lossless-from-PCM24',source_assets=MASTER_EXPECTED)
    (CHECKPOINT/'verified.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':
    try:result=main(sys.argv[1] if len(sys.argv)==2 else 'inspect');result['ok']=True
    except Exception as error:result=dict(ok=False,code=str(error))
    (BASE/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
