# ADR-001 — Local deterministic engineering intelligence

**Status:** accepted locally, 2026-08-22.

## Decision

Use a Next.js strict-TypeScript client and FastAPI service. Keep engineering conclusions in versioned Python rule tables and deterministic templates. Use bundled `Xenova/all-MiniLM-L6-v2` ONNX embeddings for semantic evidence retrieval; accept client-computed query vectors at the API boundary. Store/query vectors through PostgreSQL/pgvector when configured.

## Local prerequisite finding

The initial inspection found no local PostgreSQL service or container runtime. The approved follow-on validation installed Docker Desktop with its WSL 2 backend and verified the pinned PostgreSQL 16 + pgvector 0.8.6 path, schema, metadata, seeding, indexes, nearest-neighbor behavior, repository transition, and integration tests. The no-database local demo still explicitly reports a compatibility file-vector adapter using genuine vectors and cosine distance; it is not represented as a deployed-equivalent database.

## Consequences

The MVP remains runnable and honest on this workstation in either validated PostgreSQL/pgvector mode or explicitly labeled file compatibility mode.

Node-native ONNX ingestion also found no Microsoft Visual C++ runtime DLLs on this image. The ingestion script therefore deliberately uses the Transformers.js WASM backend—the same browser-compatible runtime and pinned ONNX model used for query embeddings—rather than introducing a machine-wide runtime dependency.
