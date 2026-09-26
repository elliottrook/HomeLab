"""Portable structural and semantic vectors for candidate contract validators."""
import argparse
import hashlib
import json
from pathlib import Path
from pydantic import ValidationError
from contracts import CONTRACTS, Catalogue, Decision, DecisionRequest, validate_proposal

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def run():
    models={cls.__name__:cls for cls in CONTRACTS}
    corpus=HERE/'conformance-vectors.json'
    data=json.loads(corpus.read_text())
    assert data['schema_version']=='conformance-vectors.v1'
    results=[]
    for vector in data['vectors']:
        try:
            if vector['scope']=='structural':
                model=models[vector['contract']].model_validate(vector['input'])
                assert type(model).model_validate_json(model.model_dump_json())==model
            elif vector['scope']=='semantic':
                item=vector['input']
                validate_proposal(DecisionRequest.model_validate(item['request']),Decision.model_validate(item['decision']),Catalogue.model_validate(item['catalogue']),now=item['now'])
            else:
                raise AssertionError('unknown vector scope')
            accepted=True
        except (ValidationError,ValueError):
            accepted=False
        results.append({'id':vector['id'],'expected_accept':vector['accept'],'actual_accept':accepted,'passed':accepted==vector['accept']})
    files=[corpus,HERE/'contracts.py',HERE/'conformance.py',*sorted((ROOT/'schemas/aster').glob('*.json'))]
    return {'schema_version':'conformance-result.v1','all_passed':all(r['passed'] for r in results),'vector_count':len(results),'results':results,'manifest':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'limitations':['One Python validator implementation tested; cross-language compatibility unproven','No execution, calibration or production routing quality claim']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=run();args.output.write_text(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if result['all_passed'] else 1)
