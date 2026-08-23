# Local PostgreSQL/pgvector validation

The database contract is PostgreSQL 16, pgvector 0.8.6, and the exact embedding profile in `data/model_manifest.json`. The pinned Compose service binds only to `127.0.0.1`, has a readiness health check, and stores database files in the named `engineering-application-intelligence-pgvector-data` volume.

No database URL means the API intentionally reports `compatibility_file_vector`. `RETRIEVAL_MODE=postgresql` without `DATABASE_URL`, or any configured database that fails the contract, produces a stable `pgvector_configuration_error` response with HTTP 503. `RETRIEVAL_MODE=file` is the only explicit override.

## Clean validation lifecycle

Set a disposable local test password in the current shell, then run the orchestrator after Docker is available:

```powershell
$env:POSTGRES_PASSWORD = Read-Host "Temporary local PostgreSQL test password"
python scripts/validate_postgres.py
```

The orchestrator removes only this Compose project's previous test container and named volume, starts a clean healthy database, seeds the corpus, runs all marked pgvector integration tests, and removes the test database afterward. Use `--keep-database` only when a persistent local development database is wanted.

The integration suite verifies server and extension versions, embedding metadata, vector count and dimensions, repository selection, exact self-neighbor cosine retrieval, structured-column restoration on reseed, and the API health transition to `postgresql_pgvector`.

This lifecycle has been validated in practice on the target Windows laptop using Docker Desktop's WSL 2 backend. The preserved development volume is stopped, not deleted, during normal shutdown with `docker compose stop postgres`; `docker desktop stop` then releases the laptop's Docker memory.
