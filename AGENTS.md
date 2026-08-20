# Repository instructions

- Treat `manifest.yaml` and `runtime/` as the only editable runtime source.
- Preserve the exact bytes under `archive/`; verify with `archive/SHA256SUMS`.
- Never hand-edit `dist/*.yios`; rebuild it.
- Keep Module 09 maintenance-only and Module 10 asset-only.
- Every runtime mode must load the shared 00/08 core exactly once.
- Keep Wei and Heng persona modules isolated; Heng accepts only a frozen, context-bound `WEI_REPORT`.
- Do not mark Beta-3 as passed based on unit tests. T1–T10 require behavioral evaluation.
- Run `PYTHONPATH=src python -m unittest discover -s tests -v` and `PYTHONPATH=src python -m yi_runtime validate .` before committing.
