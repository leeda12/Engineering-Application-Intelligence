# Embedding model provenance and license

- Model: `Xenova/all-MiniLM-L6-v2`
- Upstream architecture: `sentence-transformers/all-MiniLM-L6-v2`
- Pinned repository revision: `751bff37182d3f1213fa05d7196b954e230abad9`, recorded in `data/model_manifest.json`
- Format: quantized ONNX for Transformers.js, 384-dimensional normalized mean-pooled sentence embeddings
- License: Apache License 2.0, verified from the upstream and Xenova model cards; a local copy is stored beside the model as `LICENSE`
- Purpose: semantic retrieval only; never conclusion generation

The files are downloaded during explicit setup and bundled under `frontend/public/models/all-MiniLM-L6-v2`; the ONNX Runtime WASM module is bundled under `frontend/public/wasm`. Both browser and ingestion scripts set `allowRemoteModels = false` and explicit local WASM paths; a system scan fails if runtime code references a hosted inference or model endpoint. `data/model_manifest.json` is stored with every vector collection and compatibility is checked before retrieval.
