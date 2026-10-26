from dataclasses import replace
import unittest
from idle_policy import Config,Observation,Context,Session,decide

IDLE=Observation(180,False,False,False,False)

class IdlePolicyTests(unittest.TestCase):
    def test_default_black_and_exact_threshold(self):
        self.assertEqual(decide(Config(),IDLE).effect,'black')
        self.assertFalse(decide(Config(),replace(IDLE,idle_seconds=179.999)).enter)
    def test_selected_modes_and_unsupported_aster_fallback(self):
        for mode in ('aster','dim','black'):
            self.assertEqual(decide(Config(mode),IDLE,aster_supported=True).effect,mode)
        self.assertEqual(decide(Config('aster'),IDLE).effect,'black')
        self.assertEqual(decide(Config('aster'),IDLE,aster_supported=1).effect,'black')
    def test_disabled_never_enters(self):
        self.assertFalse(decide(Config('disabled'),replace(IDLE,idle_seconds=None)).enter)
    def test_unknown_or_malformed_state_never_enters(self):
        for value in (None,True,-1,float('inf'),float('nan'),'180'):
            self.assertFalse(decide(Config(),replace(IDLE,idle_seconds=value)).enter)
        for field in ('media_active','alarm_active','busy','sensitive_surface'):
            for value in (None,1,'false'):
                self.assertFalse(decide(Config(),replace(IDLE,**{field:value})).enter)
    def test_media_including_paused_must_block(self):
        self.assertFalse(decide(Config(),replace(IDLE,media_active=True)).enter)
    def test_alarm_and_interaction_block(self):
        for field in ('alarm_active','busy'):
            self.assertFalse(decide(Config(),replace(IDLE,**{field:True})).enter)
    def test_sensitive_surface_is_black_even_with_dim_or_branding_selected(self):
        for mode in ('dim','aster','black'):
            self.assertEqual(decide(Config(mode),replace(IDLE,sensitive_surface=True),aster_supported=True).effect,'black')
    def test_configuration_is_bounded(self):
        for mode,minutes in (('other',3),('black',0),('black',61),('dim',True),('aster',3.0)):
            with self.assertRaises(ValueError):Config(mode,minutes)
        self.assertTrue(decide(Config('black',60),replace(IDLE,idle_seconds=3600)).enter)
    def test_first_navigation_select_back_and_home_are_consumed_once(self):
        source=Context(10004,206)
        for kind in ('navigation','select','back','home'):
            session=Session(source);wake=session.wake(kind,source,owned_visible=True,foreign_media=False)
            self.assertTrue(wake.consume);self.assertTrue(wake.close_owned);self.assertEqual(wake.restore_focus,206)
            self.assertFalse(session.wake(kind,source,owned_visible=True,foreign_media=False).consume)
    def test_changed_context_or_foreign_media_prevents_restoration(self):
        source=Context(10004,206)
        for underlying,media in ((Context(10000,206),False),(Context(10004,200),False),(source,True),(source,None)):
            wake=Session(source).wake('select',underlying,owned_visible=True,foreign_media=media)
            self.assertTrue(wake.consume);self.assertIsNone(wake.restore_focus)
    def test_foreign_overlay_unknown_ownership_and_system_inputs_are_not_intercepted(self):
        source=Context(10004,206)
        for kind,owned in (('select',False),('select',None),('volume',True),('power',True),('unknown',True)):
            session=Session(source);wake=session.wake(kind,source,owned_visible=owned,foreign_media=False)
            self.assertFalse(wake.consume);self.assertFalse(wake.close_owned);self.assertFalse(session.closed)
    def test_context_types_and_bounds(self):
        for window,focus in ((True,206),(10004,False),(0,1),(10000,0),(100000,206)):
            with self.assertRaises(ValueError):Context(window,focus)
