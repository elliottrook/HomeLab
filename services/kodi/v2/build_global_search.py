"""Immutable HP search stages; optional native Home entry and accepted-page links."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(output,details=False,handoff=False,stage='aster-global-search-ui5'):
    output=Path(output)
    if output.exists():raise ValueError('immutable-search-stage')
    files={p.relative_to(HERE/'search_native').as_posix():p.read_bytes()
           for p in (HERE/'search_native').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if not details:files.pop('overlay/custom_1128_searchdetails.xml',None)
    files['resources/lib/global_search.py']=(HERE/'global_search.py').read_bytes()
    if details:
        from build_series_integration import dispatcher as series_dispatcher
        from search_integration import dispatcher
        original=(HERE.parent/'skin.asterhome/tools/select_dispatch.py').read_text()
        files['overlay/select_dispatch.py']=dispatcher(series_dispatcher(original).encode())
        files['resources/lib/search_details.py']=(HERE/'search_details.py').read_bytes()
    if handoff:
        if not details:raise ValueError('handoff-needs-details')
        from search_integration import window_dispatcher,home_entry
        import xml.etree.ElementTree as ET
        files['overlay/select_dispatch.py']=window_dispatcher(files['overlay/select_dispatch.py'])
        files['overlay/Home.xml']=home_entry((HERE.parent/'skin.asterhome/1080i/Home.xml').read_bytes(),stage)
        files['resources/lib/search_handoff.py']=(HERE/'search_handoff.py').read_bytes()
        root=ET.fromstring(files['overlay/custom_1127_search.xml']);root.set('type','window')
        root.find(".//control[@id='40']/onclick").text='ActivateWindow(Home)'
        files['overlay/custom_1127_search.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        root=ET.fromstring(files['overlay/custom_1128_searchdetails.xml'])
        hint=next(c for c in root.findall('.//control') if 'Player links are the next' in (c.findtext('label') or ''))
        hint.find('label').text='$INFO[Window(Home).Property(AsterSearch.DetailHint)]'
        back=root.find(".//control[@id='10']")
        back.find('left').text='1290';back.find('width').text='470'
        back.find('onleft').text='11';back.find('onright').text='11'
        button=ET.SubElement(root.find('controls'),'control',dict(type='button',id='11'))
        for key,value in dict(left=760,top=955,width=470,height=64,label='$INFO[Window(Home).Property(AsterSearch.OpenLabel)]',
            visible='String.IsEqual(Window(Home).Property(AsterSearch.CanOpen),true)',font='font28',
            textcolor='asterCharcoal',focusedcolor='asterGreen',align='center',aligny='center',
            onclick='SetProperty(AsterSearch.Command,open,home)',onup=21,ondown=21,onleft=10,onright=10).items():
            ET.SubElement(button,key).text=str(value)
        ET.SubElement(button,'texturefocus',dict(border='20',colordiffuse='asterGreen')).text='special://skin/media/ui-compact-card-ring.png'
        ET.SubElement(button,'texturenofocus')
        files['overlay/custom_1128_searchdetails.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    output.mkdir(parents=True)
    rows=[]
    for name,data in sorted(files.items()):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(schema=1,kind='hp-search-playerlinks' if handoff else 'hp-search-details' if details else 'hp-search-preview',files=rows)
    if details:
        from search_integration import BEFORE
        manifest.update(previous_manifest_sha256='97439284ffadb61a6375853569cabdc2f085c5f41b8d3a51fbdabdf66136b6bc',
                        dispatcher_before_sha256=BEFORE)
    if handoff:
        from search_integration import HOME_BEFORE,DETAILS_BEFORE
        manifest.update(stage=stage,previous_manifest_sha256='e754a024360a05a53ff3fb3d4c34b715e52076af9f4a51efa742aa6dcc8b2246',
                        home_before_sha256=HOME_BEFORE,details_dispatcher_before_sha256=DETAILS_BEFORE)
    data=(json.dumps(manifest,indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--details',action='store_true')
    parser.add_argument('--handoff',action='store_true');parser.add_argument('--stage',default='aster-global-search-ui5')
    args=parser.parse_args();print(build(args.output,args.details,args.handoff,args.stage))
