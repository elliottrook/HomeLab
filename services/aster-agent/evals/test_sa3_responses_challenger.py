import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('challenger',Path(__file__).with_name('sa3_responses_challenger.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=m.request_payload('sanitized packet','gpt-6-astra')
m.validate_configuration(p)
assert p['model']=='gpt-6-astra' and p['store'] is False and 'tools' not in p
print('responses_challenger_contract_ok')
