"""Exact piecewise Euler–Bernoulli tip response, using N/mm/MPa units."""

from dataclasses import dataclass, fields
import math


class InputError(ValueError):
    pass


def on_grid(value, grid):
    return abs(value / grid - round(value / grid)) <= 1e-8


@dataclass(frozen=True)
class Config:
    length_mm: float = 240
    width_mm: float = 10
    sections: int = 12
    min_height_mm: float = 6
    max_height_mm: float = 24
    height_grid_mm: float = .5
    max_neighbor_step_mm: float = 2
    tip_load_n: float = 50
    youngs_modulus_mpa: float = 69000
    allowable_stress_mpa: float = 25
    max_tip_deflection_mm: float = 1
    density_g_mm3: float = .0027

    def validate(self):
        ranges = {
            'length_mm': (120, 600), 'width_mm': (3, 50), 'sections': (4, 24),
            'min_height_mm': (1, 60), 'max_height_mm': (1, 60),
            'height_grid_mm': (.25, 2), 'max_neighbor_step_mm': (.25, 10),
            'tip_load_n': (1, 5000), 'youngs_modulus_mpa': (1000, 500000),
            'allowable_stress_mpa': (1, 500), 'max_tip_deflection_mm': (.05, 20),
            'density_g_mm3': (.0001, .02),
        }
        for name, (low, high) in ranges.items():
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise InputError(f'{name} must be finite and between {low} and {high}')
        if type(self.sections) is not int:
            raise InputError('sections must be an integer')
        if self.min_height_mm > self.max_height_mm:
            raise InputError('minimum height exceeds maximum height')
        if any(not on_grid(value, self.height_grid_mm) for value in [self.min_height_mm, self.max_height_mm, self.max_neighbor_step_mm]):
            raise InputError('height bounds and neighbour step must align with the height grid')
        if self.length_mm / self.sections < 5 or self.length_mm / self.max_height_mm < 10:
            raise InputError('require section length >=5 mm and length/max-height >=10')
        if self.max_tip_deflection_mm / self.length_mm > .05:
            raise InputError('allowed deflection must be <=5% of span for this small-deflection study')
        return self

    @classmethod
    def from_dict(cls, values):
        if not isinstance(values, dict) or set(values) - {field.name for field in fields(cls)}:
            raise InputError('configuration must be an object with known field names')
        return cls(**values).validate()


def evaluate(config, heights):
    config.validate()
    if not isinstance(heights, (list, tuple)) or len(heights) != config.sections:
        raise InputError('profile must have exactly the configured number of heights')
    for height in heights:
        if type(height) not in (int, float) or not math.isfinite(height) or not config.min_height_mm <= height <= config.max_height_mm or not on_grid(height, config.height_grid_mm):
            raise InputError('profile heights must be finite, within bounds, and on the height grid')
    length = config.length_mm
    dx = length / config.sections
    deflection = 0
    stresses = []
    for i, height in enumerate(heights):
        a, b = i * dx, (i + 1) * dx
        inertia = config.width_mm * height**3 / 12
        deflection += config.tip_load_n * ((length - a)**3 - (length - b)**3) / (3 * config.youngs_modulus_mpa * inertia)
        stresses.append(6 * config.tip_load_n * (length - a) / (config.width_mm * height**2))
    stress = max(stresses)
    volume = config.width_mm * dx * sum(heights)
    violations = []
    if any(heights[i] < heights[i + 1] - 1e-9 for i in range(config.sections - 1)):
        violations.append('monotonic-height')
    if any(abs(heights[i] - heights[i + 1]) > config.max_neighbor_step_mm + 1e-9 for i in range(config.sections - 1)):
        violations.append('adjacent-step')
    if stress > config.allowable_stress_mpa * (1 + 1e-9):
        violations.append('stress')
    if deflection > config.max_tip_deflection_mm * (1 + 1e-9):
        violations.append('deflection')
    return {'heights_mm': list(heights), 'volume_mm3': volume,
            'mass_g': volume * config.density_g_mm3, 'tip_deflection_mm': deflection,
            'max_stress_mpa': stress, 'section_stress_mpa': stresses,
            'stress_margin_mpa': config.allowable_stress_mpa - stress,
            'deflection_margin_mm': config.max_tip_deflection_mm - deflection,
            'feasible': not violations, 'violations': violations}


def uniform_baseline(config):
    config.validate()
    steps = round((config.max_height_mm - config.min_height_mm) / config.height_grid_mm)
    for step in range(steps + 1):
        height = config.min_height_mm + step * config.height_grid_mm
        result = evaluate(config, [height] * config.sections)
        if result['feasible']:
            return result
    raise InputError('No feasible uniform baseline within the configured bounds; maximum height also fails')
