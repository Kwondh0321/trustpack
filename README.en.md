# TrustPack

TrustPack is a Korean-first CLI that produces one reviewable evidence bundle for repository health, dependency pinning, research reproducibility, public-service forms, and file provenance.

```bash
python -m pip install .
trustpack scan . --profile full --lang en
```

It writes machine-readable `trustpack.json` and a standalone HTML report. Korean remains the default interface; English is an optional secondary locale.

TrustPack provides review signals, not a security, legal, or scientific-validity guarantee. Licensed under Apache-2.0.
