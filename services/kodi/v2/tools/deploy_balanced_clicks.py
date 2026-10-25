"""Pinned balance correction, with exact per-box predecessor and recovery."""
import json,shutil,sys,time
from pathlib import Path

def configure(engine):
    from deploy_canonical_clicks import configure as clicks
    clicks(engine)
    engine.ORIGINALS={'AsterTV':engine.ORIGINALS['AsterTV'],'AsterTVProd':dict(engine.EXPECTED)}
    engine.BASE=Path('/storage/.aster-staging/aster-balanced-clicks-20261025')
    engine.CHECKPOINT=Path('/storage/.aster-checkpoints/aster-balanced-clicks-20261025')
    engine.TRANSFORM=dict(left_gain=0.6227221498528474,right_gain=1,left_attenuation_db=-4.114113728199796,
        normalization=False,no_boost=True,source_commit=engine.SOURCE_COMMIT)
    engine.MASTER_EXPECTED=dict(zip(engine.MASTER_EXPECTED,(
        '9c42b6f5825b60043912902b788cf817056b584006feca99d460a6aff910c417',
        'b9f564de7ad8e6a54f75fd016a65611131b4e2c98f1c959138df2634096d710f',
        'b36cdde11cbf4cf3f163048247cdfd267c98d3c1c7c6f214c04e433e0f55e71d',
        '08e7840b28b5e392e03062f1890f7e36a05846dc42fdb4c42433f06cae82ba83',
        '7b42311967008bf7e7e41d3c219b8ddc8562e00efab335b63d1a4d814a8b6b47',
        'daf4f464a9abdb36bcbef285dae4802fe3aa0b86b6016ef01bb8921ee1f373f2',
        '992de4d370044f9e01be1935f9a2d309cc5172d08466824e88b13b7dda19ab5d')))
    engine.EXPECTED=dict(zip(engine.MASTER_EXPECTED,(
        '6c2edc8e86279053e99e49cfac37649aee1e3250049f9beff279d6b74dc65026',
        'f458261b3e8dfbc3521e642fda5f9f175af6ccb7c335e7bf9ad88fede474cd89',
        'f22d1b475eb698dff16dcd7a03110203aa739248d6daddc6ab3f8bcf32a7723e',
        'b75da71b1a94b42fabdd34b5082840890d0950886534b0c2731221edae345a08',
        '3e0118c141031dd4ca2b6628d1fdcef0359749b8daba293d5e2733fc35ed33f7',
        'deff80a6905c64329c3d2813cf228fac73308bfa9cd70c87f879f063caa239b9',
        '0bd67a6b86e0c18c5451a7ad5effcee5d9bd6906a3908195a84e333bd7cceab4')))

if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).parent))
    import deploy_canonical_sounds as engine
    configure(engine)
    try:
        result=engine.main(sys.argv[1] if len(sys.argv)==2 else 'inspect')
        if result.get('installed') or result.get('verified'):
            helper=engine.CHECKPOINT/'deploy_canonical.py'
            if Path(__file__).resolve()!=helper.resolve():
                if helper.read_bytes() not in (Path(engine.__file__).read_bytes(),Path(__file__).read_bytes()):raise RuntimeError('recovery-helper-drift')
                for name in ('deploy_canonical_sounds.py','deploy_canonical_clicks.py'):
                    shutil.copyfile(Path(__file__).with_name(name),engine.CHECKPOINT/name)
                shutil.copyfile(__file__,helper)
        result['ok']=True
    except Exception as error:result=dict(ok=False,code=str(error))
    (engine.BASE/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
