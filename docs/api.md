# API

All errors use `{ "error": { "code", "message", "details", "request_id" } }`.

- `GET /` (service discovery)
- `GET /docs` (self-hosted interactive reference)
- `GET /openapi.json`

- `GET /api/v1/health`
- `GET /api/v1/applications`
- `POST /api/v1/applications/extract` (multipart controlled PDF)
- `POST /api/v1/requirements/validate`
- `POST /api/v1/evidence/search`
- `POST /api/v1/projects/rank`
- `POST /api/v1/analysis/preliminary`
- `POST /api/v1/schematic/generate`
- `POST /api/v1/reviews/propose`
- `POST /api/v1/reviews/decision`
- `GET /api/v1/audit/{application_id}`
- `GET /api/v1/evidence/{source_id}`

Example search request:

```json
{"query":"redundant 180 kW cooling with Modbus", "query_embedding":[0.01], "architecture":"dual_loop"}
```

Evidence search permits an omitted vector for exact-identifier lookup. Comparable-project ranking and preliminary analysis require a genuine 384-value query embedding so the documented semantic component cannot silently collapse to zero.
