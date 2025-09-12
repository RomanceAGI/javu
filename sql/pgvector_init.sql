CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS vectors (
  id BIGSERIAL PRIMARY KEY,
  v vector(256) NOT NULL,
  text TEXT NOT NULL,
  meta JSONB
);
-- Opsional: index approximate
-- CREATE INDEX IF NOT EXISTS vectors_v_idx ON vectors USING ivfflat (v vector_cosine_ops) WITH (lists = 100);
