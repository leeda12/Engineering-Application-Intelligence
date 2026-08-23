# Security, privacy, and trust boundaries

Uploads are restricted to PDF, a 5 MB default maximum, and the controlled form signature. The service never executes uploads. Pydantic validates requests; React escapes displayed strings; generated SVG is assembled only from validated enums and numeric dimensions. CORS permits only the configured local frontend. Security headers deny framing, sniffing, broad permissions, and remote resource loading. No secrets, telemetry, analytics, cookies, external fonts/scripts/images, or runtime model downloads are used.

Audit records contain fictional application identifiers, review notes, source IDs, state transitions, and idempotency keys. Notes are length-limited. `.env`, uploads, vectors, and audit artifacts are ignored.
