from __future__ import annotations
import json,os
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector

ROOT=Path(__file__).resolve().parents[1]
url=os.environ.get("DATABASE_URL")
if not url: raise SystemExit("DATABASE_URL is required")
sources=json.loads((ROOT/"data/corpus/sources.json").read_text(encoding="utf-8"))
payload=json.loads((ROOT/"data/generated/embeddings.json").read_text(encoding="utf-8"))
manifest=json.loads((ROOT/"data/model_manifest.json").read_text(encoding="utf-8"))
metadata_fields=("model_id","revision","dimensions","pooling","normalize")
mismatches=[field for field in metadata_fields if payload.get(field)!=manifest.get(field)]
if mismatches:
    raise SystemExit(f"Embedding payload does not match the pinned model manifest: {', '.join(mismatches)}")
vectors=payload["vectors"]
if set(vectors)!={source["source_id"] for source in sources}:
    raise SystemExit("Embedding payload source IDs do not exactly match the corpus")
with psycopg.connect(url) as conn:
    conn.execute((ROOT/"backend/sql/schema.sql").read_text(encoding="utf-8")); register_vector(conn)
    conn.execute("""INSERT INTO embedding_metadata(profile_key,model_id,model_revision,dimensions,pooling,normalized,corpus_vector_count,generated_at,seeded_at)
        VALUES('corpus',%s,%s,%s,%s,%s,%s,%s,now())
        ON CONFLICT(profile_key) DO UPDATE SET model_id=excluded.model_id,model_revision=excluded.model_revision,
        dimensions=excluded.dimensions,pooling=excluded.pooling,normalized=excluded.normalized,
        corpus_vector_count=excluded.corpus_vector_count,generated_at=excluded.generated_at,seeded_at=now()""",
        (payload["model_id"],payload["revision"],payload["dimensions"],payload["pooling"],payload["normalize"],len(vectors),payload["generated_at"]))
    for s in sources:
        conn.execute("""INSERT INTO evidence_chunks(source_id,document_type,lifecycle_status,product_architecture,content,metadata,embedding,embedding_model)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(source_id) DO UPDATE SET document_type=excluded.document_type,
            lifecycle_status=excluded.lifecycle_status,product_architecture=excluded.product_architecture,
            content=excluded.content,metadata=excluded.metadata,embedding=excluded.embedding,
            embedding_model=excluded.embedding_model""",
            (s["source_id"],s["document_type"],s["status"],s["product_architecture"],s["title"]+" "+s["text"],json.dumps(s),vectors[s["source_id"]],payload["model_id"]))
print(f"Seeded {len(sources)} pgvector records with model revision {payload['revision']}")
