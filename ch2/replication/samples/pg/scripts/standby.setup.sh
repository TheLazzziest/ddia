#!/bin/sh
set -e

# --- 1. Wait for Primary to be Healthy ---
echo "STANDBY: Waiting for postgres-primary to be available..."
until pg_isready -h postgres-primary -U "$POSTGRES_USER"; do
  echo "STANDBY: Primary not ready. Waiting..."
  sleep 2
done

echo "STANDBY: Primary is ready. Starting base backup..."

# --- 2. Perform the initial base backup (Snapshot) ---
# We MUST remove any old data first if the container is restarting
rm -rf /var/lib/postgresql/data/*

# -D: target directory
# -h: host to connect to (our primary)
# -U: replication user
# -v -P: verbose with progress
# -R: (CRITICAL) creates the standby.signal file and connection
#     info in postgresql.auto.conf automatically.
pg_basebackup -h postgres-primary -D /var/lib/postgresql/data \
              -U "$POSTGRES_USER" -v -P -R

# Change the owner of the *entire* data directory to the 'postgres' user
chown -R postgres:postgres /var/lib/postgresql/data

# Set correct permissions on the new data directory
chmod 0700 /var/lib/postgresql/data

echo "STANDBY: Base backup complete. Starting PostgreSQL as Standby..."

# --- 3. Start PostgreSQL with the custom configuration ---
# We now start the postgres server. It will see the standby.signal
# file and start in standby (replication) mode automatically.
exec gosu postgres postgres -c config_file=/usr/local/share/postgresql/postgresql.conf