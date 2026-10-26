import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('dashboard_contract',Path(__file__).parent/'custom_components/aster_home_registry/dashboard_contract.py')
contract=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(contract)
def entity(identity,state,**attrs):return dict(entity_id=identity,state=state,attributes=attrs)

class DashboardTests(unittest.TestCase):
    def test_display_only_no_tokens_urls_person_or_mobile(self):
        rows=[entity('light.room','on',access_token='secret',friendly_name='Room'),
              entity('person.owner','home',latitude=123),
              entity('camera.entry','idle',entity_picture='http://private?token=secret'),
              entity('sensor.iphone_battery','50',device_class='battery',unit_of_measurement='%')]
        output=contract.project(rows);self.assertEqual(len(output['entities']),2)
        text=json.dumps(output)
        for banned in ('secret','http','latitude','person.owner','iphone'):self.assertNotIn(banned,text)

    def test_measurements_units_ranges_and_unavailable(self):
        for state,unit,has in (('20','°C',True),('68','°F',True),('nan','°C',False),
                               ('999','°C',False),('20','K',False),('unavailable','°C',False)):
            row=contract.project([entity('sensor.room',state,device_class='temperature',unit_of_measurement=unit)])['entities'][0]
            self.assertEqual('value' in row,has)
            if not has:self.assertNotEqual(row['availability'],'available')

    def test_weather_drops_forecast_coordinates(self):
        row=contract.project([entity('weather.home','sunny',temperature=18,temperature_unit='°C',
                                      humidity=50,forecast=['secret'],latitude=23)])['entities'][0]
        self.assertEqual(row['condition'],'sunny');self.assertEqual(row['humidity'],50)
        self.assertNotIn('forecast',row);self.assertNotIn('latitude',row)

    def test_timer_structured_not_service_commands(self):
        row=contract.project([entity('timer.cooking','active',remaining='0:05:00',
                                    finishes_at='2026-10-26T12:00:00+00:00',editable=True)])['entities'][0]
        self.assertEqual(row['remaining'],'0:05:00');self.assertNotIn('editable',row)
        for bad in ('0:99:99','command','http://private'):
            row=contract.project([entity('timer.cooking','active',remaining=bad)])['entities'][0]
            self.assertNotIn('remaining',row)

    def test_names_and_only_display_classes(self):
        rows=contract.project([entity('light.one','on',friendly_name='[B]One[/B]'),
            entity('light.two','off',friendly_name='http://secret'),
            entity('sensor.power','42',device_class='power',unit_of_measurement='W'),
            entity('binary_sensor.leak','off',device_class='moisture'),
            entity('binary_sensor.route','on',device_class='connectivity')])['entities']
        self.assertEqual(len(rows),3)
        for row in rows:self.assertNotIn('[',row['name']);self.assertNotIn('http',row['name'])

    def test_limits_duplicates_and_sorted_deterministic_rows(self):
        with self.assertRaisesRegex(ValueError,'entity-limit'):
            contract.project([entity('light.room_'+str(i),'on') for i in range(257)])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            contract.project([entity('light.one','on')]*2)
        rows=contract.project([entity('light.z','on'),entity('light.a','off')])['entities']
        self.assertEqual([r['id'] for r in rows],['light.a','light.z'])

    def test_atomic_private_output_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);legacy=root/'latest.json';legacy.write_text('legacy')
            with patch.object(contract,'OUTPUT',root/'dashboard.json'):
                contract.write_dashboard(contract.project([entity('light.one','on')]))
                self.assertEqual(contract.OUTPUT.stat().st_mode&0o777,0o600)
                self.assertEqual(json.loads(contract.OUTPUT.read_text())['schema_version'],4)
            self.assertEqual(legacy.read_text(),'legacy')
            self.assertEqual(sorted(p.name for p in root.iterdir()),['dashboard.json','latest.json'])

if __name__=='__main__':unittest.main()
