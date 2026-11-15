# Research app examples

This public catalog holds **entirely synthetic** datasets and reproducible learning material for research applications. Each app owns a versioned folder, generator, questionnaire, codebook, manual, and verification script. Large data and video files are attached to GitHub Releases rather than embedded in app runtime images or Git history.

## Available package

| App | Example | Release | Formats | Guide |
| --- | --- | --- | --- | --- |
| [LCA–MCA platform](https://github.com/cnucho/lca-mca-platform) | Synthetic mobility survey, 1,800 rows × 21 columns | [tutorial-v1](https://github.com/cnucho/research-app-examples/releases/tag/lca-mca-tutorial-v1) | CSV, SPSS SAV, JSON codebook, item map | [Korean follow-along manual](lca-mca-platform/tutorial-v1/manual-ko.md) |

The app must calculate results from the downloaded bytes. A cached dashboard, model, or report is not shipped as the tutorial answer. Every release has a manifest of file hashes and a generator. Synthetic records are not anonymized real respondents.

## Adding another app

Use a separate `<app-slug>/<tutorial-version>/` folder and a matching GitHub Release. Follow the [synthetic example and tutorial standard](https://github.com/cnucho/app-design-principle/blob/main/docs/29_SYNTHETIC_EXAMPLE_AND_REPRODUCIBLE_TUTORIAL.md). Match the actual app importer, include a codebook and an exact manual, run the real product path, and publish introduction and tutorial videos only after their screen states are verified.

Data and questionnaire text in this catalog are offered under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); generator and verification code are offered under the [MIT License](LICENSE-CODE).
