# Research app examples

This public catalog holds **entirely synthetic** datasets and reproducible learning material for research applications. Each app owns a versioned folder, generator, questionnaire, codebook, manual, and verification script. Large data and video files are attached to GitHub Releases rather than embedded in app runtime images or Git history.

## Available packages

| App | Example | Release | Formats | Guide |
| --- | --- | --- | --- | --- |
| [LCA–MCA platform](https://github.com/cnucho/lca-mca-platform) | Synthetic mobility survey, 1,800 rows × 21 columns | [tutorial-v1](https://github.com/cnucho/research-app-examples/releases/tag/lca-mca-tutorial-v1) | CSV, SPSS SAV, JSON codebook, item map | [Korean follow-along manual](lca-mca-platform/tutorial-v1/manual-ko.md) |
| [Policy analysis MCP](https://github.com/cnucho/mcp-special-analysis-tools) | Six concrete policy questions, 12 synthetic packages, 38 input tables | [policy-benchmark-v1](https://github.com/cnucho/research-app-examples/releases/tag/policy-benchmark-v1) | CSV, SPSS SAV, Frictionless JSON, codebook, questionnaire, source crosswalk | [Korean usage guide](mcp-special-analysis-tools/policy-benchmark-v1/manual-ko.md) |

## Student policy-research practice

The [Korean student guide](mcp-special-analysis-tools/policy-benchmark-v1/teaching/README_KO.md)
and [six concrete practice problems](mcp-special-analysis-tools/policy-benchmark-v1/teaching/PRACTICE_PROBLEMS_KO.md)
support question-first analysis without prescribing a statistical method. The student
archive adds these handouts to the exact ordinary-input release: 12 data packages,
38 observed CSV tables and 38 corresponding SPSS SAV files. It contains no curator
answers or reference plans. The [distribution record](mcp-special-analysis-tools/policy-benchmark-v1/teaching/distribution.json)
identifies the archive checksum and Dropbox public-link status. A pending link is
not an active public download.

## Machine-readable discovery

[`registry.json`](registry.json) records the existing LCA package and all 12 policy
packages. Entries state the generation purpose, observation unit, time structure,
file shape, canonical CSV hashes, metadata entry point, seed, generator,
compatibility, structural references and license. A release manifest identifies
the exact downloadable ZIPs. Other apps may consume this catalog; automatic
integration must be implemented by the consuming app.

Policy analysis inputs and evaluator-only material are distributed separately.
The ordinary input archive contains no hidden potential outcomes, DGP coefficients
or reference plans. Evaluator receipts record actual calculations and mechanical
checks. They are not cached answers for the application or certificates of causal
validity. Public generator source is available for inspection, so blinded
evaluation requires giving an analysis agent only the ordinary input archive.

The app must calculate results from the downloaded bytes. A cached dashboard, model, or report is not shipped as the tutorial answer. Every release has a manifest of file hashes and a generator. Synthetic records are not anonymized real respondents.

## Adding another app

Use a separate `<app-slug>/<tutorial-version>/` folder and a matching GitHub Release. Follow the [synthetic example and tutorial standard](https://github.com/cnucho/app-design-principle/blob/main/docs/29_SYNTHETIC_EXAMPLE_AND_REPRODUCIBLE_TUTORIAL.md). Match the actual app importer, include a codebook and an exact manual, run the real product path, and publish introduction and tutorial videos only after their screen states are verified.

Data and questionnaire text in this catalog are offered under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); generator and verification code are offered under the [MIT License](LICENSE-CODE).
