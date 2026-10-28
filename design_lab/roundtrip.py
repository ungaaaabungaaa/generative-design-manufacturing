"""Parse an exported SVG independently, then check its evaluator profile and area."""

import math
from xml.etree import ElementTree

from .geometry import contour
from .mechanics import InputError, evaluate


NS = '{http://www.w3.org/2000/svg}'


def validate_svg(config, heights, text):
    design = evaluate(config, heights)
    if not design['feasible']:
        raise InputError('round-trip validation requires a model-feasible design')
    if not isinstance(text, str) or len(text.encode('utf-8')) > 65536 or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise InputError('SVG must be bounded plain XML without declarations or entities')
    try:
        root = ElementTree.fromstring(text)
        nodes = list(root.iter())
        if root.tag != NS + 'svg' or len(nodes) > 8 or any(node.tag not in {NS + 'svg', NS + 'title', NS + 'polygon'} or 'transform' in node.attrib for node in nodes):
            raise InputError('only a plain SVG profile without transforms is supported')
        allowed = {NS + 'svg': {'width', 'height', 'viewBox'}, NS + 'title': set(),
                   NS + 'polygon': {'points', 'fill', 'stroke', 'stroke-width'}}
        if any(set(node.attrib) - allowed[node.tag] for node in nodes) or any(list(node) for node in root):
            raise InputError('only direct plain title and polygon elements with known attributes are supported')
        polygons = list(root.iter(NS + 'polygon'))
        if len(polygons) != 1:
            raise InputError('SVG must contain exactly one polygon')
        dimensions = []
        for name in ('width', 'height'):
            value = root.attrib[name]
            if not value.endswith('mm'):
                raise InputError('SVG dimensions must use millimetres')
            dimensions.append(float(value[:-2]))
        view = [float(value) for value in root.attrib['viewBox'].split()]
        points = [tuple(float(value) for value in pair.split(',')) for pair in polygons[0].attrib['points'].split()]
    except (ElementTree.ParseError, KeyError, ValueError, OverflowError) as error:
        raise InputError('SVG profile XML or numeric fields are invalid') from error
    if (not 4 <= len(points) <= 100 or any(len(point) != 2 for point in points)
            or not all(math.isfinite(value) for point in points for value in point)
            or not all(math.isfinite(value) for value in dimensions + view)):
        raise InputError('SVG profile dimensions and bounded coordinates must be finite')
    expected = contour(config, heights)
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-8)
    if len(view) != 4 or not all(close(a, b) for a, b in zip(dimensions + view, [config.length_mm, max(heights), 0, -max(heights) / 2, config.length_mm, max(heights)], strict=True)):
        raise InputError('SVG dimensions/viewBox differ from the evaluated profile')
    if points[0] != points[-1] or len(points) != len(expected) or any(not close(a, b) for actual, target in zip(points, expected) for a, b in zip(actual, target)):
        raise InputError('SVG coordinates or closure differ from the evaluated profile')
    area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:]))) / 2
    volume = area * config.width_mm
    if not close(volume, design['volume_mm3']):
        raise InputError('Parsed SVG volume differs from the evaluator')
    return {'closed': True, 'length_mm': dimensions[0], 'height_mm': dimensions[1],
            'point_count': len(points), 'area_mm2': area, 'volume_mm3': volume}
