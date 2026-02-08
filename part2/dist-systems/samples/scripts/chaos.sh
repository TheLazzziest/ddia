#!/bin/bash
echo "🐒 Releasing the monkey..."
docker-compose up -d pumba --profile chaos-testing
echo "✅ Pumba is active. Every 30 seconds, a random node will be killed."
echo "💡 TIP: Make sure your nodes have 'restart: always' in docker-compose if you want them to recover!"

sleep 90

echo "🍌 Luring the monkey away..."
docker-compose stop pumba
echo "✅ Chaos stopped."