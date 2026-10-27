"""Closed symmetric staircase contours and explicit millimetre exports."""

import json

from .mechanics import InputError, evaluate


def contour(config, heights):
    result = evaluate(config, heights)
    if any(name in result['violations'] for name in ['monotonic-height', 'adjacent-step']):
        raise InputError('profile violates geometry constraints')
    dx = config.length_mm / config.sections
    points = [(0, -heights[0] / 2)]
    for i, height in enumerate(heights):
        points.append(((i + 1) * dx, -height / 2))
        if i + 1 < config.sections:
            points.append(((i + 1) * dx, -heights[i + 1] / 2))
    points.append((config.length_mm, heights[-1] / 2))
    for i in reversed(range(config.sections)):
        points.append((i * dx, heights[i] / 2))
        if i > 0:
            points.append((i * dx, heights[i - 1] / 2))
    points.append(points[0])
    return [point for i, point in enumerate(points) if i == 0 or point != points[i - 1]]


def checked_contour(config, heights):
    if not evaluate(config, heights)['feasible']:
        raise InputError('exports require a model-feasible design; this is still not fabrication certification')
    return contour(config, heights)


def number(value):
    return format(value, '.17g')


def svg_export(config, heights):
    points = checked_contour(config, heights)
    height = max(heights)
    coordinates = ' '.join(f'{number(x)},{number(y)}' for x, y in points)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{number(config.length_mm)}mm" height="{number(height)}mm" viewBox="0 {number(-height / 2)} {number(config.length_mm)} {number(height)}">
<title>Evaluated beam study profile in millimetres; physical validation pending</title>
<polygon points="{coordinates}" fill="#b7c3b7" stroke="#223831" stroke-width="0.15"/>
</svg>
'''


def dxf_export(config, heights):
    points = checked_contour(config, heights)[:-1]
    lines = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1015', '9', '$INSUNITS', '70', '4', '0', 'ENDSEC',
             '0', 'SECTION', '2', 'ENTITIES', '0', 'LWPOLYLINE', '100', 'AcDbEntity', '8', 'STUDY_PROFILE',
             '100', 'AcDbPolyline', '90', str(len(points)), '70', '1']
    for x, y in points:
        lines.extend(['10', number(x), '20', number(y)])
    return '\n'.join(lines + ['0', 'ENDSEC', '0', 'EOF']) + '\n'


def scad_export(config, heights):
    points = checked_contour(config, heights)[:-1]
    return '// Units: mm. Beam-model study only; physical/manufacturing validation pending.\n' + f'linear_extrude(height={number(config.width_mm)})\npolygon(points={json.dumps(points, separators=(",", ":"))});\n'
