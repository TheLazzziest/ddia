# Distributed Systems Laboratory

This lab environment allows you to inject faults into a three-node cluster to observe how distributed systems handle "The Trouble with Distributed Systems."

Two nodes behind a proxy; you run scripts to add latency, partitions, and chaos, then watch what happens. Needs Docker and Docker Compose. All commands from the `samples/` folder.

Start the stack:

```bash
docker-compose up -d
```

You get Toxiproxy and two nodes. Traffic goes through the proxy: node1 at `localhost:10001`, node2 at `localhost:10002`. The scripts add latency through the proxy or simulate faults (throttle, partition, chaos).

**Terminal 1** — run the observer and leave it open. It prints node1 and node2 status every 2 seconds (UP/DOWN and response time). You’ll see the effect of the other scripts here.

```bash
bash ./scripts/observe.sh
```

**Terminal 2** — run the rest in this order:

1. Adds ~2s latency to node1 via Toxiproxy.

   ```bash
   bash ./scripts/latency.sh
   ```

2. One request with 5s timeout (succeeds), one with 1s (times out when latency is on). Shows that timeouts can’t tell slow from dead.

   ```bash
   bash ./scripts/demo_timeout.sh
   ```

3. Starts Pumba: every 30s a random node is paused for 10s. Runs ~90s then stops.

   ```bash
   bash ./scripts/chaos.sh
   ```

4. Limits node1 to 0.1 CPU and 10MB RAM for ~90s, then restores. Node may go slow or show as DOWN in the observer.

   ```bash
   bash ./scripts/throttle.sh
   ```

5. Disconnects node1 from the network for ~90s, then reconnects. In the observer, node1 goes DOWN and back UP.

   ```bash
   bash ./scripts/partitioning.sh
   ```
