#!/bin/sh
set -e

if [ -n "$RAG_MODELS_S3_BUCKET" ]; then
  aws s3 sync "s3://${RAG_MODELS_S3_BUCKET}/${RAG_MODELS_S3_PREFIX:-models}" /app/data/models
fi

# Seed the exercise catalogue into MongoDB on first boot. Idempotent and a
# fast no-op once the collection is populated (see scripts/seed_exercises.py).
# Non-fatal: a seeding hiccup must not stop the API from coming up.
if [ "${SKIP_EXERCISE_SEED:-0}" != "1" ]; then
  python -m scripts.seed_exercises || echo "[entrypoint] exercise seed failed — continuing"
fi

exec "$@"
