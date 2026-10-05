"""Bounded metadata-only label-design validator; never a collection or approval path."""
import argparse
import json
import re
from pathlib import Path

CLASSES = frozenset({'timer','home','media','facts','calendar','web','mixed','personal','sysadmin','ambiguous'})
CAPABILITIES = frozenset({'timer','home','media','facts','calendar','web','local_join','lab_read','private_context'})
FORBIDDEN = frozenset({'shell','credentials','automatic_approval','cloud_private_export'})
SPLITS = frozenset({'train','dev','calibration','test'})
STATUSES = frozenset({'plan','clarify','abstain','deny','unsupported'})
ID = re.compile(r'^[a-z][a-z0-9-]{0,63}$')
MAX_BYTES=256*1024


def reject(condition, reason):
    if condition: raise ValueError(reason)


def unique(pairs):
    result={}
    for key,value in pairs:
        reject(key in result,'duplicate JSON key')
        result[key]=value
    return result


def exact(obj, fields):
    reject(type(obj) is not dict or set(obj)!=set(fields),'unexpected fields')


def identifier(value):
    reject(type(value) is not str or ID.fullmatch(value) is None,'invalid opaque identifier')


def members(value, allowed):
    reject(type(value) is not list or any(type(x) is not str for x in value),'invalid label list')
    reject(len(value)!=len(set(value)) or not set(value)<=allowed,'duplicate or unknown label')
    return set(value)


def validate(batch):
    exact(batch, {'schema_version','protocol','data_class','rows'})
    reject(batch['schema_version']!='label-batch.v1' or batch['protocol']!='m3-human-labels-draft-v1','unknown protocol')
    reject(batch['data_class']!='synthetic-design-only','real collection is not authorized')
    rows=batch['rows'];reject(type(rows) is not list or len(rows)>300,'invalid row count')
    ids=set();family_splits={}; handles={}; adjudicated=0
    counts={name:0 for name in SPLITS}
    for row in rows:
        exact(row, {'case_id','family_id','split','category','content_ref','origin','retention','content_review','labels'})
        for key in ('case_id','family_id','content_ref'):identifier(row[key])
        reject(row['case_id'] in ids,'duplicate case');ids.add(row['case_id'])
        reject(type(row['split']) is not str or row['split'] not in SPLITS,'invalid split')
        reject(type(row['category']) is not str or row['category'] not in CLASSES,'invalid category')
        reject(row['origin']!='synthetic_fixture','real interaction is not allowed in this design tool')
        reject(row['retention']!='synthetic-git','unsupported retention')
        prior=family_splits.setdefault(row['family_id'],row['split'])
        reject(prior!=row['split'],'family crosses splits')
        prior=handles.setdefault(row['content_ref'],row['family_id'])
        reject(prior!=row['family_id'],'content reference reused across families')
        counts[row['split']]+=1
        reject(row['content_review'] not in ('not-reviewed','synthetic-fixture-only'),'unverified content-review assertion')
        labels=row['labels']
        if labels is None:continue
        exact(labels, {'provenance','required','optional','prohibited','acceptable_statuses','sensitivity','cloud','adjudication'})
        reject(labels['provenance'] not in ('pending-human','synthetic-test'),'human authenticity is not established here')
        req=members(labels['required'],CAPABILITIES);opt=members(labels['optional'],CAPABILITIES)
        prohibited=members(labels['prohibited'],CAPABILITIES|FORBIDDEN)
        reject(bool(req&opt or req&prohibited or opt&prohibited),'conflicting capability labels')
        reject(not FORBIDDEN<=prohibited,'mandatory prohibited labels missing')
        statuses=members(labels['acceptable_statuses'],STATUSES)
        reject(not statuses,'missing acceptable status')
        reject(req and 'plan' not in statuses,'required capabilities without acceptable plan')
        reject(labels['sensitivity'] not in ('public','internal','personal'),'excluded or invalid sensitivity')
        reject(labels['cloud'] not in ('forbidden','public-only','unresolved'),'invalid egress label')
        reject(labels['sensitivity'] in ('personal','internal','excluded') and labels['cloud']!='forbidden','sensitive egress must remain forbidden')
        reject(labels['adjudication'] not in ('pending','synthetic-fixture-only'),'human adjudication cannot be manufactured')
        requested=req|opt
        personal=bool(requested & {'calendar','private_context','local_join'}) or row['category']=='mixed'
        internal=bool(requested & {'lab_read'}) or row['category']=='sysadmin'
        reject(personal and (labels['sensitivity']!='personal' or labels['cloud']!='forbidden'),'private capability requires personal local-only label')
        reject(internal and (labels['sensitivity'] not in ('internal','personal') or labels['cloud']!='forbidden'),'lab capability requires internal local-only label')
        reject(labels['adjudication']=='synthetic-fixture-only' and row['content_review']!='synthetic-fixture-only','fixture content review missing')
        adjudicated+=labels['adjudication']=='synthetic-fixture-only'
    return {'schema_version':'label-validation.v1','rows':len(rows),'families':len(family_splits),'split_rows':counts,
            'synthetic_fixture_labels':adjudicated,'human_labels_verified':0,'collection_authorized':False,
            'evaluation_authorized':False,'limitations':['Metadata only; content equivalence and human identity are unverified','No real prompts or labels are collected; no model or network calls']}


def validate_file(path):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    reject(len(raw)>MAX_BYTES,'batch exceeds size limit')
    return validate(json.loads(raw,object_pairs_hook=unique))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('batch',type=Path);args=parser.parse_args()
    try: print(json.dumps(validate_file(args.batch),sort_keys=True))
    except (ValueError,TypeError,KeyError,RecursionError):
        raise SystemExit('Batch rejected; no input content printed')
