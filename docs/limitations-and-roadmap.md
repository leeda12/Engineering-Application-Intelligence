# Known limitations and future roadmap

- Controlled-form PDFs only; scanned, handwritten, and arbitrary documents are unsupported.
- Material properties are fictional, discrete table values without interpolation.
- Pressure drop is a boundary lookup, not CFD or a validated hydraulic network model.
- Semantic retrieval is compact-model relevance, not reasoning.
- The validated workstation path uses Docker Desktop with the WSL 2 backend, PostgreSQL 16, and pgvector 0.8.6. Compatibility mode remains intentionally available only when PostgreSQL is not configured.
- SVG is a concept diagram without fabrication dimensions, tolerances, GD&T, or CAD semantics.

Future work: add authenticated roles, immutable database audit events, malware scanning, DXF export, richer controlled forms, uncertainty propagation, and deploy only after explicit approval. The possible deployment split is Next.js on Vercel, reviewed FastAPI functions, Neon PostgreSQL/pgvector, and bundled browser inference; nothing has been deployed or connected.
