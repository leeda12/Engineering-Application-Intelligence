from __future__ import annotations

import math
from typing import Any

from .config import settings
from .data import corpus, embedding_manifest, embedding_payload, vectors

EXPECTED_POSTGRES_MAJOR = 16
EXPECTED_PGVECTOR_VERSION = "0.8.6"
REQUIRED_INDEXES = {"evidence_embedding_hnsw", "evidence_content_fts"}


class PgVectorConfigurationError(RuntimeError):
    """The explicitly configured PostgreSQL service cannot satisfy the vector contract."""


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


class FileVectorRepository:
    mode = "compatibility_file_vector"

    def records(self) -> list[dict]:
        return corpus()

    def semantic(self, query_embedding: list[float] | None) -> dict[str, float]:
        stored = vectors()
        return {
            record["source_id"]: max(
                0.0, cosine(query_embedding, stored.get(record["source_id"]))
            )
            for record in corpus()
        }


class PgVectorRepository:
    mode = "postgresql_pgvector"

    def __init__(self, url: str):
        self.url = url

    def records(self) -> list[dict]:
        return corpus()

    def validate_readiness(self) -> dict[str, Any]:
        import psycopg

        manifest = embedding_manifest()
        payload = embedding_payload()
        expected_count = len(corpus())

        try:
            with psycopg.connect(self.url, connect_timeout=3) as conn:
                postgres_major = conn.info.server_version // 10_000
                extension = conn.execute(
                    "SELECT extversion FROM pg_extension WHERE extname='vector'"
                ).fetchone()
                tables = conn.execute(
                    "SELECT to_regclass('public.embedding_metadata'), "
                    "to_regclass('public.evidence_chunks')"
                ).fetchone()
                if not extension:
                    raise PgVectorConfigurationError(
                        "Configured PostgreSQL is missing the vector extension"
                    )
                if not tables or not all(tables):
                    raise PgVectorConfigurationError(
                        "Configured PostgreSQL is missing the required pgvector schema; run scripts/seed_postgres.py"
                    )

                metadata = conn.execute(
                    "SELECT model_id,model_revision,dimensions,pooling,normalized,corpus_vector_count "
                    "FROM embedding_metadata WHERE profile_key='corpus'"
                ).fetchone()
                vector_state = conn.execute(
                    "SELECT count(*), "
                    "coalesce(bool_and(vector_dims(embedding)=%s),false), "
                    "coalesce(bool_and(embedding_model=%s),false) "
                    "FROM evidence_chunks",
                    (manifest["dimensions"], manifest["model_id"]),
                ).fetchone()
                index_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE schemaname='public' AND tablename='evidence_chunks'"
                    ).fetchall()
                }
        except PgVectorConfigurationError:
            raise
        except Exception as exc:
            raise PgVectorConfigurationError(
                f"Configured PostgreSQL/pgvector could not be validated ({type(exc).__name__})"
            ) from exc

        errors: list[str] = []
        if postgres_major != EXPECTED_POSTGRES_MAJOR:
            errors.append(
                f"PostgreSQL major version {postgres_major} does not match required {EXPECTED_POSTGRES_MAJOR}"
            )
        if extension[0] != EXPECTED_PGVECTOR_VERSION:
            errors.append(
                f"pgvector version {extension[0]} does not match required {EXPECTED_PGVECTOR_VERSION}"
            )
        expected_metadata = (
            manifest["model_id"],
            manifest["revision"],
            manifest["dimensions"],
            manifest["pooling"],
            manifest["normalize"],
            len(payload["vectors"]),
        )
        if metadata != expected_metadata:
            errors.append("database embedding metadata does not match the pinned local model contract")
        if not vector_state or vector_state[0] != expected_count:
            actual = vector_state[0] if vector_state else 0
            errors.append(f"database contains {actual} evidence vectors; expected {expected_count}")
        elif not vector_state[1]:
            errors.append(f"one or more database vectors are not {manifest['dimensions']}-dimensional")
        elif not vector_state[2]:
            errors.append("one or more database records use an incompatible embedding model")
        missing_indexes = REQUIRED_INDEXES - index_names
        if missing_indexes:
            errors.append(f"database is missing required indexes: {', '.join(sorted(missing_indexes))}")
        if errors:
            raise PgVectorConfigurationError(
                "Configured PostgreSQL/pgvector is incompatible: " + "; ".join(errors)
            )

        return {
            "postgres_major": postgres_major,
            "pgvector_version": extension[0],
            "vector_count": vector_state[0],
            "model_revision": metadata[1],
        }

    def ready(self) -> bool:
        self.validate_readiness()
        return True

    def semantic(self, query_embedding: list[float] | None) -> dict[str, float]:
        if query_embedding is None:
            return {}
        expected_dimensions = embedding_manifest()["dimensions"]
        if len(query_embedding) != expected_dimensions:
            raise ValueError(
                f"query embedding has {len(query_embedding)} dimensions; expected {expected_dimensions}"
            )

        import psycopg
        from pgvector import Vector
        from pgvector.psycopg import register_vector

        try:
            with psycopg.connect(self.url) as conn:
                register_vector(conn)
                vector_parameter = Vector(query_embedding)
                rows = conn.execute(
                    "SELECT source_id, 1 - (embedding <=> %s) AS similarity "
                    "FROM evidence_chunks ORDER BY embedding <=> %s LIMIT 100",
                    (vector_parameter, vector_parameter),
                ).fetchall()
        except Exception as exc:
            raise PgVectorConfigurationError(
                f"Configured PostgreSQL/pgvector query failed ({type(exc).__name__})"
            ) from exc
        return {source_id: float(score) for source_id, score in rows}


def repository() -> FileVectorRepository | PgVectorRepository:
    if settings.retrieval_mode == "file":
        return FileVectorRepository()
    if not settings.database_url:
        if settings.retrieval_mode == "postgresql":
            raise PgVectorConfigurationError(
                "RETRIEVAL_MODE=postgresql requires DATABASE_URL"
            )
        return FileVectorRepository()

    repo = PgVectorRepository(settings.database_url)
    repo.validate_readiness()
    return repo
