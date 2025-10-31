## The PostgreSQL Replication Deep Dive

To reproduce replication strategies described in the book

_From Fast Writes to Zero Data Loss_

## Context

1. Postgres
2. Docker + (compose plugin)
3. k6

## Agenda

### Module 1: Cluster Initialization (Base Backup)

**Goal**: Create a 2-node (Primary + Standby) cluster from scratch.

    1.1. Configure & Start the Leader:

        Define postgres-primary in Docker Compose.

        Configure postgresql.conf for replication (e.g., wal_level = replica).

    1.2. Create the Dataset:

        Use an init-db.sh script to load the Pagila sample database (.sql dump) on the Primary. This gives us a realistic dataset to query.

    1.3. Start the Follower (The "Snapshot"):

        Start the postgres-standby container.

        Use an init-standby.sh script that runs pg_basebackup.

        Narrative: We are taking a full physical snapshot from the Leader to initialize the Follower. This is our "Base Backup" process.

    Outcome: A 2-node cluster is running. The Standby is streaming from the Primary.

### Module 2: Asynchronous Replication (The Default & The "Lag")

**Goal**: Demonstrate the default replication mode: fast writes, but with measurable "replication lag" and risk.

    2.1. Run a Mixed Workload:

        Use k6 to run a mixed read/write script (pagila_read_write_test.js).

        Writes go to the postgres-primary (e.g., simulating new rentals).

        Reads go to the postgres-standby (e.g., browsing films).

    2.2. Observe the Lag:

        Connect to the Primary and run SELECT * FROM pg_stat_replication;.

        Narrative: Show the replay_lag. This is Eventual Consistency in action. The Follower is always slightly behind.

    2.3. The "Async" Failure Test (RPO > 0):

        While the k6 script is running, abruptly kill the postgres-primary container.

        Narrative: We'll see the k6 script report write failures. More importantly, we can query the Standby and show that the very last successful writes from k6 are missing. This demonstrates data loss (a non-zero RPO).

    Outcome: Understand the speed vs. data-loss trade-off of Asynchronous replication.

### Module 3: Synchronous Replication (The "Safe" Mode)

**Goal**: Demonstrate "zero data loss" (RPO ≈ 0) and its performance cost.

    3.1. Reconfigure for Sync:

        Restart the cluster.

        Modify postgresql.conf on the Primary to set synchronous_standby_names = 'postgres-standby'.

    3.2. Observe Write Latency:

        Rerun the same k6 write script against the Primary.

        Narrative: Look at the k6 output. The p90 write latency will be significantly higher. We are now waiting for a network round-trip to the Standby for every single write.

    3.3. The "Sync" Failure Test (RPO ≈ 0):

        Kill the postgres-primary again.

        Narrative: This time, when we check the Standby, no data is lost. Every write that k6 reported as "successful" is present.

    Outcome: Understand the performance cost required to guarantee zero data loss.

### Module 4: High Availability Demos (Reacting to Failure)

**Goal**: Show how the cluster heals and recovers from outages.

    4.1. Demo: Follower Failure (Catch-up Recovery)

        Action: Stop the postgres-standby container.

        Observe: The k6 write script on the Primary will stall (if in Sync mode) or continue (if in Async mode).

        Action: Wait 30 seconds, then restart the postgres-standby container.

        Observe: Watch the container logs. The Standby automatically reconnects and replays the WALs it missed.

        Narrative: This is Catch-up Recovery. The node self-heals without data loss.

    4.2. Demo: Leader Failure (Manual Failover)

        Action: Stop the postgres-primary container.

        Observe: All writes from k6 are now failing. The cluster is "read-only."

        Action: In the postgres-standby container, run the promotion command: pg_ctl promote.

        Observe: The Standby instantly becomes the new Primary.

        Action: Re-route the k6 write workload to the new Primary (e.g., by changing the k6 script's connection string and re-running).

        Narrative: This is a Failover. We have restored write availability. We'll also discuss how to bring the old primary back as a new follower.

### Module 5: (Bonus) Differentiating Replication Mechanisms

**Goal**: Briefly explain why WAL streaming is superior to older methods.

    This is a "slides-only" section, not a demo.

    WAL Shipping (What we used): Physical replication. Fast, byte-for-byte. But, it's tied to the OS and Postgres version.

    Logical Replication (Row-based): Replicates changes (like "row 5 updated"), not physical bytes.

        Use Case: This is how you replicate between different Postgres versions (addressing your "breaks on different versions" point) or send data to other systems (Change Data Capture).

    Trigger-Based (Bucardo): The old way. Slow, high overhead, and hard to maintain.

    Statement-Based: Prone to errors (e.g., NOW() or RAND()). Not used by Postgres for transactional replication.




### Working with replication strategies

* Practice with leader-based replication strategies
* Configure a database cluster leader
  * Rollout the test dataset
  * Do a base backup (pg_dump)
* Run some workloads to generate data
* Run a replica
  * Apply the base backup (pg_restore)
  * Configure a synchronous replication (master/replica)
  * Use statement replication
  * Show the amount of traffic exchanged between the nodes
* Show how writes are accepted and rejected when required nodes are unavailable
* Run another replica
  * Apply the base backup (pg_restore)
  * Configure an asynchronous confirmation using Burcado
  * Use replication
  * Show the amount of traffic exchanged between the nodes
* Run another replica
  * Use WAL replication (show how it breaks when there are different versions)
  * Show the amount of traffic exchanged between the nodes
* Reproduce catch-up recovery
  * Stop the container
  * Wait
  * Start the container again
* Reproduce failover
  * Drop the leader
  * How to configure the failover in docker environment ?

### Showing consistency problems

* Reproduce read-after-write consistency pattern
  * Implement a multi-leader setup
* Reproduce a monotonic read consistency pattern
  * 