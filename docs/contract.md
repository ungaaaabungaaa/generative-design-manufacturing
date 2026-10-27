# Design study contract, version 1

The study uses a symmetric rectangular cantilever with fixed width, constant Young's modulus, and one transverse tip load. Section heights change symmetrically about a common centroidal axis. All lengths are millimetres, load is newtons, modulus/stress are MPa (N/mm²), density is g/mm³, volume is mm³, and mass is grams.

Configuration defaults: L=240, b=10, 12 equal sections, height range6–24, height grid0.5, adjacent-height change≤2, load50, E=69000, nominal stress limit25, tip-deflection limit1, density0.0027. Heights must be nonincreasing from clamp to tip and aligned to the grid. Section length must be≥5mm, L/max-height≥10, and allowed deflection/L≤0.05. Grid/bounds must align and the step limit must be a grid multiple.

Supported bounds: length120–600, width3–50, sections4–24, heights1–60, grid0.25–2, neighbour step0.25–10, load1–5000, E1000–500000, stress limit1–500, deflection limit0.05–20, density0.0001–0.02. Booleans, unknown fields, nonfinite values, and invalid combinations fail before evaluation. Profiles have exactly N finite heights within the configured bounds and grid. Nonmonotone or excessive-step profiles receive geometric constraint violations; invalid positive dimensions are input errors.

For section i spanning [a,b], I_i=width×height_i³/12. Its tip-deflection contribution is P×[(L−a)³−(L−b)³]/(3×E×I_i). Nominal maximum bending stress in the section is6×P×(L−a)/(width×height_i²). Sum contributions for tip deflection and use the largest stress. Volume=width×section-length×sum(heights); mass=density×volume. Constraints use a numerical tolerance of1e−9 relative to their limits.

This is a linear elastic, small-deflection Euler–Bernoulli study. It excludes shear deformation, stress concentrations at steps/clamp, local load effects, fatigue, buckling, residual stresses, tolerances, joints, and process validation. It is not FEA, a trained neural model, a globally optimal solution, or fabrication certification.

The uniform baseline scans the same height grid for the smallest feasible constant section. Search uses a seeded population, mutation/crossover, geometry repair, and elitism. The feasible baseline is retained. Final comparisons evaluate the original physics model and divide volume reduction by baseline volume. No surrogate prediction substitutes for final evaluation.

`python3 -m design_lab generate --out NEW_DIR [--config JSON] [--seeds 7 21 42] [--generations 80] [--population 32]` creates deterministic JSON plus baseline/final SVG, DXF, and OpenSCAD files. The directory must not exist. Config is a regular UTF-8 JSON file≤16KiB. Generations1–300, population8–64, seeds1–8 unique integers0–2³²−1; combined candidate budget≤100000. Errors exit2 for inputs,1 for I/O; success0. Outputs contain no runtime timestamps.

The report contains schemaVersion1, model/config/algorithm, baseline, seed runs with best-feasible histories, final geometry/metrics, evaluation counts, and summary reduction statistics. Histories start with generation0baseline. Exported closed profiles match the evaluated symmetric staircase. DXF declares millimetres; OpenSCAD extrudes that profile to the configured width. OpenSCAD execution and physical builds remain separate validation.

Evaluation counts are candidate-profile evaluations only: population×(generations+1) per seed, including repeated profiles. They exclude the uniform-baseline grid scans and extra export verification calls. The combined100000budget applies to those candidate evaluations, not every helper call.

The static browser only reads this report and generated geometry. It selects runs and recorded generations, showing exact constraints and baseline comparisons. No API, tracking, or user upload is required. The local loopback server serves only explicit public files; production builds copy that allowlist.
