from __future__ import annotations
import json
from functools import lru_cache
from .config import ROOT

@lru_cache
def corpus()->list[dict]:
    return json.loads((ROOT/"data/corpus/sources.json").read_text(encoding="utf-8"))

@lru_cache
def corpus_by_id()->dict[str,dict]:
    return {x["source_id"]:x for x in corpus()}

@lru_cache
def rules()->dict:
    return json.loads((ROOT/"data/engineering_rules.json").read_text(encoding="utf-8"))

@lru_cache
def applications()->list[dict]:
    return json.loads((ROOT/"data/fixtures/applications.json").read_text(encoding="utf-8"))

@lru_cache
def embedding_manifest()->dict:
    return json.loads((ROOT/"data/model_manifest.json").read_text(encoding="utf-8"))

@lru_cache
def embedding_payload()->dict:
    path=ROOT/"data/generated/embeddings.json"
    if not path.exists():
        raise RuntimeError("Generated embeddings are missing; run npm run model:embed")
    payload=json.loads(path.read_text(encoding="utf-8"))
    manifest=embedding_manifest()
    fields=("model_id","revision","dimensions","pooling","normalize")
    mismatches=[field for field in fields if payload.get(field)!=manifest.get(field)]
    if mismatches:
        raise RuntimeError(f"Stored vectors are incompatible with the pinned model manifest: {', '.join(mismatches)}")
    return payload

def vectors()->dict[str,list[float]]:
    return embedding_payload()["vectors"]
