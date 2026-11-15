# LCA–MCA synthetic mobility survey · tutorial-v1

**All 1,800 records are generated. No real respondent or fitted result is included.** The 21 columns contain eight attitude items for LCA, five categorical choice items for MCA, and eight contextual fields. The generator uses a hidden, imperfectly separated response propensity to create plausible associations. This is teaching material, not a validated population estimate or proof that any class number is correct in real research.

Download the [versioned release](https://github.com/cnucho/research-app-examples/releases/tag/lca-mca-tutorial-v1). It contains `mobility_survey.csv`, `mobility_survey.sav`, `codebook.json`, `item_map.csv`, and `manifest.json`. The CSV and SAV encode the same values; SAV includes SPSS labels and the income refusal code. Their *decoded values* are checked for parity. The SAV writer adds file metadata, so regenerating it may change its bytes even when values agree. Use the published manifest hash to identify the exact released file.

- [Korean questionnaire and scenario](questionnaire-ko.md)
- [Korean follow-along manual](manual-ko.md)
- [Generator](generate.py), [live calculation verifier](verify.py), and [MCP dispatcher verifier](verify_mcp.py)
- [Introduction and tutorial videos](https://github.com/cnucho/research-app-examples/releases/tag/lca-mca-tutorial-v1) — video links appear here after publication.

To regenerate in an empty directory with the LCA–MCA platform Python environment:

```powershell
python lca-mca-platform/tutorial-v1/generate.py --output out/lca-mca-tutorial-v1
```

The verifier imports both formats and runs new LCA/MCA fits. It does not replay stored results.

```powershell
$env:PYTHONPATH = "D:\Git\lca-mca-platform\src"
python lca-mca-platform/tutorial-v1/verify.py out/lca-mca-tutorial-v1
python lca-mca-platform/tutorial-v1/verify_mcp.py out/lca-mca-tutorial-v1
```

The tutorial omits `survey_weight` from the basic fit: this app's weighted LCA uses a pseudo-likelihood and leaves AIC/BIC blank. The example's `income_group=99` is a declared refusal code, while the attitude and choice items are complete. No causal, prediction, survey-design variance, or ordinal-LCA claim follows from this example.
