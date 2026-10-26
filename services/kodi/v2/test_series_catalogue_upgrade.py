import hashlib,json,shutil,tempfile,unittest
from pathlib import Path

from build_series_catalogue_upgrade import build,digest
from build_series_preview import build as build_series
from series_catalogue_upgrade_install import run

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def fixture(root):
    candidate=root/'candidate';build_series(candidate)
    source=json.loads((candidate/'manifest.json').read_text())
    addon=root/'active';component=addon/'aster-series-preview24';component.mkdir(parents=True)
    retained=[row for row in source['files'] if row['path'] not in (
        'resources/lib/series_catalogue.py','resources/lib/series_seerr_client.py')]
    for row in retained:
        target=component/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(candidate/row['path'],target)
    old=dict(schema=1,kind='hp-series-player',component='aster-series-preview24',files=retained)
    write_json(component/'manifest.json',old);old_sha=sha((component/'manifest.json').read_bytes())
    search=addon/'aster-global-search-ui22';handoff=search/'resources/lib/search_handoff.py'
    handoff.parent.mkdir(parents=True)
    handoff.write_text("SERIES_SHA='"+old_sha+"'\nif len(rows)!=(6 if kind=='tvshow' else 48):raise ValueError()\n")
    search_manifest={'files':[{'path':'resources/lib/search_handoff.py','bytes':handoff.stat().st_size,
                               'sha256':sha(handoff.read_bytes())}]}
    write_json(search/'manifest.json',search_manifest);search_sha=sha((search/'manifest.json').read_bytes())
    skin=root/'skin';launcher=skin/'tools/aster_v2_series.py';launcher.parent.mkdir(parents=True)
    launcher.write_text("MANIFEST_SHA='"+old_sha+"'\nif len(manifest.get('files',[]))!=6:return False\n")
    family={'components':{'aster-series-preview24':{'files':6,'manifest_sha256':old_sha},
                          'aster-global-search-ui22':{'files':1,'manifest_sha256':search_sha}},
            'skin':{'tools/aster_v2_series.py':sha(launcher.read_bytes())}}
    write_json(addon/'family-manifest.json',family)
    return addon,skin,candidate


class SeriesCatalogueUpgradeTests(unittest.TestCase):
    def test_deterministic_build_and_reversible_install(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent);active,skin,candidate=fixture(root)
            one=root/'one';two=root/'two'
            first=build(active,skin,candidate,one);second=build(active,skin,candidate,two)
            self.assertEqual(first,second)
            storage=root/'storage';addon=storage/'.kodi/addons/script.asterruntime'
            live_skin=storage/'.kodi/addons/skin.asterhome'
            addon.parent.mkdir(parents=True);shutil.copytree(active,addon)
            (live_skin/'tools').mkdir(parents=True);shutil.copy2(
                skin/'tools/aster_v2_series.py',live_skin/'tools/aster_v2_series.py')
            result=run(one,storage,first,idle=lambda:True)
            self.assertTrue(result['installed'])
            manifest=json.loads((one/'manifest.json').read_text())
            self.assertEqual(digest((addon/'aster-series-preview24/manifest.json').read_bytes()),
                             manifest['component_manifest_sha256'])
            self.assertTrue((storage/'.aster-checkpoints/aster-series-catalogue1/retired-series').is_dir())

    def test_predecessor_drift_refuses_before_checkpoint(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent);active,skin,candidate=fixture(root);stage=root/'stage'
            pin=build(active,skin,candidate,stage)
            storage=root/'storage';addon=storage/'.kodi/addons/script.asterruntime'
            live_skin=storage/'.kodi/addons/skin.asterhome';addon.parent.mkdir(parents=True)
            shutil.copytree(active,addon);(live_skin/'tools').mkdir(parents=True)
            shutil.copy2(skin/'tools/aster_v2_series.py',live_skin/'tools/aster_v2_series.py')
            (live_skin/'tools/aster_v2_series.py').write_text('owner change')
            with self.assertRaisesRegex(ValueError,'live-drift'):
                run(stage,storage,pin,idle=lambda:True)
            self.assertFalse((storage/'.aster-checkpoints/aster-series-catalogue1').exists())


if __name__=='__main__':unittest.main()
