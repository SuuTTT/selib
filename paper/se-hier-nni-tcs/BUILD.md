# Build and submission files

Compile from this directory with:

```bash
SOURCE_DATE_EPOCH=1786449600 FORCE_SOURCE_DATE=1 \
  latexmk -gg -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The fixed source date makes independent builds byte-identical with the stated
TeX Live toolchain, which permits checksum verification of the reviewed PDF.

Upload the editable LaTeX sources, both BibTeX databases, `sections/`,
`tables/`, and `figures/`. `HIGHLIGHTS.txt` is a separate Elsevier highlights
file. Before upload, resolve every item in `HUMAN_METADATA_AND_DECLARATIONS.md`
and complete the scientific gate in `SUBMISSION_GAP_REPORT.md`.
