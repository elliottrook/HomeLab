"""Generate the two-file HP TV-show-only Select hook; never edit v1 source."""
import argparse,ast,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'skin.asterhome/tools/select_dispatch.py'

def dispatcher(source):
    needle='    if window_id == 10502 and focus_id == 50:\n'
    if source.count(needle)!=1:raise ValueError('unexpected-select-source')
    hook=('    if window_id == 10025 and focus_id == 50:\n'
          '        try:\n'
          '            from aster_v2_series import launch_selected_show\n'
          '        except ImportError:\n'
          '            pass\n'
          '        else:\n'
          '            if launch_selected_show():return\n')
    result=source.replace(needle,hook+needle);ast.parse(result);return result

def build(output,stage,sha):
    if re.fullmatch(r'aster-series-preview[1-9][0-9]*',stage) is None or re.fullmatch('[0-9a-f]{64}',sha) is None:
        raise ValueError('invalid-series-stage')
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('nonempty-output')
    original=SOURCE.read_bytes()
    files={'tools/select_dispatch.py':dispatcher(original.decode()).encode(),
        'tools/aster_v2_series.py':(HERE/'integration/aster_v2_series.py').read_text().replace('@SERIES_STAGE@',stage).replace('@SERIES_SHA@',sha).encode()}
    records=[]
    for name,data in sorted(files.items()):
        ast.parse(data);path=output/'files'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        records.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                            before_sha256=hashlib.sha256(original).hexdigest() if name.endswith('/select_dispatch.py') else None))
    manifest=dict(schema=1,kind='hp-series-integration',series_stage=stage,series_manifest_sha256=sha,files=records)
    path=output/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--stage',required=True);parser.add_argument('--sha',required=True)
    args=parser.parse_args();print(build(args.output,args.stage,args.sha))
