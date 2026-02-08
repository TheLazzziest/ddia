#!/bin/bash
echo "🐌 Throttling node1 to 10% CPU and 10MB RAM..."
docker update --cpus 0.1 --memory 10M node1
echo "✅ node1 is now resource-constrained. Watch for timeout-based fault detection."

sleep 90

echo "🐌 Recovering node1 to 50% CPU and 50MB RAM..."
docker update --cpus 0.5 --memory 50M node1