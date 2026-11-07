"""Build only from the actual independent full postcheck; never perform LAN work."""
import argparse,ast,base64,hashlib,json,time
from pathlib import Path

H=Path(__file__).resolve().parent
REVIEW=Path('/private/tmp/b60-independent-r7-acceptance-source-review-v2-20261106.json')
REVIEW_SHA='c13b798b7f062f23159df25ca06d1a4b5d299f7c2fb552b01c600395f7a43c30'

def build(independent_path,independent_sha):
    independent_raw=Path(independent_path).read_bytes()
    assert hashlib.sha256(independent_raw).hexdigest()==independent_sha
    document=json.loads(independent_raw);assert document.get('source_only',False) is False
    post=document.get('result',document)
    sources=json.loads((H/'manifest.json').read_bytes())
    assert all(hashlib.sha256((H/n).read_bytes()).hexdigest()==sha for n,sha in sources.items())
    producer=(H/'acceptance_writer.py').read_bytes();reconciler=(H/'read_only_postcheck.py').read_bytes()
    review_raw=REVIEW.read_bytes();assert hashlib.sha256(review_raw).hexdigest()==REVIEW_SHA
    review=json.loads(review_raw);assert review['findings']==[]
    for name,raw in (('acceptance_writer.py',producer),('read_only_postcheck.py',reconciler)):
        assert review['source_sha256'][H.name+'/'+name]==hashlib.sha256(raw).hexdigest()
    tree=ast.parse(producer);validate=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
    ns={'SOURCE_SHA256':sources};exec(compile(ast.Module(body=[validate],type_ignores=[]),'reviewed-acceptance-predicates','exec'),ns);ns['validate'](post)
    assert post['finished_epoch']<=post['observed_epoch']<=time.time()
    values={'INDEPENDENT_BYTES':independent_raw,'INDEPENDENT_SHA256':independent_sha,
            'PRODUCER_SOURCE':producer,'PRODUCER_SHA256':hashlib.sha256(producer).hexdigest(),
            'PRODUCER_REVIEW_BYTES':review_raw,'PRODUCER_REVIEW_SHA256':REVIEW_SHA,
            'RECONCILER_SOURCE':reconciler,'RECONCILER_SHA256':hashlib.sha256(reconciler).hexdigest(),
            'SOURCE_SHA256':sources}
    header='import base64\n'
    for k,v in values.items():
        header+=k+'='+('base64.b64decode('+repr(base64.b64encode(v).decode())+')' if isinstance(v,bytes) else repr(v))+'\n'
    result=header.encode()+producer;compile(result,'source-bound-acceptance','exec')
    dest=Path('/private/tmp/b60-r7-controller-acceptance.py');dest.write_bytes(result)
    return {'payload_sha256':hashlib.sha256(result).hexdigest(),'producer_sha256':values['PRODUCER_SHA256'],'independent_postcheck_sha256':independent_sha,'source_sha256':sources,'root_write_attempted':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--independent-path',required=True);p.add_argument('--independent-sha256',required=True);args=p.parse_args()
    print(json.dumps(build(args.independent_path,args.independent_sha256),sort_keys=True))
