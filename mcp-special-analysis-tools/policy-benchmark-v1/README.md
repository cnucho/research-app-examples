# Synthetic policy research benchmarks · policy-benchmark-v1

**SYNTHETIC: every observation, person, region, policy rule and questionnaire
response is generated. No real microdata or anonymized real records are used.**

This package starts with specific policy questions and documentation that a
researcher could receive. It is shared test material, independent of one app's
database or result format. The current execution target is the R-backed policy
MCP in [`cnucho/mcp-special-analysis-tools`](https://github.com/cnucho/mcp-special-analysis-tools),
version `0.2.0`, source commit `5db498e3195ecc214b1b7d3c890212f074901514`.

## Download and start

For classroom practice, start with the [Korean student guide](teaching/README_KO.md)
and [practice problems](teaching/PRACTICE_PROBLEMS_KO.md). The student ZIP preserves
all ordinary input bytes under `user/` and adds these two handouts. Its checksum,
contents and Dropbox public-link status are recorded in [distribution.json](teaching/distribution.json).
The original release below remains a separately versioned benchmark archive.

- [Versioned release](https://github.com/cnucho/research-app-examples/releases/tag/policy-benchmark-v1)
- [Ordinary analysis inputs ZIP](https://github.com/cnucho/research-app-examples/releases/download/policy-benchmark-v1/policy-benchmark-v1-inputs.zip)
- [Machine-readable package registry](https://github.com/cnucho/research-app-examples/releases/download/policy-benchmark-v1/policy-benchmark-v1-registry.json)
- [Korean usage guide](manual-ko.md)
- [Official structural references and exact mapping scope](sources.json)
- [Evaluator protocol](evaluation/README.md)

Read one case's `README.md` and provide its observed files, codebook and policy
question to the analysis AI. Use either CSV or SAV, not both stacked together.
The ordinary inputs archive contains no potential outcomes, DGP coefficients,
method-selection answer or reference estimate. Public generator source and
the separate evaluator ZIP do contain oracle information; keep them out of a
blinded analysis session.

## Concrete cases

Each case has neutral variants `v01` and `v02`. The sizes below are **per
variant after the intended joins**, not the sum of every input file.

| Case | Policy question | Main observations | Separate input files |
| --- | --- | ---: | --- |
| `c01_heat_shelters` | Did longer cooling-shelter opening hours change heat-illness surveillance reports? | 48 fictional municipalities × 8 years = 384 | Annual outcomes, adoption history, baseline facility inventory |
| `c02_youth_transport` | Did youth job-search transport support change monthly labor earnings? | 40 areas × 4 independent survey waves × 20 people = 3,200 | Survey records, area policy history |
| `c03_training` | How do six-month earnings differ for participants after considering baseline differences? | 900 adults | Baseline, program roster, six-month follow-up |
| `c04_home_insulation` | What changes in electricity use appear near the housing-support eligibility cutoff? | 1,200 households | Applications, awards, bills, public program rules |
| `c05_digital_service` | Does digital-service training improve later performance, and how does self-efficacy relate to that change? | 800 adults | Baseline, assignment, mediator questionnaire, later assessment |
| `c06_heat_safety` | Does the relation between safety-training hours and heat burden vary with outdoor work exposure? | 900 workers | Baseline environment, training log, common 30-day follow-up |

The entire suite contains 12 input packages and 38 underlying tables. All
canonical CSVs have UTF-8 BOM encoding. SAV copies carry variable labels,
value labels and user-missing codes. JSON uses Frictionless Data Package v1
and Table Schema, with documented extensions for units and field provenance.

## What is modeled on actual sources

The source ledger separates verified field names from semantic aliases,
conceptual adaptations, derived values and entirely fictional policy fields.
Examples include Ministry of the Interior and Safety cooling-shelter fields,
KDCA surveillance definitions, the regional employment survey structure,
verified KLIPS integrated-codebook fields, household energy survey concepts,
NIA digital-information domains and working-conditions exposure concepts.

Actual source observations, original questionnaires and attached codebooks are
not redistributed. Adapted variables do not claim to be original microdata
columns. In particular, whole-sample earnings with nonemployment coded zero
are not the same outcome as wages observed only for employed wage earners.

## Regenerate

Python 3.12 and the pinned packages in `requirements.txt` are sufficient to
create the data. R is needed only for the actual policy-app execution check.

```bash
python -m pip install -r mcp-special-analysis-tools/policy-benchmark-v1/requirements.txt
python mcp-special-analysis-tools/policy-benchmark-v1/generate.py \
  --output out/policy-benchmark-v1
python mcp-special-analysis-tools/policy-benchmark-v1/verify.py \
  out/policy-benchmark-v1 --regenerate --receipt out/integrity-receipt.json
```

The generator refuses to overwrite a nonempty output directory. Seeds are
fixed and recorded per variant. No seed is selected to achieve significance,
a desired estimated sign or interval coverage. CSV bytes reproduce under the
pinned dependencies. The SAV header timestamp is explicitly normalized to
the version date, 2026-11-16 00:00:00, so both formats can be checked byte for
byte. This header date is not an execution timestamp. Decoded values, variable
labels, value labels and user-missing definitions are checked separately.
Published byte hashes identify each exact release asset.

## Actual MCP/R verification

Check out the compatible app commit and configure its pinned R runtime. Then:

```bash
POLICY_RSCRIPT=/absolute/path/to/Rscript OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python mcp-special-analysis-tools/policy-benchmark-v1/verify_mcp.py \
  out/policy-benchmark-v1 --app /absolute/path/to/mcp-special-analysis-tools \
  --output out/policy-mcp-evidence
```

The verifier imports the distributed bytes through authenticated HTTP MCP,
executes curator-authored joins and derived variables, runs 20 explicit plans
across seven R adapters, verifies matched-sample preservation, downloads
signed report ZIPs, and compares results with separate R package calls or
independent matrix arithmetic in `evaluation/check_reference.R`.

It also exercises duplicate joins, unmatched keys, identifier precision and
explicit missing-code recoding. All scientific choices are fixed host-authored
fixtures; the code does not recommend a method, interpret an effect or grade
causal credibility. The AI review rubric is separate.

The receipt is evidence of execution on this version. The input package does
not replay its stored estimates as an answer. Population DGP targets, finite
sample potential-outcome targets and realized estimates are distinct.

`evaluation/app-source.json` binds the actual execution sources to the upstream
commit by their Git blob contents. The receipt records the local checkout
commit separately, so a restored checkout is not confused with its upstream
history. `evaluation/bind_receipt.py` also binds each current plan and preparation
to the saved execution request and exactly reproduced prepared rows. A changed
plan, source, dataset or metadata registry cannot reuse an unrelated receipt.

## Package and register

```bash
python mcp-special-analysis-tools/policy-benchmark-v1/package.py \
  out/policy-benchmark-v1 --output out/policy-benchmark-release \
  --verification out/policy-mcp-evidence/verification-receipt.json
python mcp-special-analysis-tools/policy-benchmark-v1/write_catalog.py \
  out/policy-benchmark-v1 --output registry.json
```

The release workflow checks all schemas and hashes, regenerates CSV and SAV,
compares the data with the bytes actually imported in the MCP receipt, and
publishes separate input/evaluator archives. An existing version is never
silently replaced. The root registry keeps the existing LCA package and adds
all policy cases, with purposes, structure, generator, seed, formats, licenses,
source IDs and stable distribution pointers. Other apps can use these records
but need their own catalog integration.

No generalized causal-tree adapter, fuzzy-RD estimator, RD density test,
complex survey variance estimator or full PROCESS catalog is claimed by these
fixtures. The suite covers the current seven explicit R adapter families.

Data and newly authored documentation: [CC BY 4.0](LICENSE-DATA.md). Code: the
repository's [MIT license](../../LICENSE-CODE).
