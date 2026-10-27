from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from design_lab.__main__ import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err): code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_generate_complete_bundle_and_refuse_existing_directory(self):
        target = self.root / 'result'
        args = ['generate', '--out', str(target), '--seeds', '7', '--generations', '4', '--population', '8']
        code, stdout, stderr = self.run_cli(args)
        self.assertEqual(code, 0, stderr)
        report = json.loads((target / 'report.json').read_text())
        self.assertTrue(report['runs'][0]['best']['feasible'])
        self.assertEqual(len(list((target / 'designs').iterdir())), 6)
        self.assertIn('evolutionary', stdout)
        marker = target / 'keep.txt'; marker.write_text('unrelated')
        self.assertEqual(self.run_cli(args)[0], 1)
        self.assertEqual(marker.read_text(), 'unrelated')

    def test_bad_config_and_search_budget_create_no_partial_outputs(self):
        config = self.root / 'config.json'; target = self.root / 'result'
        for content in ['{bad', '{"width_mm":true}', '{"invented":1}', '[]', 'x' * 16385, '[' * 2000 + ']' * 2000]:
            with self.subTest(content=content[:30]):
                config.write_text(content)
                code, _, _ = self.run_cli(['generate', '--out', str(target), '--config', str(config)])
                self.assertEqual(code, 2); self.assertFalse(target.exists())
        code, _, _ = self.run_cli(['generate', '--out', str(target), '--seeds', '7', '7'])
        self.assertEqual(code, 2); self.assertFalse(target.exists())

    def test_symlinked_config_is_rejected(self):
        source = self.root / 'real.json'; source.write_text('{}')
        link = self.root / 'link.json'; link.symlink_to(source)
        code, _, _ = self.run_cli(['generate', '--out', str(self.root / 'out'), '--config', str(link)])
        self.assertEqual(code, 2)

    def test_partial_valid_config_keeps_defaults_and_changes_the_actual_study(self):
        config=self.root/'config.json';config.write_text('{"tip_load_n":25}')
        target=self.root/'custom'
        code,_,stderr=self.run_cli(['generate','--out',str(target),'--config',str(config),'--seeds','7','--generations','4','--population','8'])
        self.assertEqual(code,0,stderr)
        report=json.loads((target/'report.json').read_text())
        self.assertEqual(report['config']['tip_load_n'],25)
        self.assertEqual(report['config']['length_mm'],240)
        self.assertTrue(report['runs'][0]['best']['feasible'])

    def test_older_runtime_json_recursion_error_is_a_controlled_input_error(self):
        config=self.root/'config.json';config.write_text('{}')
        with patch('design_lab.__main__.json.loads',side_effect=RecursionError('nested JSON')):
            code,_,stderr=self.run_cli(['generate','--out',str(self.root/'out'),'--config',str(config)])
        self.assertEqual(code,2);self.assertNotIn('Traceback',stderr)


if __name__ == '__main__': unittest.main()
