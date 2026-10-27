"""Seeded evolutionary geometry search; every score uses the beam evaluator."""

from dataclasses import asdict
import math
import random
import statistics

from . import __version__
from .mechanics import Config, InputError, evaluate, uniform_baseline


def validate_run(seed, generations, population):
    for name, value, low, high in [('seed', seed, 0, 2**32 - 1), ('generations', generations, 1, 300), ('population', population, 8, 64)]:
        if type(value) is not int or not low <= value <= high:
            raise InputError(f'{name} must be an integer between {low} and {high}')


def repair(config, values):
    if len(values) != config.sections or any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise InputError('cannot repair a malformed profile')
    grid = config.height_grid_mm
    result = [min(config.max_height_mm, max(config.min_height_mm, round(value / grid) * grid)) for value in values]
    for i in range(1, config.sections):
        result[i] = min(result[i - 1], max(result[i - 1] - config.max_neighbor_step_mm, result[i]))
    return result


def fitness(config, result):
    if result['feasible']:
        return (0, result['volume_mm3'], result['max_stress_mpa'], tuple(result['heights_mm']))
    penalty = max(0, result['max_stress_mpa'] / config.allowable_stress_mpa - 1) + max(0, result['tip_deflection_mm'] / config.max_tip_deflection_mm - 1)
    penalty += sum(name in result['violations'] for name in ['monotonic-height', 'adjacent-step'])
    return (1, penalty, result['volume_mm3'], tuple(result['heights_mm']))


def search(config, *, seed=7, generations=80, population=32):
    config.validate()
    validate_run(seed, generations, population)
    baseline = uniform_baseline(config)
    rng = random.Random(seed)
    profiles = [list(baseline['heights_mm']) for _ in range(population)]
    best = baseline
    history = []
    for generation in range(generations + 1):
        scored = [(fitness(config, result), result) for result in [evaluate(config, profile) for profile in profiles]]
        scored.sort(key=lambda pair: pair[0])
        candidate = scored[0][1]
        if fitness(config, candidate) < fitness(config, best):
            best = candidate
        history.append({'generation': generation, **best})
        if generation == generations:
            break
        elite_count = max(2, population // 8)
        profiles = [list(result['heights_mm']) for _, result in scored[:elite_count]]
        while len(profiles) < population:
            if rng.random() < .18:
                root = rng.uniform(baseline['heights_mm'][0], config.max_height_mm)
                tip = rng.uniform(config.min_height_mm, baseline['heights_mm'][0])
                child = [root + (tip - root) * i / (config.sections - 1) for i in range(config.sections)]
            else:
                parent = min(rng.sample(scored, 3), key=lambda pair: pair[0])[1]
                child = list(parent['heights_mm'])
                if rng.random() < .6:
                    other = min(rng.sample(scored, 3), key=lambda pair: pair[0])[1]
                    cut = rng.randrange(1, config.sections)
                    child[cut:] = other['heights_mm'][cut:]
                for _ in range(rng.randint(1, 4)):
                    index = rng.randrange(config.sections)
                    child[index] += rng.choice([-2, -1, 1, 2]) * config.height_grid_mm
            profiles.append(repair(config, child))
    return {'seed': seed, 'evaluations': population * (generations + 1), 'best': best, 'history': history}


def benchmark(config, *, seeds=(7, 21, 42), generations=80, population=32):
    config.validate()
    if not isinstance(seeds, (list, tuple)) or not 1 <= len(seeds) <= 8:
        raise InputError('supply between one and eight unique seeds')
    for seed in seeds:
        validate_run(seed, generations, population)
    if len(set(seeds)) != len(seeds) or len(seeds) * population * (generations + 1) > 100000:
        raise InputError('seeds must be unique and the combined candidate budget must be <=100000')
    baseline = uniform_baseline(config)
    runs = [search(config, seed=seed, generations=generations, population=population) for seed in seeds]
    for run in runs:
        run['volume_reduction_pct'] = (baseline['volume_mm3'] - run['best']['volume_mm3']) / baseline['volume_mm3'] * 100
    reductions = [run['volume_reduction_pct'] for run in runs]
    return {'schemaVersion': 1, 'version': __version__, 'model': 'piecewise Euler-Bernoulli cantilever',
            'algorithm': {'name': 'seeded evolutionary search', 'generations': generations, 'population': population,
                          'evaluation_count_scope': 'candidate profile evaluations; excludes uniform-baseline grid scans and export verification',
                          'evaluation_count_includes_repeated_profiles': True, 'neural_model_trained': False},
            'config': asdict(config), 'baseline': baseline, 'runs': runs,
            'summary': {'seed_count': len(seeds), 'total_evaluations': sum(run['evaluations'] for run in runs),
                        'min_reduction_pct': min(reductions), 'median_reduction_pct': statistics.median(reductions),
                        'max_reduction_pct': max(reductions)}}
