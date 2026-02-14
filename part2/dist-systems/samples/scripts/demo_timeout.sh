#!/bin/bash
echo "Timeout vs Latency Demo"
echo "This shows that a short timeout + network delay = false 'node dead' signal"
echo "─────────────────────────────────────────────────────────────────────────────"

echo ""
echo "1. Request with 5s timeout (should succeed even with latency):"
if curl -s -o /dev/null -w "   HTTP %{http_code}, time %{time_total}s\n" --max-time 5 http://localhost:10001/; then
  echo "   Success"
else
  echo "   Failed (connection issue?)"
fi

echo ""
echo "2. Request with 1s timeout:"
echo "   (If latency.sh is active, node responds in ~2s — timeout will fail)"
if curl -s -o /dev/null -w "   HTTP %{http_code}, time %{time_total}s\n" --max-time 1 http://localhost:10001/ 2>/dev/null; then
  echo "   Success (latency < 1s or latency.sh not active)"
else
  echo "   Timeout! Node is alive but slow. False 'dead' signal."
  echo "   Lesson: Simple timeouts can't distinguish slow from dead."
fi

echo ""
