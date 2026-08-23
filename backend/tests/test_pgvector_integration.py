from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.repository import (
    EXPECTED_PGVECTOR_VERSION,
    EXPECTED_POSTGRES_MAJOR,
    PgVectorRepository,
    repository,
)

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not supplied; actual PostgreSQL/pgvector prerequisite unavailable")
    return url


@pytest.fixture(autouse=True)
def require_live_database() -> None:
    database_url()


def test_pgvector_contract_and_repository_transition():
    import psycopg

    url = database_url()
    with psycopg.connect(url) as conn:
        assert conn.info.server_version // 10_000 == EXPECTED_POSTGRES_MAJOR
        assert conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname='vector'"
        ).fetchone() == (EXPECTED_PGVECTOR_VERSION,)
        metadata = conn.execute(
            "SELECT model_id,model_revision,dimensions,pooling,normalized,corpus_vector_count "
            "FROM embedding_metadata WHERE profile_key='corpus'"
        ).fetchone()
        manifest = json.loads((ROOT / "data/model_manifest.json").read_text(encoding="utf-8"))
        assert metadata == (
            manifest["model_id"],
            manifest["revision"],
            manifest["dimensions"],
            manifest["pooling"],
            manifest["normalize"],
            41,
        )
        assert conn.execute(
            "SELECT count(*) FROM evidence_chunks WHERE vector_dims(embedding)=384"
        ).fetchone() == (41,)

    assert settings.database_url == url
    selected = repository()
    assert selected.mode == "postgresql_pgvector"
    assert selected.validate_readiness()["vector_count"] == 41


def test_pgvector_nearest_neighbor_self_match():
    payload = json.loads(
        (ROOT / "data/generated/embeddings.json").read_text(encoding="utf-8")
    )
    source_id = "PRJ-024"
    scores = PgVectorRepository(database_url()).semantic(payload["vectors"][source_id])
    winner = max(scores, key=scores.get)
    assert winner == source_id
    assert scores[winner] > 0.999


def test_reseed_restores_every_structured_source_column():
    import psycopg

    url = database_url()
    with psycopg.connect(url) as conn:
        conn.execute(
            "UPDATE evidence_chunks SET document_type='wrong',lifecycle_status='wrong',"
            "product_architecture='wrong',content='wrong',metadata='{}',embedding_model='wrong' "
            "WHERE source_id='PRJ-024'"
        )
    subprocess.run(
        [sys.executable, "scripts/seed_postgres.py"],
        cwd=ROOT,
        env=os.environ.copy(),
        check=True,
    )
    source = next(
        item
        for item in json.loads((ROOT / "data/corpus/sources.json").read_text(encoding="utf-8"))
        if item["source_id"] == "PRJ-024"
    )
    with psycopg.connect(url) as conn:
        restored = conn.execute(
            "SELECT document_type,lifecycle_status,product_architecture,content,metadata->>'source_id',embedding_model "
            "FROM evidence_chunks WHERE source_id='PRJ-024'"
        ).fetchone()
    assert restored == (
        source["document_type"],
        source["status"],
        source["product_architecture"],
        source["title"] + " " + source["text"],
        source["source_id"],
        "Xenova/all-MiniLM-L6-v2",
    )


def test_api_health_reports_postgresql_transition():
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_mode"] == "postgresql_pgvector"
    assert body["pgvector_active"] is True
