# Synthetic policy research benchmarks v1

Six concrete policy questions, two neutral variants per question, 38 input tables.
All observations, people, areas, policy rules and questionnaire responses are
fictional. No real microdata were used or redistributed.

**Start with `policy-benchmark-v1-inputs.zip`.** Each case includes its question,
CSV and SPSS SAV files, variable codebook, questionnaire, value labels, source
crosswalk, Frictionless Data Package metadata, keys and file hashes.

`policy-benchmark-v1-registry.json` lets another app discover the individual
packages inside the input ZIP. `policy-benchmark-v1-manifest.json` identifies
the exact assets with SHA-256 hashes.

`policy-benchmark-v1-evaluator.zip` contains the known generation mechanisms,
potential outcomes, curator-authored reference plans and AI review rubrics.
Keep this separate from an analysis AI during a blinded benchmark. The public
generator source also reveals this information; separation is a benchmark
protocol, not an access-control guarantee.

`verification-receipt.json` records actual authenticated MCP imports, explicit
data transformations, fresh R calculations, independent numerical references
and signed report exports on policy app 0.2.0. `integrity-receipt.json` records
schema, key, hash, regeneration and cross-format checks. These receipts concern
execution consistency and do not certify causal identification.

The cases exercise regional panel and repeated-cross-section comparisons,
covariate-adjusted and matched group comparisons, an eligibility threshold,
basic observed-variable mediation, continuous moderation, and Gaussian,
binomial and Poisson regression. The consuming AI owns the choices and all
substantive interpretation.

Data and newly authored documents: CC BY 4.0 with attribution to cnucho,
*Research App Examples: Synthetic Policy Benchmarks*, policy-benchmark-v1.
Generator and verification code: MIT. Structural reference sources retain
their own terms; no original questionnaire/codebook attachment is included.
