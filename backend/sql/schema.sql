CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embedding_metadata (
  profile_key text PRIMARY KEY CHECK (profile_key = 'corpus'),
  model_id text NOT NULL,
  model_revision text NOT NULL,
  dimensions integer NOT NULL CHECK (dimensions = 384),
  pooling text NOT NULL CHECK (pooling = 'mean'),
  normalized boolean NOT NULL CHECK (normalized),
  corpus_vector_count integer NOT NULL CHECK (corpus_vector_count > 0),
  generated_at timestamptz NOT NULL,
  seeded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_chunks (
  source_id text PRIMARY KEY,
  document_type text NOT NULL,
  lifecycle_status text NOT NULL,
  product_architecture text NOT NULL,
  content text NOT NULL,
  metadata jsonb NOT NULL,
  embedding vector(384) NOT NULL CHECK (vector_dims(embedding) = 384),
  embedding_model text NOT NULL
);
CREATE INDEX IF NOT EXISTS evidence_embedding_hnsw ON evidence_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS evidence_content_fts ON evidence_chunks USING gin (to_tsvector('english', content));
