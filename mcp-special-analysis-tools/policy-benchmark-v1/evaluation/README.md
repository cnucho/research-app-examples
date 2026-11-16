# Evaluator material: keep separate from analysis input

The ordinary ZIP is `policy-benchmark-v1-inputs.zip`. It contains questions,
observed records and normal documentation. This evaluator package contains
deliberately authored generation mechanisms, potential outcomes, reference
plans and review rubrics. Do not give the evaluator package or generator
source to an analysis agent during a blinded benchmark.

This is protocol separation, not access control. The shared repository is
public and the generator makes its assumptions inspectable.

## Three distinct quantities

1. **Population DGP target**: the parameter/estimand explicitly written into
   the generator, conditional on the stated hypothetical intervention.
2. **Finite-sample target**: a potential-outcome contrast for the relevant
   generated sample. With matching, recompute it among the *actual retained
   treated rows*. It need not equal the full treated-sample target.
3. **Realized reference estimate**: the fresh numerical output of the stated
   R package, sample and options. This is the target for implementation
   parity; it is not automatically equal to either of the first two.

No test requires a random sample estimate to equal the DGP coefficient,
every null-effect dataset to produce p > .05, or every interval to cover
the true value. No result is a real policy finding.

## Evaluation responsibilities

`verify.py` checks bytes, schemas, data types, keys, metadata and CSV/SAV
parity. `verify_mcp.py` sends the distributed files through the actual
authenticated MCP HTTP service, executes explicitly authored preparation
steps and R plans, checks numerical consistency and signed report exports.
Its receipt records what actually ran. It does not grade scientific quality.

The host AI or human reviewer uses each case's `rubric.json` to assess
research reasoning: whether it distinguishes panel from repeated cross
sections, explains the comparison and target population, identifies limits
of overlap or local inference, avoids post-treatment controls without a
reason, and describes assumptions behind mediation/moderation.

An unobserved confounder is not guaranteed to be detectable from the
observed file. The rubric must accept appropriately qualified answers;
it must not require clairvoyance about the hidden generator.

Reference plans are curator-authored test inputs. They are never runtime
rules that choose the method for a user. Different defensible plans are
possible. Prewritten narrative text in a test identifies the fixture and
execution scope only; it does not interpret effects.

## Additional integrity probes

The MCP verifier also creates deliberately small duplicates, unmatched keys,
missing-code examples and identifier-precision probes in its isolated test
study. These test explicit data contracts rather than changing every
substantive dataset. The receipt lists the errors or exact retained values.

The current app does not expose fuzzy RD, an RD manipulation-density test,
complex survey-design variance, generalized causal trees, or the full Hayes
PROCESS model catalog through these seven R adapters. No fixture claims
those capabilities were run.
