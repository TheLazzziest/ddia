#!/bin/bash
echo "🚧 Creating a network partition for node1..."
docker network disconnect ddia_lab_net node1
echo "✅ node1 is now isolated. Check if the cluster triggers a new leader election."

sleep 90

echo "🩹 Healing the network partition..."
docker network connect ddia_lab_net node1
echo "✅ node1 rejoined the network."