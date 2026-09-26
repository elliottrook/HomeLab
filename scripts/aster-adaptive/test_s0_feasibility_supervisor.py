"""Local invented fixtures only. Never connects to the proposed HomeLab target."""
import ast
import contextlib
import io
import copy
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import s0_feasibility_supervisor as s


class SupervisorTests(unittest.TestCase):
    def test_combined_streams_success(self):
        r=s.run_fixture('success')
        self.assertEqual(r['status'],'complete');self.assertEqual(r['retained_bytes'],22)
        self.assertEqual(r['output'],{'stdout':'fixture-out','stderr':'fixture-err'})
        self.assertTrue(r['reaped']);self.assertFalse(r['remote_stop_fallback']['needed'])

    def test_combined_and_stderr_flood(self):
        for name in ('flood-both','stderr-flood'):
            r=s.run_fixture(name)
            self.assertEqual(r['status'],'output-limit');self.assertEqual(r['retained_bytes'],8192)
            self.assertTrue(r['reaped']);self.assertTrue(r['remote_stop_fallback']['needed'])
            self.assertFalse(r['remote_stop_fallback']['executed'])

    def test_deadline_and_closed_pipes_do_not_hang(self):
        for name in ('timeout','closed-streams'):
            r=s.run_fixture(name,deadline=.1)
            self.assertEqual(r['status'],'timeout');self.assertTrue(r['killed']);self.assertTrue(r['reaped'])
            self.assertLess(r['elapsed_seconds'],3)

    def test_nonzero_and_invalid_output(self):
        self.assertEqual(s.run_fixture('nonzero')['status'],'child-failed')
        self.assertEqual(s.run_fixture('invalid-utf8')['status'],'invalid-output')

    def test_no_generic_command_or_path(self):
        for name in ('ssh','/usr/bin/true',['sh','-c','true']):
            with self.assertRaises(ValueError):s.run_fixture(name)
        for deadline in (0,-1,21,float('nan'),True):
            with self.assertRaises(ValueError):s.run_fixture('success',deadline=deadline)
        with self.assertRaises(PermissionError):s.execute_remote(approved=True)

    def test_spawn_only_exact_constant_local_argv(self):
        original=subprocess.Popen
        def checked(argv,**kwargs):
            self.assertEqual(argv,[sys.executable,'-I','-S','-B','-c',s.FIXTURES['success']])
            self.assertEqual(kwargs['env'],{'LANG':'C','LC_ALL':'C'})
            self.assertTrue(kwargs['close_fds']);self.assertTrue(kwargs['start_new_session'])
            return original(argv,**kwargs)
        with patch.object(s.subprocess,'Popen',side_effect=checked):s.run_fixture('success')

    def test_exact_loadstate(self):
        self.assertTrue(s.load_state_ok(0,b'LoadState=not-found\n',b''))
        for code,out,err in [(1,b'LoadState=not-found\n',b''),(0,b'LoadState=loaded\n',b''),
                             (0,b'',b''),(0,b'LoadState=not-found\n',b'warning')]:
            self.assertFalse(s.load_state_ok(code,out,err))

    def test_exact_command_payload_hash(self):
        proposal=s.command_proposal();s.verify_proposal(proposal)
        argv=proposal['commands']['run-proposal-only']
        inner=shlex.split(argv[-1]);self.assertEqual(inner[:4],['pct','exec','100','--'])
        self.assertEqual(inner[-1].encode(),s.PAYLOAD.read_bytes())
        changed=copy.deepcopy(proposal);changed['commands']['run-proposal-only'][-1]+=' '
        with self.assertRaises(ValueError):s.verify_proposal(changed)
        with patch.object(s,'PAYLOAD_SHA256','0'*64):
            with self.assertRaises(ValueError):s.command_proposal()

    def test_quoted_commands_roundtrip_and_disposable_execution(self):
        proposal=s.command_proposal()
        for name,source in [('create-canary',s.CREATE_SOURCE),('remove-canary',s.CLEANUP_SOURCE)]:
            argv=proposal['commands'][name]
            self.assertEqual(shlex.split(shlex.join(argv)),argv)
            inner=shlex.split(argv[-1]);self.assertEqual(inner[-1],source)
            ast.parse(source)
        # Preserve all source operations/quoting, substitute only the fixed path
        # to a disposable local path. No SSH, pct or remote path is executed.
        with tempfile.TemporaryDirectory(prefix='s0-argv-') as temp:
            target=str(Path(temp)/'canary dir with spaces')
            for source in (s.CREATE_SOURCE,s.CLEANUP_SOURCE):
                replacement=source.replace(json.dumps(s.CANARY_DIR),json.dumps(target))
                self.assertNotIn(s.CANARY_DIR,replacement)
                command=shlex.join([sys.executable,'-I','-S','-B','-c',replacement])
                result=subprocess.run(['/bin/sh','-c',command],stdin=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3,
                                      env={'LANG':'C','LC_ALL':'C'})
                self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(Path(target).exists())

    def bootstrap(self, environment):
        # Execute only the environment prefix; never socket/fork/canary operations.
        module=ast.parse(s.PAYLOAD.read_text());nodes=[]
        for node in module.body:
            if isinstance(node,ast.FunctionDef):break
            nodes.append(node)
        self.assertIsInstance(nodes[0],ast.Import)
        self.assertEqual([a.name for a in nodes[0].names],['os'])
        code=compile(ast.Module(body=nodes,type_ignores=[]),'<invented-bootstrap>','exec')
        output=io.StringIO();ns={};exitcode=0
        with patch.dict(os.environ,environment,clear=True),contextlib.redirect_stdout(output):
            try:exec(code,ns)
            except SystemExit as exc:exitcode=exc.code
            self.assertEqual(dict(os.environ),{})
        return ns,exitcode,output.getvalue()

    def test_inherited_environment_before_scrub(self):
        ns,code,out=self.bootstrap({'LANG':'C','LC_ALL':'C','INVOCATION_ID':'invented'})
        self.assertEqual(code,0);self.assertTrue(ns['checks']['inherited_environment_allowlisted'])
        self.assertIn('INVOCATION_ID',ns['initial_env_keys']);self.assertEqual(out,'')
        ns,code,out=self.bootstrap({'LANG':'C','LC_ALL':'C','UNEXPECTED_FIXTURE':'never-print-this-value'})
        self.assertEqual(code,1);self.assertFalse(ns['checks']['inherited_environment_allowlisted'])
        self.assertNotIn('never-print-this-value',out);self.assertNotIn('UNEXPECTED_FIXTURE',out)
        self.assertEqual(json.loads(out)['phase'],'environment-rejected')

    def test_bad_locale_and_sensitive_names_fail(self):
        for env in ({'LANG':'C'}, {'LANG':'wrong','LC_ALL':'C'},
                    {'LANG':'C','LC_ALL':'C','PYTHONPATH':'invented'},
                    {'LANG':'C','LC_ALL':'C','LD_PRELOAD':'invented'},
                    {'LANG':'C','LC_ALL':'C','SSH_AUTH_SOCK':'invented'}):
            _,code,_=self.bootstrap(env);self.assertEqual(code,1)

    def test_unit_environment_properties(self):
        self.assertIn('Environment=LANG=C LC_ALL=C',s.PROPERTIES)
        unset=next(p.split('=',1)[1].split() for p in s.PROPERTIES if p.startswith('UnsetEnvironment='))
        self.assertTrue({'PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT',
                         'DYLD_INSERT_LIBRARIES','SSH_AUTH_SOCK','GPG_AGENT_INFO','VAULT_TOKEN'}<=set(unset))

    def test_cleanup_refuses_changed_modes(self):
        with tempfile.TemporaryDirectory(prefix='s0-mode-') as temp:
            target=Path(temp)/'fixture'
            def run(source):
                code=source.replace(json.dumps(s.CANARY_DIR),json.dumps(str(target)))
                return subprocess.run([sys.executable,'-I','-S','-B','-c',code],
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3,env={'LANG':'C','LC_ALL':'C'})
            self.assertEqual(run(s.CREATE_SOURCE).returncode,0)
            self.assertEqual(target.stat().st_mode&0o777,0o755)
            self.assertEqual((target/'canary').stat().st_mode&0o777,0o644)
            target.chmod(0o700);self.assertNotEqual(run(s.CLEANUP_SOURCE).returncode,0)
            self.assertTrue((target/'canary').exists());target.chmod(0o755)
            (target/'canary').chmod(0o600);self.assertNotEqual(run(s.CLEANUP_SOURCE).returncode,0)
            self.assertTrue((target/'canary').exists());(target/'canary').chmod(0o644)
            self.assertEqual(run(s.CLEANUP_SOURCE).returncode,0)


if __name__=='__main__':unittest.main()
