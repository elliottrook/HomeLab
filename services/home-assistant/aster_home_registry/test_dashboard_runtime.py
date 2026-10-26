"""Exercise exporter integration without Home Assistant or a live household."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).parent/'custom_components/aster_home_registry'


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.outputs=[];self.scheduled=[];self.intervals=[];self.listeners=[]
        self.states=[types.SimpleNamespace(entity_id='light.room',state='on',attributes={'friendly_name':'Room'})]
        self.states_api=types.SimpleNamespace(get=lambda identity:next((s for s in self.states if s.entity_id==identity),None),
                                              async_all=lambda:self.states)
        async def executor(function,*args):return function(*args)
        self.hass=types.SimpleNamespace(states=self.states_api,async_add_executor_job=executor,
            bus=types.SimpleNamespace(async_listen=lambda event,callback:self.listeners.append((event,callback))))
        mods={key:types.ModuleType(key) for key in ('voluptuous','homeassistant','homeassistant.core',
            'homeassistant.const','homeassistant.helpers','homeassistant.helpers.entity_registry',
            'homeassistant.helpers.event','homeassistant.helpers.typing')}
        mods['voluptuous'].Schema=lambda *args,**kwargs:None
        mods['voluptuous'].ALLOW_EXTRA=object()
        mods['homeassistant.core'].HomeAssistant=object
        mods['homeassistant.const'].EVENT_STATE_CHANGED='state_changed'
        mods['homeassistant.helpers.typing'].ConfigType=dict
        mods['homeassistant.helpers.entity_registry'].async_get=lambda hass:types.SimpleNamespace(async_get=lambda identity:True)
        mods['homeassistant.helpers.event'].async_call_later=lambda hass,seconds,callback:self.scheduled.append((seconds,callback)) or object()
        mods['homeassistant.helpers.event'].async_track_time_interval=lambda hass,callback,interval:self.intervals.append((callback,interval))
        self.patch=patch.dict(sys.modules,mods);self.patch.start()
        spec=importlib.util.spec_from_file_location('aster_home_runtime_test',BASE/'__init__.py',submodule_search_locations=[str(BASE)])
        self.module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=self.module;spec.loader.exec_module(self.module)
        self.module.write_atomic=lambda report:self.outputs.append(('legacy',report))
        self.module.write_dashboard=lambda report:self.outputs.append(('dashboard',report))

    async def asyncTearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key.startswith('aster_home_runtime_test'):sys.modules.pop(key)

    async def test_opt_in_only(self):
        self.assertTrue(await self.module.async_setup(self.hass,{}))
        self.assertEqual(self.outputs,[]);self.assertEqual(self.listeners,[])

    async def test_legacy_unchanged_and_dashboard_separate(self):
        await self.module.async_setup(self.hass,{'aster_home_registry':{}})
        legacy,new=self.outputs
        self.assertEqual(legacy[1]['schema_version'],3)
        self.assertEqual(new[1]['schema_version'],4)
        self.assertEqual(new[1]['entities'][0]['id'],'light.room')
        self.assertEqual(self.intervals[0][1].total_seconds(),300)
        self.assertEqual(len(self.listeners),1)

    async def test_coalesces_events_without_repeated_rescheduling(self):
        await self.module.async_setup(self.hass,{'aster_home_registry':{}})
        callback=self.listeners[0][1]
        callback(types.SimpleNamespace(data={'entity_id':'person.owner'}))
        self.assertEqual(self.scheduled,[])
        for _ in range(100):callback(types.SimpleNamespace(data={'entity_id':'light.room'}))
        self.assertEqual(len(self.scheduled),1);self.assertEqual(self.scheduled[0][0],1)
        await self.scheduled[0][1]()
        callback(types.SimpleNamespace(data={'entity_id':'light.new_room'}))
        self.assertEqual(len(self.scheduled),2)

    async def test_projection_failure_preserves_legacy_and_old_timestamp(self):
        with patch.object(self.module,'project',side_effect=ValueError('synthetic')):
            with self.assertLogs(self.module.LOGGER,level='WARNING'):
                await self.module.async_setup(self.hass,{'aster_home_registry':{}})
        self.assertEqual([kind for kind,_ in self.outputs],['legacy'])

if __name__=='__main__':unittest.main()
