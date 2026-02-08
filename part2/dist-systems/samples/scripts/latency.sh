#!/bin/bash
echo "⏳ Injecting 2000ms latency to node1 via Toxiproxy..."
curl -X POST http://localhost:8474/proxies/node1_proxy/toxics \
  -d '{
    "type": "latency",
    "attributes": { "latency": 2000, "jitter": 500 }
  }'