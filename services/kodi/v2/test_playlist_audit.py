import ast,copy,unittest
from pathlib import Path


class AuditTests(unittest.TestCase):
    def setUp(self):
        source=Path(__file__).parent/'tools/live_readonly_audit.py'
        tree=ast.parse(source.read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='check_inventory')
        namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec',optimize=2),namespace)
        self.check=namespace['check_inventory']

    def test_additional_playlist_is_counted_without_mutating_baseline(self):
        before=[dict(Id='one',Name='Fixture',details=dict(ItemIds=['song'],OpenAccess=False))]
        original=copy.deepcopy(before);current=copy.deepcopy(before)+[dict(Id='two',Name='New fixture')]
        self.assertEqual(self.check(before,current),1);self.assertEqual(before,original)
        self.assertEqual(self.check(before,copy.deepcopy(before)),0)

    def test_missing_changed_or_duplicate_original_is_never_ignored(self):
        before=[dict(Id='one',details=dict(ItemIds=['song'],OpenAccess=False))]
        for current in ([],[dict(Id='one',details=dict(ItemIds=['other'],OpenAccess=False))],
                [dict(Id='one',details=dict(ItemIds=['song'],OpenAccess=True))],before*2):
            with self.subTest(current=current),self.assertRaises(RuntimeError):self.check(before,current)
