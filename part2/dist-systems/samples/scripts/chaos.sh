#!/bin/bash
echo "🐒 Releasing the monkey..."
docker-compose --profile chaos-testing up -d pumba
echo "✅ Pumba is active. Every 30s a random node is paused for 10s."

sleep 90

echo "🍌 Luring the monkey away..."
docker-compose --profile chaos-testing stop pumba
echo "✅ Chaos stopped."