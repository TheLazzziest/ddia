#!/bin/sh
set -e

echo "Running setup_db.sh: Waiting for postgres to be ready..."
# This script doesn't need to do anything,
# the entrypoint will automatically run all .sql files
# after this script finishes. We just use it for ordering.

# We use 'trust' here to simplify the workshop setup.
echo "host replication all 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"

echo "Enforcing SYNCHRONOUS COMMIT."
PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  -- Set the commit level to ON
  ALTER SYSTEM SET synchronous_commit = on; 
  
  SELECT pg_reload_conf();
EOSQL


echo "Setup complete. The entrypoint will now load pagila.sql."