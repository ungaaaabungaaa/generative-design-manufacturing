# Methods and measured results

## The bounded problem

Minimize beam volume under one tip load, with fixed span, width, elastic modulus, density, and explicit geometry/response limits. The study uses a symmetric stepped section about a common centroidal axis. It does not model an arbitrary bracket, topology optimization, a neural generator, or a manufacturing process.

Default inputs are documented in `docs/contract.md` and the report. The modulus and density are illustrative aluminum-like values, not a verified material certificate. The nominal stress allowance is a chosen study constraint, not a measured yield strength or a derived safety factor.

## Mechanics and units

Lengths use mm, forces N, stress/modulus MPa=N/mm², and density g/mm³. In each constant-height section, second moment I=width×height³/12. For a section from a to b along a span L, its tip-deflection contribution is:

`P × ((L−a)³ − (L−b)³) / (3 × E × I)`

The integral uses the end-load moment field and a unit-load/energy expression. Sum section contributions. Nominal maximum bending stress in each section is at its left end:

`6 × P × (L−a) / (width × height²)`

Volume is width×section-length×sum(heights). Mass is volume×density. The constant-height limit reduces to tip deflection PL³/(3EI) and root stress PLh/(2I), as covered in the [MIT mechanics reference](https://web.mit.edu/1.105/emech10_04.pdf). The implementation is original. Tests compare this limit and an independent dense midpoint quadrature for a nonuniform profile.

The model assumes linear elasticity, small deflection, a rigid clamp, a common neutral axis, and one transverse tip force. Geometry limits screen for slenderness; they do not establish validity of every neglected local effect. Nominal beam stresses omit the step/clamp concentrations that would matter in an actual part.

## Baseline and search

The baseline scans heights from the minimum to maximum on the configured grid. It selects the first feasible uniform profile. The grid immediately below is checked as infeasible in tests. This baseline shares the search's span, width, load, material inputs, and response limits.

Each seed starts from a population of that feasible baseline. Tournament selection, crossover, height mutations, and occasional tapered profiles propose candidates. Repair quantizes/clamps heights and enforces a nonincreasing profile with bounded adjacent steps. Every candidate uses the original physics evaluator. Elitism keeps feasible results; recorded best volume cannot increase.

Scores prioritize feasibility, then volume. Infeasible candidates are ranked by normalized response violations. This is a finite heuristic search, with no proof of global optimality. The baseline is part of the population, so keeping its volume is a valid outcome; positive improvement is not forced.

## Actual benchmark

Three fixed seeds (7, 21, 42), 80 generations, and population 32 were run on 27 October 2026. Candidate evaluations total32×81×3=7,776, including repeated profiles. Uniform grid scans and export verification are outside this count. The current implementation scans the uniform baseline once for the benchmark and once per seed; this overhead is not reported as candidate search work.

The baseline height is 17 mm: volume 40,800 mm³ and model mass 110.16 g. Every seed found 32,500 mm³ and 87.75 g, giving `(40,800−32,500)/40,800×100 = 20.343137%`. Equal objective values came from different profiles and slightly different response margins; the full report retains both.

The final tip-deflection margins range from approximately 0.00091 to 0.00253 mm. These are numerical model margins, not a practical manufacturing allowance. The results must not be represented as certified or robust physical designs. A tolerance study, realistic fillets/fixtures, material evidence, independent FEA, and physical tests would be needed before any structural use.

## Geometry and reproducibility

The same evaluated heights form a symmetric closed staircase contour. SVG declares physical mm dimensions, DXF declares `$INSUNITS=4` and a closed polyline, and OpenSCAD extrudes the contour to the configured width. Geometry area×width is checked against model volume. Independent ezdxf parsing/audit verifies the four final DXFs without repairs; that does not establish validation in all CAD tools or a fabrication process.

Default report/export output is deterministic and has no clock timestamps. `scripts/reproduce.py` regenerates every canonical report/export file and compares text. Figures come from that actual report using Matplotlib; fonts/rendering libraries can change figure bytes. Python versions and random-library changes may affect future runs, so use the tested versions and verify the canonical output rather than assuming cross-version identity.
