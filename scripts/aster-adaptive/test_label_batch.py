import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from validate_label_batch import FORBIDDEN, MAX_BYTES, validate, validate_file


def row():
    return dict(case_id='case-one',family_id='family-one',split='train',category='timer',content_ref='fixture-one',origin='synthetic_fixture',retention='synthetic-git',content_review='synthetic-fixture-only',labels=None)


def batch():
    return dict(schema_version='label-batch.v1',protocol='m3-human-labels-draft-v1',data_class='synthetic-design-only',rows=[row()])


def labels():
    return dict(provenance='synthetic-test',required=['timer'],optional=[],prohibited=sorted(FORBIDDEN),acceptable_statuses=['plan'],sensitivity='public',cloud='public-only',adjudication='synthetic-fixture-only')


class LabelDesignTests(unittest.TestCase):
    def test_empty_template_no_claim(self):
        b=batch();b['rows']=[];r=validate(b)
        self.assertEqual(r['human_labels_verified'],0);self.assertFalse(r['evaluation_authorized'])

    def test_fixture_has_no_collection_or_network(self):
        b=batch();b['rows'][0]['labels']=labels()
        with patch('socket.socket',side_effect=AssertionError('no network')),patch('subprocess.Popen',side_effect=AssertionError('no subprocess')):
            r=validate(b)
        self.assertEqual(r['synthetic_fixture_labels'],1);self.assertFalse(r['collection_authorized'])

    def test_no_real_or_claimed_human_data(self):
        for where,key,value in [('batch','data_class','real'),('row','origin','real'),('row','retention','private'),('labels','provenance','human-verified'),('labels','adjudication','human-accepted')]:
            b=batch();b['rows'][0]['labels']=labels();target={'batch':b,'row':b['rows'][0],'labels':b['rows'][0]['labels']}[where];target[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(b)

    def test_raw_content_and_extra_fields_rejected(self):
        for key in ['text','prompt','email','credential','notes']:
            b=batch();b['rows'][0][key]='synthetic-canary'
            with self.assertRaises(ValueError):validate(b)

    def test_family_never_crosses_splits(self):
        b=batch();other=row();other.update(case_id='case-two',split='test',content_ref='fixture-two');b['rows'].append(other)
        with self.assertRaises(ValueError):validate(b)

    def test_alias_reference_cannot_cross_families(self):
        b=batch();other=row();other.update(case_id='case-two',family_id='family-two',split='test');b['rows'].append(other)
        with self.assertRaises(ValueError):validate(b)

    def test_duplicate_case(self):
        b=batch();b['rows']*=2
        with self.assertRaises(ValueError):validate(b)

    def test_conflicts_and_unknown_capabilities(self):
        for key,value in [('optional',['timer']),('required',['unknown']),('prohibited',[])]:
            b=batch();b['rows'][0]['labels']=labels();b['rows'][0]['labels'][key]=value
            with self.assertRaises(ValueError):validate(b)

    def test_sensitive_egress_denied(self):
        for sensitivity in ['internal','personal','excluded']:
            b=batch();b['rows'][0]['labels']=labels();b['rows'][0]['labels']['sensitivity']=sensitivity
            with self.assertRaises(ValueError):validate(b)

    def test_excluded_event_cannot_survive_as_a_label(self):
        b=batch();b['rows'][0]['labels']=labels()
        b['rows'][0]['labels'].update(sensitivity='excluded',cloud='forbidden')
        with self.assertRaises(ValueError):validate(b)

    def test_private_capability_inherits_local_personal_boundary(self):
        for cap in ('calendar','private_context','local_join'):
            for slot in ('required','optional'):
                b=batch();b['rows'][0]['labels']=labels();lab=b['rows'][0]['labels'];lab[slot]=[cap]
                with self.subTest(cap=cap,slot=slot),self.assertRaises(ValueError):validate(b)
                lab.update(sensitivity='personal',cloud='forbidden')
                self.assertEqual(validate(b)['human_labels_verified'],0)

    def test_sysadmin_and_lab_reads_require_internal_boundary(self):
        for category,cap in [('sysadmin','timer'),('timer','lab_read')]:
            b=batch();b['rows'][0]['category']=category;b['rows'][0]['labels']=labels();lab=b['rows'][0]['labels'];lab['required']=[cap]
            with self.assertRaises(ValueError):validate(b)
            lab.update(sensitivity='internal',cloud='forbidden');validate(b)

    def test_mixed_route_cannot_export_private_context(self):
        b=batch();b['rows'][0]['category']='mixed';b['rows'][0]['labels']=labels()
        with self.assertRaises(ValueError):validate(b)

    def test_content_review_is_explicit_but_never_human_authenticated(self):
        b=batch();b['rows'][0]['labels']=labels()
        for state in ('not-reviewed','human-approved'):
            b['rows'][0]['content_review']=state
            with self.assertRaises(ValueError):validate(b)
        b['rows'][0]['content_review']='synthetic-fixture-only'
        self.assertEqual(validate(b)['human_labels_verified'],0)

    def test_required_capability_needs_plan(self):
        b=batch();b['rows'][0]['labels']=labels();b['rows'][0]['labels']['acceptable_statuses']=['clarify']
        with self.assertRaises(ValueError):validate(b)

    def test_bad_types_versions_and_limits(self):
        for key,value in [('schema_version','other'),('rows',{}),('rows',[row()]*301)]:
            b=batch();b[key]=value
            with self.assertRaises(ValueError):validate(b)

    def test_duplicate_json_and_oversize(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'batch.json'
            for raw in [b'{"rows":[],"rows":[]}',b' '*(MAX_BYTES+1)]:
                p.write_bytes(raw)
                with self.assertRaises(ValueError):validate_file(p)


if __name__=='__main__':unittest.main()
