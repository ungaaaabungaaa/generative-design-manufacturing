from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


class LoadSensitivityTests(unittest.TestCase):
    def test_cli_reports_actual_response_failures_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'loads.json'
            command = [sys.executable, 'scripts/load_sensitivity.py', '--loads', '25', '50', '500', '--out', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(len(report['designs']), 4)
            self.assertEqual(report['source_report_sha256'], sha256((ROOT / 'web/assets/report.json').read_bytes()).hexdigest())
            for name, loads in report['designs'].items():
                with self.subTest(design=name):
                    self.assertEqual([row['tip_load_n'] for row in loads], [25, 50, 500])
                    self.assertTrue(loads[1]['feasible'])
                    self.assertFalse(loads[2]['feasible'])
                    self.assertAlmostEqual(loads[0]['max_stress_mpa'] * 2, loads[1]['max_stress_mpa'])
                    self.assertEqual(loads[0]['heights_mm'], loads[2]['heights_mm'])
            before = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(output.read_bytes(), before)

    def test_invalid_loads_fail_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'loads.json'
            for loads in [('nan',), ('0',), ('50', '50'), ('5001',)]:
                result = subprocess.run([sys.executable, 'scripts/load_sensitivity.py', '--loads', *loads, '--out', str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(output.exists())
