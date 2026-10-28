from dataclasses import replace
import math
import unittest

from design_lab.mechanics import Config, InputError, evaluate, evaluate_loads, uniform_baseline


class MechanicsTests(unittest.TestCase):
    def test_constant_section_matches_closed_form_and_units(self):
        cfg = Config()
        height = 18
        result = evaluate(cfg, [height] * cfg.sections)
        inertia = cfg.width_mm * height**3 / 12
        self.assertAlmostEqual(result['tip_deflection_mm'], cfg.tip_load_n * cfg.length_mm**3 / (3 * cfg.youngs_modulus_mpa * inertia))
        self.assertAlmostEqual(result['max_stress_mpa'], 6 * cfg.tip_load_n * cfg.length_mm / (cfg.width_mm * height**2))
        self.assertEqual(result['volume_mm3'], cfg.width_mm * cfg.length_mm * height)
        self.assertAlmostEqual(result['mass_g'], result['volume_mm3'] * cfg.density_g_mm3)
        self.assertTrue(result['feasible'])

    def test_load_and_modulus_scaling(self):
        cfg = Config(); heights = [18] * cfg.sections
        base = evaluate(cfg, heights)
        double = evaluate(replace(cfg, tip_load_n=cfg.tip_load_n * 2), heights)
        stiff = evaluate(replace(cfg, youngs_modulus_mpa=cfg.youngs_modulus_mpa * 2), heights)
        self.assertAlmostEqual(double['tip_deflection_mm'], base['tip_deflection_mm'] * 2)
        self.assertAlmostEqual(double['max_stress_mpa'], base['max_stress_mpa'] * 2)
        self.assertAlmostEqual(stiff['tip_deflection_mm'], base['tip_deflection_mm'] / 2)
        self.assertEqual(stiff['max_stress_mpa'], base['max_stress_mpa'])

    def test_nonuniform_integral_matches_independent_midpoint_quadrature(self):
        cfg = Config(); heights = [22, 22, 21, 20, 19, 18, 16, 14, 12, 10, 8, 6]
        result = evaluate(cfg, heights)
        total = 0
        dx = cfg.length_mm / 12000
        for j in range(12000):
            x = (j + .5) * dx
            h = heights[min(int(x / (cfg.length_mm / cfg.sections)), cfg.sections - 1)]
            total += cfg.tip_load_n * (cfg.length_mm - x)**2 / (cfg.youngs_modulus_mpa * cfg.width_mm * h**3 / 12) * dx
        self.assertAlmostEqual(result['tip_deflection_mm'], total, places=7)

    def test_constraints_report_physics_and_geometry_failures(self):
        cfg = Config()
        small = evaluate(cfg, [6] * cfg.sections)
        self.assertFalse(small['feasible'])
        self.assertIn('deflection', small['violations'])
        self.assertIn('stress', small['violations'])
        zigzag = evaluate(cfg, [18, 20] + [18] * 10)
        self.assertIn('monotonic-height', zigzag['violations'])
        step = evaluate(cfg, [24] + [18] * 11)
        self.assertIn('adjacent-step', step['violations'])

    def test_smallest_uniform_baseline_is_feasible_and_previous_grid_is_not(self):
        cfg = Config(); base = uniform_baseline(cfg)
        self.assertTrue(base['feasible'])
        previous = [base['heights_mm'][0] - cfg.height_grid_mm] * cfg.sections
        self.assertFalse(evaluate(cfg, previous)['feasible'])

    def test_invalid_configs_and_extreme_inputs_are_rejected(self):
        cases = [dict(length_mm=0), dict(length_mm=float('nan')), dict(width_mm=True),
            dict(sections=12.5), dict(sections=1000000), dict(min_height_mm=30), dict(max_height_mm=25),
            dict(height_grid_mm=.3), dict(tip_load_n=float('inf')), dict(youngs_modulus_mpa=-1),
            dict(max_tip_deflection_mm=20), dict(density_g_mm3=0), dict(max_neighbor_step_mm=.75)]
        for fields in cases:
            with self.subTest(fields=fields), self.assertRaises(InputError):
                replace(Config(), **fields).validate()
        for heights in [[18]*11, [0]*12, [float('nan')]*12, [1e200]*12, [18.1]*12, [True]*12]:
            with self.subTest(heights=heights), self.assertRaises(InputError):
                evaluate(Config(), heights)

    def test_load_sweep_rechecks_fixed_geometry_and_records_failed_loads(self):
        cfg = Config()
        heights = [18] * cfg.sections
        result = evaluate_loads(cfg, heights, [25, 50, 500])
        self.assertEqual([row['tip_load_n'] for row in result], [25, 50, 500])
        self.assertTrue(result[1]['feasible'])
        self.assertFalse(result[2]['feasible'])
        self.assertIn('stress', result[2]['violations'])
        self.assertEqual(result[0]['heights_mm'], heights)
        self.assertAlmostEqual(result[0]['max_stress_mpa'] * 2, result[1]['max_stress_mpa'])
        self.assertAlmostEqual(result[0]['tip_deflection_mm'] * 2, result[1]['tip_deflection_mm'])
        self.assertEqual(cfg.tip_load_n, 50)

    def test_load_sweep_rejects_unbounded_duplicate_or_invalid_loads(self):
        for loads in [[], [50] * 17, [50, 50], [True], [float('nan')], [0], [5001]]:
            with self.subTest(loads=loads), self.assertRaises(InputError):
                evaluate_loads(Config(), [18] * 12, loads)

    def test_infeasible_problem_does_not_return_a_fake_baseline(self):
        with self.assertRaisesRegex(InputError, 'No feasible uniform'):
            uniform_baseline(replace(Config(), tip_load_n=5000))


if __name__ == '__main__': unittest.main()
