## The PostgreSQL Replication Deep Dive

To practically demonstrate the WAL (Write-Ahead Log) based replication strategies—Asynchronous, Synchronous, and Delayed—and their associated trade-offs in performance, data loss, and availability.

## Requirements

1. Postgres
2. Docker + (compose plugin)
3. k6

## Agenda

### Prerequisites

**Goal**: To make sure the environment can be reproduced

    1. Make sure you use `docker compose` (or `podman-compose`) can process `docker-compose.yml` correctly  
    2. Make sure k6-tester can be built on your platform

### Module 1: Run a cluster

**Goal**: Create a 2-node (Primary + Standby in Sync Mode) cluster from scratch.

**Setup Procedure**

1. **Start**: Run `docker compose up --build -d pgbouncer`
    
    **Important Note on Replication Slots:** For robust replication, it's highly recommended to use replication slots. A replication slot prevents the primary from removing WAL files before the standby has received them. **Try yourself!**

2. **Verification**: To check the status of replication, you can view active replication connections and slots.
    - **Check replication stats:**
      ```sh
      docker compose exec postgres-primary psql -U postgres -c "SELECT usename, application_name, client_hostname, replay_lag, sync_priority, sync_state, reply_time FROM pg_stat_replication;"
      ```
      This will show the **connected standby in sync mode**.
    - **Check replication slots:**
      ```sh
      docker compose exec postgres-primary psql -U postgres -c "SELECT slot_name, active FROM pg_replication_slots;"
      ```
      If you created a slot, you will see it here and whether it's active.

3. **Test**: Let's run a writing worker
    - **Run k6 write scenario**
    ```sh
    docker compose up k6-tester-writer
    ```
    The worker must produce a successful write rate in logs
    - **Check the write queue in pgbouncer**:
    ```sh
    docker compose exec pgbouncer psql -h 127.0.0.1 -p 6432 -U postgres pgbouncer -c "SHOW POOLS;"
    ```
    `cl_waiting` must be equal to 0

**Outcome**: A 2-node cluster with a load balancer running. The Standby is streaming from the Primary.

### Module 2: Synchronous Replication (The "Safe" Mode)

**Goal**: Demonstrate "zero data loss" (RPO ≈ 0)

1. **Start**: The 2-node cluster must be working and healthy.

2. **Verification**: To check the zero-data loss

    - **Open a client session in a primary node**
    ```sh
    docker compose exec postgres-primary psql -U postgres -d db
    ```
    - **Check the connections' activity**
    ```sql
    SELECT 
      pid,
      usename,
      state,
      wait_event,
      wait_event_type,
      NOW() - query_start as waiting_for,
      query
    FROM pg_stat_activity
    WHERE wait_event = 'SyncRep';
    ```
    You must see no activity
    - **Run k6 write scenario**
    ```sh
    docker compose up k6-load-writer
    ```
    The worker must produce a successful write rate in logs

3. **Test**: Check the sync replication guarantees
    - **Stop the sync standby**
    ```sh
    docker compose stop postgres-sync-standby
    ```
    - **Check the logs of the worker in the docker**
    - **Check the connections' activity**
    ```sql
    SELECT 
      pid,
      usename,
      state,
      wait_event,
      wait_event_type,
      NOW() - query_start as waiting_for,
      query
    FROM pg_stat_activity
    WHERE wait_event = 'SyncRep';
    ```
    You will see a different picture. Why ?

4. **Outcome**: Understand the guarantees of zero data loss.

### Module 3: Asynchronous Replication (The Default & The "Lag")

**Goal**: Demonstrate fast writes with asynchronous replication and observe the resulting "replication lag".

1. **Setup**: Configure the primary for asynchronous replication.
    - **Run the async replica to the primary and turn off synchronous commit:**
    ```sh
    docker compose up -d postgres-async-standby 
    ```
    You should see another replica in `pg_stat_replication`

2. **Start**: Run a continuous write workload to generate WAL files that need to be replicated.
    - **Run k6 write scenario:**
    ```sh
    docker compose up k6-load-writer
    ```
    The worker should produce a high rate of successful writes, as it no longer waits for the replica.

3. **Verification**: While the writer is running, check the replication statistics on the primary to see the lag.
    - **Connect to the primary and query `pg_stat_replication`:**
    ```sh
    docker compose exec postgres-primary psql -U postgres -d db -c "SELECT application_name, state, sync_state, replay_lag FROM pg_stat_replication;"
    ```
    - **Observe the output:**
      - `postgres-sync-standby` will now show its `sync_state` as `async`.
      - The `replay_lag` column shows the time delay between the primary writing a transaction and the standby replaying it. This is eventual consistency in action. You may need to run the command several times to see the lag fluctuate under load.

4. **Test (RPO > 0)**: Demonstrate the risk of data loss.
    - While the k6 script is running, abruptly stop the `postgres-primary` container.
    ```sh
    docker compose stop postgres-primary
    ```
    - The k6 script will report write failures. More importantly, if you were to promote the standby and inspect the data, you would find that the very last writes acknowledged by the primary are missing. This demonstrates a non-zero Recovery Point Objective (RPO).

5. **Outcome**: Understand the trade-off of asynchronous replication: you get faster write performance at the cost of a measurable replication lag and the risk of data loss on primary failure.

### Module 4: Manual Failover (The High Availability Test)

**Goal**: Demonstrate how to manually recover from a primary node failure by promoting a synchronous standby, ensuring zero data loss (RPO ≈ 0).

1. **Setup**: Ensure the cluster is running in synchronous mode with an active write workload.
    - **Start the k6 writer:**
    ```sh
    docker compose up k6-load-writer
    ```
    - **Verify writes are succeeding:** Check the logs to see successful rental and payment insertions.

2. **Test**: Simulate a primary failure and perform a manual failover.
    - **Stop the primary node abruptly.**
    ```sh
    docker compose stop postgres-primary
    ```
    - **Observe the impact:** The `k6-load-writer` will immediately stall and start logging connection errors. This is because `pgbouncer` can no longer reach the primary, and write availability is lost.

    - **Promote the synchronous standby to become the new primary.**
    ```sh
    docker compose exec postgres-sync-standby pg_ctl promote
    ```
    The standby will stop following the old primary and become a writable node.

    - **Re-route traffic to the new primary.** In a real scenario, you would update DNS or a load balancer. Here, we will restart `pgbouncer` and point it to the new primary.
    ```sh
    docker compose stop pgbouncer
    docker compose run --service-ports -d pgbouncer
    ```
    *(Note: We use `run` to easily override the environment variable. You would typically have a more robust way to manage the `DB_HOST` configuration.)*

3. **Verification**: Confirm that write availability is restored and no data was lost.
    - The `k6-load-writer` logs should show that writes are succeeding again, now directed to the newly promoted primary.
    - Because we were using synchronous replication, every write that was successfully acknowledged to the k6 client before the crash is guaranteed to be present on the new primary. **Zero data was lost (RPO ≈ 0)**.

4. **Outcome**: Understand the manual steps required for failover and appreciate the time it takes (Recovery Time Objective). This highlights the need for automation.

---

### From Manual Failover to Production-Ready HA

The manual failover process is slow, error-prone, and requires human intervention, leading to a high **Recovery Time Objective (RTO)**. In production, this process is automated by cluster management tools.

#### Patroni
**Patroni** is a popular open-source tool that provides a template for building a highly available PostgreSQL cluster. It uses a distributed consensus store (like etcd, Consul, or ZooKeeper) to manage the cluster state.
- **Automated Failover**: It constantly monitors the primary's health. If the primary fails, Patroni automatically runs an election and promotes the healthiest standby in seconds.
- **Configuration Management**: Manages `postgresql.conf` settings across all nodes.
- **REST API**: Provides an API to query the health and status of the entire cluster.

#### Citus (Hyperscale)
While Patroni focuses on high availability, **Citus** is an extension that transforms PostgreSQL into a distributed database, focusing on **horizontal scaling (sharding)**.
- **Distributed Query Engine**: It shards tables across multiple PostgreSQL nodes and parallelizes queries across them for massive performance gains.
- **Built-in HA**: Citus can be combined with standard PostgreSQL streaming replication on each node, and tools like Patroni can be used to manage failover for both the coordinator and the worker nodes.

In summary, while it's essential to understand the underlying mechanics of replication and failover, production systems rely on tools like **Patroni** to automate HA and tools like **Citus** to achieve massive scale.


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