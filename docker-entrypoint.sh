#!/bin/sh
set -e

required_vars="DATABASE_URL SECRET_KEY JWT_SECRET_KEY"
for var_name in $required_vars; do
  if [ -z "$(eval echo \$$var_name)" ]; then
    echo "Missing required environment variable: $var_name"
    exit 1
  fi
done

echo "Running database migrations..."
attempt=1
max_attempts=5
until alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Migration failed after $attempt attempts."
    exit 1
  fi
  echo "Migration attempt $attempt failed; retrying in 5 seconds..."
  attempt=$((attempt + 1))
  sleep 5
done

echo "Starting application..."
exec "$@"
