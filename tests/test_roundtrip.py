from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from design_lab.geometry import svg_export
from design_lab.mechanics import Config, InputError, evaluate
from design_lab.roundtrip import validate_svg


class RoundTripTests(unittest.TestCase):
    def test_svg_roundtrip_checks_nonround_dimensions_and_evaluator_volume(self):
        config = replace(Config(), length_mm=243.123456789, width_mm=9.87654321)
        heights = [18] * config.sections
        result = validate_svg(config, heights, svg_export(config, heights))
        expected = evaluate(config, heights)
        self.assertAlmostEqual(result['volume_mm3'], expected['volume_mm3'])
        self.assertAlmostEqual(result['area_mm2'], expected['volume_mm3'] / config.width_mm)
        self.assertEqual(result['length_mm'], config.length_mm)
        self.assertTrue(result['closed'])

    def test_altered_units_coordinates_closure_and_active_xml_are_rejected(self):
        config = Config()
        text = svg_export(config, [18] * config.sections)
        cases = [text.replace('240mm', '240px'), text.replace('0,-9', '0,-8', 1),
                 text.replace('0,-9"', '1,-9"'), text.replace('viewBox="0', 'transform="scale(2)" viewBox="0'),
                 '<!DOCTYPE svg [<!ENTITY x "x">]>' + text,
                 text.replace('<title>', '<script>unsafe</script><title>'),
                 text.replace('20,-9', 'nan,-9', 1), text * 1000]
        for svg in cases:
            with self.subTest(svg=svg[:80]), self.assertRaises(InputError):
                validate_svg(config, [18] * config.sections, svg)

    def test_cli_checks_all_bundled_designs_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'roundtrip.json'
            command = [sys.executable, 'scripts/check_svg_roundtrip.py', '--bundle', 'web/assets', '--out', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text())
            self.assertEqual(len(data['designs']), 4)
            self.assertEqual(len(data['source_report_sha256']), 64)
            for item in data['designs'].values():
                self.assertGreater(item['volume_mm3'], 0)
                self.assertEqual(len(item['svg_sha256']), 64)
            before = output.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            self.assertEqual(output.read_bytes(), before)
