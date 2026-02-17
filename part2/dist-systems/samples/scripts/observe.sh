#!/bin/bash
INTERVAL=2
echo "Observing node1 and node2 every 2s"
echo "Run latency.sh, chaos.sh, throttle.sh or partitioning.sh in another terminal."
echo "─────────────────────────────────────────────────────────────────────────────"

while true; do
  TS=$(date +%H:%M:%S)
  
  # node1
  NODE1=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --connect-timeout 1 --max-time 5 http://localhost:10001/ 2>/dev/null)
  if [[ "$NODE1" == "200 "* ]]; then
    NODE1_TIME=$(echo "$NODE1" | awk '{print $2}')
    NODE1_STATUS="UP  ${NODE1_TIME}s"
  else
    NODE1_STATUS="DOWN"
  fi
  
  # node2
  NODE2=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --connect-timeout 1 --max-time 5 http://localhost:10002/ 2>/dev/null)
  if [[ "$NODE2" == "200 "* ]]; then
    NODE2_TIME=$(echo "$NODE2" | awk '{print $2}')
    NODE2_STATUS="UP  ${NODE2_TIME}s"
  else
    NODE2_STATUS="DOWN"
  fi
  
  printf "%s  node1: %-18s  node2: %s\n" "$TS" "$NODE1_STATUS" "$NODE2_STATUS"
  sleep "$INTERVAL"
done