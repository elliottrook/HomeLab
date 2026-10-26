from datetime import datetime,timedelta,timezone
import json
import unittest
from home_status_model import view

NOW=datetime(2026,10,26,5,tzinfo=timezone.utc)
def payload(rows,stamp=NOW):return json.dumps(dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',observed_at=stamp.isoformat(),entities=rows)).encode()
LIGHT=dict(id='light.room',name='Room',kind='light',availability='available',state='on')

class HomeStatusTests(unittest.TestCase):
    def test_values_and_lighting_filter(self):
        raw=payload([LIGHT,dict(id='sensor.temperature',name='Room temperature',kind='temperature',availability='available',value=20,unit='°C')])
        result=view(raw,NOW);self.assertEqual(result.state,'fresh');self.assertEqual(len(result.rows),2)
        self.assertEqual(result.properties['LightValue'],'1 on · 1/1 available')
        self.assertEqual(result.properties['TemperatureValue'],'20°C')
        self.assertEqual(view(raw,NOW,'lighting').rows,(('Room','On'),))

    def test_missing_stale_future_hide_values(self):
        for raw in (b'',payload([LIGHT],NOW-timedelta(seconds=601)),payload([LIGHT],NOW+timedelta(seconds=11))):
            result=view(raw,NOW);self.assertNotEqual(result.state,'fresh')
            self.assertEqual(result.properties['LightValue'],'Unavailable')

    def test_unknown_and_unavailable_not_fabricated(self):
        result=view(payload([dict(LIGHT,state='unavailable',availability='unavailable')]),NOW)
        self.assertEqual(result.rows,(('Room','Unavailable'),));self.assertIn('0/1',result.properties['LightValue'])

    def test_invalid_or_extraneous_fields_fail_closed(self):
        for row in (dict(LIGHT,token='secret'),dict(LIGHT,name='[B]Room'),dict(LIGHT,name='http://secret'),
                    dict(LIGHT,availability='unknown'),dict(LIGHT,id='person.room')):
            self.assertEqual(view(payload([row]),NOW).state,'invalid')

    def test_duplicates_limits_and_numeric_bounds(self):
        self.assertEqual(view(payload([LIGHT,LIGHT]),NOW).state,'invalid')
        self.assertEqual(view(payload([LIGHT]*257),NOW).state,'invalid')
        for value in (True,float('nan'),float('inf'),999):
            row=dict(id='sensor.room',name='Room',kind='temperature',availability='available',value=value,unit='°C')
            self.assertEqual(view(payload([row]),NOW).state,'invalid')

    def test_leak_has_meaningful_label(self):
        row=dict(id='binary_sensor.leak',name='Kitchen leak',kind='moisture',availability='available',state='off')
        self.assertEqual(view(payload([row]),NOW).rows,(('Kitchen leak','Dry'),))

if __name__=='__main__':unittest.main()
