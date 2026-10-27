from dataclasses import replace
import json
import unittest
from xml.etree import ElementTree

from design_lab.mechanics import Config, InputError, evaluate, uniform_baseline
from design_lab.search import search, benchmark, repair
from design_lab.geometry import contour, svg_export, dxf_export, scad_export


class SearchTests(unittest.TestCase):
    def test_seeded_search_is_deterministic_and_never_loses_feasible_baseline(self):
        cfg = Config(); base = uniform_baseline(cfg)
        a = search(cfg, seed=7, generations=12, population=16)
        b = search(cfg, seed=7, generations=12, population=16)
        self.assertEqual(a, b)
        self.assertEqual(a['evaluations'], 16 * 13)
        self.assertEqual(len(a['history']), 13)
        self.assertLessEqual(a['best']['volume_mm3'], base['volume_mm3'])
        volumes = [item['volume_mm3'] for item in a['history']]
        self.assertEqual(volumes, sorted(volumes, reverse=True))
        for item in a['history']:
            self.assertTrue(evaluate(cfg, item['heights_mm'])['feasible'])

    def test_repair_respects_quantized_monotonic_step_constraints(self):
        cfg = Config()
        heights = repair(cfg, [30, 4, 18, 20, 8, 9, 30, 6, 16, 10, 22, 4])
        result = evaluate(cfg, heights)
        self.assertNotIn('monotonic-height', result['violations'])
        self.assertNotIn('adjacent-step', result['violations'])

    def test_benchmark_reductions_use_the_same_uniform_denominator(self):
        report = benchmark(Config(), seeds=[7, 21, 42], generations=8, population=12)
        base = report['baseline']['volume_mm3']
        for run in report['runs']:
            self.assertAlmostEqual(run['volume_reduction_pct'], (base - run['best']['volume_mm3']) / base * 100)
            self.assertTrue(run['best']['feasible'])
        self.assertEqual(report['summary']['seed_count'], 3)

    def test_search_bounds_and_unknown_config_keys_fail(self):
        for fields in [dict(seed=True), dict(seed=-1), dict(generations=0), dict(population=4), dict(generations=100000)]:
            with self.subTest(fields=fields), self.assertRaises(InputError): search(Config(), **fields)
        for seeds in [[], [7, 7], list(range(9))]:
            with self.assertRaises(InputError): benchmark(Config(), seeds=seeds)
        with self.assertRaises(InputError): benchmark(Config(), seeds=list(range(8)), generations=300, population=64)
        with self.assertRaises(InputError): Config.from_dict({'invented': 1})


class ExportTests(unittest.TestCase):
    def test_contour_area_and_bounds_match_the_evaluated_symmetric_beam(self):
        cfg = Config(); heights = [22, 22, 21, 20, 19, 18, 16, 14, 12, 10, 8, 6]
        points = contour(cfg, heights)
        self.assertEqual(points[0], points[-1])
        self.assertEqual(min(x for x, y in points), 0)
        self.assertEqual(max(x for x, y in points), cfg.length_mm)
        self.assertEqual(min(y for x, y in points), -11)
        self.assertEqual(max(y for x, y in points), 11)
        area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:]))) / 2
        self.assertAlmostEqual(area * cfg.width_mm, evaluate(cfg, heights)['volume_mm3'])
        self.assertTrue(all(a != b for a, b in zip(points, points[1:])))

    def test_exports_have_closed_geometry_and_mm_units(self):
        cfg = Config(); heights = uniform_baseline(cfg)['heights_mm']
        svg = ElementTree.fromstring(svg_export(cfg, heights))
        self.assertEqual(svg.attrib['width'], '240mm')
        self.assertIn('mm', svg.attrib['height'])
        polygon = svg.find('{http://www.w3.org/2000/svg}polygon')
        self.assertIsNotNone(polygon)
        self.assertEqual(polygon.attrib['points'].split()[0], polygon.attrib['points'].split()[-1])
        dxf = dxf_export(cfg, heights)
        self.assertIn('$INSUNITS\n70\n4\n', dxf)
        self.assertIn('LWPOLYLINE\n', dxf)
        self.assertIn('70\n1\n', dxf)
        self.assertTrue(dxf.endswith('0\nEOF\n'))
        scad = scad_export(cfg, heights)
        self.assertIn('linear_extrude(height=10)', scad)
        self.assertIn('polygon(points=', scad)

    def test_infeasible_geometry_is_not_exported_as_a_usable_design(self):
        for exporter in [svg_export, dxf_export, scad_export]:
            with self.assertRaisesRegex(InputError, 'feasible'):
                exporter(Config(), [6] * 12)

    def test_nonround_dimensions_roundtrip_without_changing_evaluated_coordinates(self):
        cfg=replace(Config(),length_mm=243.123456789,width_mm=9.87654321)
        heights=[18]*cfg.sections
        svg=ElementTree.fromstring(svg_export(cfg,heights))
        points=svg.find('{http://www.w3.org/2000/svg}polygon').attrib['points']
        parsed=[tuple(map(float,pair.split(',')))for pair in points.split()]
        self.assertEqual(parsed,contour(cfg,heights))


if __name__ == '__main__': unittest.main()
