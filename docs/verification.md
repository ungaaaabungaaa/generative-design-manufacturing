# Verification record

Date: 27 October 2026. Local system: macOS arm64, Python 3.14.7, Node.js 24.18.0. Temporary plotting/verification tools were isolated from global packages.

## Mechanics, search, and exports

- `python3 -m unittest discover -s tests -v`: 23 tests pass. Checks cover the uniform closed form, independent 12,000-point nonuniform quadrature, load/modulus scaling, units, response/geometry violations, smallest feasible grid baseline, invalid/extreme values, seeded determinism, retained feasibility, resource limits, reduction denominators, symmetric contour area/bounds, export units/closure and nonround coordinate precision, invalid export refusal, CLI output protection, valid partial configurations, malformed/deep JSON, symlinks, and local server restrictions.
- `node --test tests/viewer.test.mjs`: 4 tests pass. The real report/history schema, reduction denominator, symmetric displayed area, and corrupt-data rejection are checked.
- `node --check web/app.mjs`, `python3 scripts/build.py`, and `git diff --check`: pass. The build copies 17 public viewer/report/export files.
- `python3 scripts/reproduce.py`: all 13 canonical report/export files reproduce byte-for-byte. The actual CLI also generated its complete new-directory bundle successfully.

Python coverage was measured with coverage 7.17.0: 95% combined line/branch coverage over automated tests, including 100% for mechanics. CI separately runs Python 3.11/3.14, Node.js 22 checks, and canonical reproduction; local checks do not establish a remote CI pass.

The real default benchmark contains three seeds, 80 generations, population 32, and 7,776 candidate evaluations. Its uniform baseline is 40,800 mm³ / 110.16 g; all final runs are 32,500 mm³ / 87.75 g, with different profiles. Candidate counts exclude baseline grid scans and export verification. Results are numerical model outputs, not measured hardware performance.

## Independent format and figure checks

All four canonical DXFs were read with **ezdxf 1.4.5**. Each declared millimetres, contained one closed LWPOLYLINE, and produced the evaluator's volume from parsed area×width. Every audit returned zero errors and zero repairs. This is an independent format check, not validation in every CAD/manufacturing tool.

To repeat optional checks in a temporary environment:

```sh
python3 -m pip install -r requirements-verification.txt
python3 scripts/validate_exports.py
python3 -m coverage run --branch --source=design_lab -m unittest discover -s tests
python3 -m coverage report -m
```

The Matplotlib 3.11.2 comparison figure was generated from the actual report and visually inspected. The optional `scripts/figure.py` regenerates it. The user-approved line-art concept cover was later added with its portable provenance record; its PNG decoded correctly at 1672×941, and SHA-256 matched the approved asset manifest. Concept art remains separate from the measured figure.

## Actual browser evidence

Root inspected the running desktop explorer on loopback port 8790. Generation 0 displayed the uniform baseline: 110.16 g, 0% reduction, 0.816 mm deflection, 24.91 MPa nominal stress. Seed 21 at generation 80 displayed 87.75 g, 20.34%, 0.997 mm, and 21.04 MPa. Seed/generation controls updated geometry, history, and margins; final download URLs selected the correct seed. No desktop overlap was observed.

The child browser surface was unavailable, so no child screenshot or narrow-screen browser validation is claimed here. Responsive CSS is implemented; additional device checks remain distinct evidence.

## Unverified physical scope

No public deployment, OpenSCAD engine execution, FEA, material test, machining validation, or physical load test was performed. Step/clamp concentrations and other stated model omissions remain. Exports are study artifacts, not certified or fabrication-ready designs.
