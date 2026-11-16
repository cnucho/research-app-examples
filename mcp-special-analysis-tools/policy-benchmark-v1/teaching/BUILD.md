# Build the standalone student handout

Students use the distributed PDF and data directly. These commands are for
maintainers rebuilding the handout, not prerequisites for completing a policy
analysis assignment.

## Inputs

- The exact `user/` directory from the original `policy-benchmark-v1` input release.
- The four Korean manuscripts in this directory.
- Noto Sans CJK regular and bold fonts, with Korean collection index 1 for the
  documented TTC files. Font files are build inputs; the resulting PDF embeds
  the required glyphs so readers do not need to install them.
- Python with `requirements-teaching.txt`. Archive packaging itself uses only
  Python's standard library.

## Render and inspect

From the repository root:

```bash
python -m pip install -r mcp-special-analysis-tools/policy-benchmark-v1/teaching/requirements-teaching.txt
python mcp-special-analysis-tools/policy-benchmark-v1/teaching/build_handbook.py \
  --output out/student/policy-effect-exercises-ko.pdf
```

The renderer defaults to the Noto CJK paths printed in its `--help`. Supply
`--font-regular`, `--font-bold` and `--font-index` for a different installation.
It writes a PDF and a `.qa.json` receipt with manuscript hashes and text checks.
Render every PDF page and inspect typography, table wrapping, headings and
page transitions before packaging. Text checks do not replace visual review.
Font caches and rendered inspection images stay outside the repository.

## Package

```bash
python mcp-special-analysis-tools/policy-benchmark-v1/teaching/package_student.py \
  out/policy-benchmark-v1/user \
  --handbook out/student/policy-effect-exercises-ko.pdf \
  --output out/student/policy-analysis-student-v1-r2.zip
```

The packager first verifies all original input files against the original
manifest and CSV/SAV descriptors. It then adapts the input index and twelve
case README files for tool-independent teaching, updates their registry hashes
and the current manifest, and preserves the original manifest and registry in
`provenance/`. Observation data, codebooks, questionnaires, value labels,
source descriptions and data descriptors are unchanged. It includes no curator
plans, DGP answers or numerical reference output.

The archive refuses to overwrite an existing output. Given the same validated
PDF, manuscripts and original inputs, its member bytes, ordering and timestamps
are fixed. Update `distribution.json` with the actual archive size, SHA-256 and
file count; do not reuse an earlier revision's checksum. Keep the original
benchmark release assets unchanged. Activate a Dropbox URL only after checking
the intended distribution account, public read/download access and exact bytes.

The script performs file checks and formatting. It does not choose a research
method, interpret results, grade a student, or certify causal validity.
