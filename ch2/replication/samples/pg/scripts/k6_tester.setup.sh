#!/bin/sh
set -e

BINARY_PATH="/home/k6/bin/k6-with-sql"

if [ ! -f "$BINARY_PATH" ]; then

  # Ensure the target directory exists (Docker might not create it)
  mkdir -p /home/k6/bin
  
  # Build the binary using the full path and output it to our volume
  xk6 build --verbose --os "$ARCH" \
    --with github.com/grafana/xk6-sql \
    --with github.com/grafana/xk6-sql-driver-postgres \
    -o "$BINARY_PATH"
  
  echo "K6: Build complete. Binary saved for future runs."
else
  echo "K6: Found existing binary at $BINARY_PATH. Skipping build."
fi

echo "K6: Starting tests...";
$BINARY_PATH run --insecure-skip-tls-verify --verbose --log-output stderr --log-format raw "$1"