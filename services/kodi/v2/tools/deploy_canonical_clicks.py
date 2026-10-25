"""Owner-approved seven-cue successor; preserve the prior runtime checkpoint."""
import hashlib,json,shutil,sys,time
from pathlib import Path

def configure(engine):
    prior=dict(engine.EXPECTED)
    engine.BASE=Path('/storage/.aster-staging/aster-canonical-clicks-20261025')
    engine.CHECKPOINT=Path('/storage/.aster-checkpoints/aster-canonical-clicks-20261025')
    engine.ORIGINALS={host:dict(prior) for host in ('AsterTV','AsterTVProd')}
    engine.SOURCE_COMMIT='5e7b5cccd09e15f0bd64bc7febb87077093267f3'
    engine.CUE_COUNT=7
    engine.MASTER_EXPECTED=dict(zip(('back.wav','nav-down.wav','nav-left.wav','nav-right.wav','nav-up.wav','notify.wav','select.wav'),(
        'b5c3678e2849cb6b9dd15125f2e1ebeb9afda6f469524d6bada3a20ba6424125',
        '6c414975aff7b7d4caa8866a0e4ffa41f80f222b1c4ca5db199a45c34d741ea9',
        '233b96079ed5471e774b86f840f7ef00dabe2b6f5c5effe91d4ccb17aafb2285',
        'dce25cc207715fba406fb86905e32c4bfbfc5ec17be83abff2db2d9cb77aaa28',
        '08037d2c1e0dd6f930715584493f98e09885e3a8126df076a3cdf01729663cba',
        'c093d94abbabc0383d278b9f8e39dda8ca5fbfdee8080bdce1c4078126e175c8',
        '6e38a7c6fc9964c8c53e49409df42d53200ce51e221c2dbb63b13a8bdb811c3f')))
    engine.EXPECTED=dict(zip(engine.MASTER_EXPECTED,(
        '2f52c6832f200f1b736c2409a647c26526d9204fffca4cbae8a2be1ad7ffe358',
        '9ecfcad41f3f80d2bb54f2e40805ba540b6e1eb2756f65ff373fc68fa36dbdaf',
        '4468672436a0784b6434e056d0d5ec7dcf27e5117f1be2e675d287dd73b47c2a',
        'aab317c5bc447a377617f5ccfe4bd3c07830b9b26ee137bc113196ddc67bdc46',
        '8d16568b195c6097a1893ca0bca1f3b4632086aed093db2c9984ea68e7ab94e7',
        '2fc2aa7e69240ab0dbc8611ff50e604acae1cf60822db5816c36073c7141b9b4',
        '7b9753371bbf2d7396d8a6ca5b76ea045240d95522a71db356042ce72e1b9a9f')))

if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).parent))
    import deploy_canonical_sounds as engine
    configure(engine)
    try:
        result=engine.main(sys.argv[1] if len(sys.argv)==2 else 'inspect')
        if result.get('installed') or result.get('verified'):
            helper=engine.CHECKPOINT/'deploy_canonical.py'
            if Path(__file__).resolve()!=helper.resolve():
                known_predecessor=hashlib.sha256(helper.read_bytes()).hexdigest()=='34517628fc03668b5eef96a7008a86d92164929455beb6259c37141a1ccc5c28'
                if helper.read_bytes() not in (Path(engine.__file__).read_bytes(),Path(__file__).read_bytes()) and not known_predecessor:raise RuntimeError('recovery-helper-drift')
                shutil.copyfile(engine.__file__,engine.CHECKPOINT/'deploy_canonical_sounds.py')
                shutil.copyfile(__file__,helper)
        result['ok']=True
    except Exception as error:result=dict(ok=False,code=str(error))
    (engine.BASE/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
