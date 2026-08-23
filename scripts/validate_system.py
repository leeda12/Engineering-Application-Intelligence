from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sources=json.loads((ROOT/"data/corpus/sources.json").read_text(encoding="utf-8")); by_id={x["source_id"]:x for x in sources}
assert len(sources)==41, f"Expected 41 corpus records, found {len(sources)}"
assert len([x for x in sources if x["document_type"]=="historical_project"])==24
assert len({x["product_architecture"] for x in sources if x["document_type"]=="historical_project"})==3
for source in sources:
    for field in ("source_id","title","document_type","revision","effective_date","locator","status","product_architecture","text","applicable_constraints","provenance"): assert field in source,f"{source['source_id']} missing {field}"
for source in sources:
    if source.get("validation_outcome") in ("failed","missing_evidence"): assert source["source_id"] not in {"PRJ-024"}
superseded={x["source_id"] for x in sources if x["status"]=="superseded"}; assert "MAN-THERM-001" in superseded
rules=json.loads((ROOT/"data/engineering_rules.json").read_text(encoding="utf-8")); assert all(x in by_id for x in rules["source_ids"])
manifest=json.loads((ROOT/"data/model_manifest.json").read_text(encoding="utf-8")); assert manifest["license"]=="Apache-2.0" and manifest["dimensions"]==384
emb=ROOT/"data/generated/embeddings.json"
if emb.exists():
    payload=json.loads(emb.read_text(encoding="utf-8")); assert all(payload[field]==manifest[field] for field in ("model_id","revision","dimensions","pooling","normalize")); assert set(payload["vectors"])==set(by_id); assert all(len(v)==384 for v in payload["vectors"].values()); assert set(payload["application_queries"])=={f"APP-{index:03d}" for index in range(1,6)}; assert all(len(v)==384 for v in payload["application_queries"].values())
compose=(ROOT/"compose.yaml").read_text(encoding="utf-8")
assert "pgvector/pgvector:0.8.6-pg16-bookworm" in compose
assert '127.0.0.1:${POSTGRES_PORT:-5432}:5432' in compose
assert "pg_isready" in compose and "pgvector_data" in compose
runtime=[ROOT/"frontend/lib",ROOT/"frontend/components",ROOT/"frontend/app",ROOT/"backend/app"]
prohibited_hosts=("api.openai.com","api.anthropic.com","generativelanguage.googleapis.com","api.cohere.com","api-inference.huggingface.co","huggingface.co/")
for folder in runtime:
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix in {".py",".ts",".tsx",".js",".mjs"}:
            text=path.read_text(encoding="utf-8"); assert not any(host in text for host in prohibited_hosts),f"Runtime external model host in {path}"
            assert not re.search(r"\b(?:sk-[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,})\b",text),f"Secret-like token in {path}"
fictional=json.dumps(sources).lower(); assert "omni powertrain" not in fictional
print("System validation passed: corpus, citations, lifecycle, provenance, secrets, and runtime network boundaries")
