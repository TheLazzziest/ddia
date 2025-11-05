---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
marp: true
---

# Welcome

![bg right](../assets/ddia.png)

---

### **Replication**

**Replication** - keeping a copy of the same data on multiple connected nodes.

#### Question: how do we ensure that all the data ends up on all the replicas?

---

### **Replication**

**Categories**: <!-- They are orthogonal to each other.--> 

* **Timing/synchronicity** - when the replica acknowledges a successful write. 
<!-- impacting data integrity (RPO) and performance (RTO) -->
* **Roles/architecture** - the relationship between nodes and which ones handle writes/reads
<!-- -->
* **Functional mode/availability** - how the replica is utilized during normal operation.

---

### **Replication**

#### Timing

<!-- What are the advantages of synchronous approach ? - guarantess of up-to-date copy -->

|Strategy|Write Acknowledgment|Data Loss <!-- RPO -->|Primary Use Case|
| :--- | :--- | :--- | :--- |
| **Synchronous** | Primary waits for the replica(s) to confirm the write is received <!-- durable before confirming success to the client. --> |RPO ≈ 0 <!-- (Zero data loss is guaranteed on failover) --> | Financial transactions and mission-critical data where integrity is paramount.|

---

### **Replication**

#### Timing

<!-- What are the advantages of semi-synchronous approach ? - guarantess of up-to-date copy -->

|Strategy|Write Acknowledgment|Data Loss <!-- RPO -->|Primary Use Case|
| :--- | :--- | :--- | :--- |
| **Semi-synchronous** | a Primary waits for at least one Standby to confirm it has received the write-ahead log (WAL) data and successfully written it to disk | RPO > 0 <!-- (technically possible if Standby fails immediately after its disk write) --> | Switching between async/sync modes due to failovers <!-- if the Standby fails to acknowledge the write within a defined timeout, the Primary automatically reverts to Asynchronous mode to prevent blocking the entire system. --> |
---

### **Replication**

#### Timing

<!-- What are the advantages of asynchronous approach ? - guarantess of up-to-date copy -->

|Strategy|Write Acknowledgment|Data Loss <!-- RPO -->|Primary Use Case|
| :--- | :--- | :--- | :--- |
| **Asynchronous** | Primary confirms the write immediately to the client <!-- without waiting for the replica(s) acks which happen slightly later. -->| RPO > 0 <!-- (Potential for slight data loss upon Primary failure) --> | Most web workloads where low write latency is critical (e.g., social media posts)|

---

### **Replication**

#### Artchitecture

| Architecture | Write Flow (Lowest -> Highest) | Scalability Type |
| :--- | :--- | :--- |
|**Single-Leader** (Master-Slave / Primary-Standby) | "Writes go only to one designated node (the Primary/Master) <!-- which then asynchronously or synchronously replicates to all others. --> | Excellent for Read Scaling |

---

### **Replication**

#### Artchitecture

| Architecture | Write Flow (Lowest -> Highest) | Scalability Type |
| :--- | :--- | :--- |
| **Multi-Leader (Multi-Master)** | "Writes can be accepted by multiple leaders <!-- who then replicate to each other --> | Excellent for Multi-Region Writes and high write availability <!-- but introduces complex write conflict resolution --> |

---

### **Replication**

#### Artchitecture

| Architecture | Write Flow (Lowest -> Highest) | Scalability Type |
| :--- | :--- | :--- |
| **Leaderless** | Writes can be sent to any node. Confirmation is based on quorum <!-- The client or a coordinator decides when a write is successful based on a quorum (W+R>N) --> | Used in many NoSQL and distributed storage systems (e.g., Cassandra) |

---

### **Replication**

Why Nodes Fail: Causes of Outages

Any event that renders a node (Primary or Follower) unavailable or unable to participate fully in the cluster's function. Failures are the norm, not the exception.

---

### **Replication**

#### Common Causes

| Category | Reason | Impact |
| :--- | :--- | :--- |
| **Planned Maintenance** | **Planned Restarts, Upgrades, or Configuration Changes.** | Brief downtime is expected, but *zero* service interruption should be the goal via **Rolling Upgrades** and **Failover**. |

---

### **Replication**

#### Common Causes

| Category | Reason | Impact |
| :--- | :--- | :--- |
| **Software Failure** | **Process Crash, Resource Leak, or Software Bugs** (e.g., a query using up all available memory/CPU). | Often localized to the node; triggers automatic **Catch-up Recovery** upon restart. |

---

### **Replication**

#### Common Causes

| **Hardware Failure** | **Disk Failure (I/O Errors), Power Supply Unit (PSU) Failure, or Motherboard Failure.** | Requires manual replacement of the physical machine or disk before data can be fully recovered and the node rejoined. |

---

### **Replication**

#### Common Causes

| Category | Reason | Impact |
| :--- | :--- | :--- |
| **Network Outage** | **Network Isolation** (Node cannot communicate with the rest of the cluster, even if its processes are running). | Can lead to **Split Brain** if the isolated node assumes the Primary role; proper **Quorum** is required to prevent this. |

---

### **Replication**

#### Common Causes

| Category | Reason | Impact |
| :--- | :--- | :--- |
| **Resource Exhaustion** 💨 | **Runaway Query** (eats all CPU/RAM), **Disk Full** (cannot accept new writes), or **Too Many Connections**. | Leads to severe performance degradation (**High Latency**) before a full crash. The node is "functionally dead." |

---

### **Replication**

#### Failover

**Failover** is the high-availability process of reacting to a Leader (Primary) failure by detecting the outage
<!-- electing a new Leader from the available Standbys, and promoting it to restore write availability to the system -->

---

### **Replication**

#### Failover: FailPotential Problems

* **Asynchronous Data Loss:** If asynchronous replication is used, the new Leader may not have received all the writes from the old Leader before it failed. This means recently committed data can be permanently lost

* **External System Inconsistency:** Discarding those lost writes is especially dangerous. If an external system (like a payment processor or cache) was coordinated with the lost data, the database and the external system are now permanently out of sync.

---

### **Replication**

#### Failover: Potential Problems

* **Split Brain:** This occurs when two nodes (e.g., the old, isolated Leader and a newly promoted Follower) both believe they are the Leader. They both accept writes, leading to two divergent data histories that are extremely difficult to merge. 

* **Choosing the Right Timeout:** Setting the failure detection timeout is a difficult trade-off:
    * **Too Short:** The system may trigger an unnecessary, "false" failover during a temporary network slowdown, causing instability.
    * **Too Long:** The system takes too long to detect a real failure, resulting in extended write downtime

---

### **Replication**

#### Strategies

| Method | What It Is | Primary Goal | Analogy |
| :--- | :--- | :--- | :--- |
| **1. Batch Replication** | Moving data in large, discrete chunks at intervals. | **Disaster Recovery (DR)** | Periodic data dumps or file system snapshots that are copied to a backup server. |

---

### **Replication**

#### Strategies

| Method | What It Is | Primary Goal | Analogy |
| :--- | :--- | :--- | :--- |
| **2. Streaming Replication** | A continuous, real-time flow of data changes (events). | **High Availability (HA)** | Continuous stream of messages replicating changes as they occur |

---

### **Replication**

#### Strategies

> **Key Distinction:** Batching is periodic and asynchronous *by nature*. Streaming is continuous and forces a choice between **synchronous** (safe) and **asynchronous** (fast).

---

### **Replication**

#### Batch: Base backup (Full Batch)

A complete, physical snapshot of all database files (e..g, the `PGDATA` directory in Postgres). This is the **foundation** for all recovery.

* **Method 1: Cold/Offline (Filesystem Copy)**
    * **Mechanism:** Shut down the database server, then use OS tools (`cp`, `rsync`, or LVM snapshots) to copy the physical data directory.
    * **Trade-off:** Very simple and reliable, but requires **total database downtime**.

---

### **Replication**

#### Batch: Base backup (Full Batch)


* **Method 2: Hot/Online (Tool-based)**
    * **Mechanism:** Use a specialized tool (like `pg_basebackup`) to take a consistent snapshot *while the database is running*.
    * **Trade-off:** The standard for production systems as it requires **zero downtime**.

---

### **Replication**

#### Batch: Incremental Backups (Batched Incrementals)

* **What it is:** Copying the *changes* (the WAL files) in periodic batches.
* **Mechanism:** A separate process copies archived WAL files (e.g., 16MB segments) to backup storage every few minutes.
* **Use Case:** Allows for **Point-in-Time Recovery (PITR)**. You restore the Base Backup, then "replay" these batched WALs to get to a specific time.

---

### **Replication**

#### Streaming: Asynchronous

* **How it works:** The Leader sends the WAL record and **immediately** confirms the write to the client *without* waiting for a response from the Follower.
* **Pros:** Very low write latency; no performance impact on the Leader.
* **Cons:** **Risk of data loss** ($\text{RPO} > 0$). If the Leader fails before sending the write, that data is gone.
* **Use Case:** Most standard workloads, read scaling.

---

### **Replication**

#### Streaming: Semi-synchronous

* **How it works**: The Leader waits for at least one Follower to confirm it has received the data (e.g., written to disk) <!-- If the Follower doesn't respond in time, the Leader can act differently depending on fallback strategy -->
* **Pros**: Higher durability than Async (data is confirmed on 2+ nodes). Lower risk of stalling than full Sync.
* **Cons**: Higher write latency than Async. Can still lose data (RPO>0) if the timeout hits <!-- it can revert to Async mode before the write is sent. -->
* **Use Case**: Workloads needing better data guarantees than Async, but where Leader availability (preventing stalls) is still a top priority.

---

### **Replication**

#### Streaming: Synchronous

* **How it works:** The Leader sends the WAL record and **waits** for all Followers to confirm they have received and saved the data *before* confirming success to the client.
* **Pros:** **Guaranteed zero data loss** ($\text{RPO} \approx 0$) if the Leader fails.
* **Cons:** Higher write latency (at least one network round-trip); risk of stalling writes if the Follower is slow or fails.
* **Use Case:** Financial transactions, critical data integrity.

---

### **Replication**

#### Streaming: Statement-Based Replication

* **Mechanism:** The Leader (Primary) records every `INSERT`, `UPDATE`, `DELETE`, `CREATE TABLE`, etc., statement. These SQL statements are then sent to followers.
* **Follower Action:** Each Follower executes the *exact same SQL statements* that were run on the Leader.

---

### **Replication**

#### Streaming: Statement-Based Replication

**Pros**

||
| :--- |
| **Simple to Implement:** Less data transferred over the network than other methods (only the statement text). |
| **Compact Logs:** Replication logs can be small. |

---

### **Replication**

#### Streaming: Statement-Based Replication

**Cons**

||
| :--- |
| **Non-Deterministic Issues:** Statements involving `NOW()`, `UUID()`, `RAND()` functions or relying on the exact order of `UPDATE` without an `ORDER BY` can produce *different results* on followers. This breaks consistency. |
| **Side Effects:** Statements with side effects (e.g., triggers, stored procedures) can behave differently if the follower's environment isn't identical. |

---

### **Replication**

#### Streaming: Statement-Based Replication

**Cons**

||
| :--- |
| **Write Conflicts:** Difficult to handle concurrent writes in multi-leader setups due to potentially different execution orders. |

---

### **Replication**

#### Streaming: WAL (Write-Ahead Log) Shipping

* **Mechanism:** The Leader (Primary) writes all changes to a durable **Write-Ahead Log (WAL)** *before* applying them to the actual data files. This log contains low-level byte-by-byte descriptions of every change (e.g., "set byte 123 of page 456 in table X to value Y").
* **Follower Action:** Followers receive these WAL records and simply **replay** them onto their own data files, effectively rebuilding the exact state of the Primary.

---
### **Replication**

#### Streaming: WAL (Write-Ahead Log) Shipping

**Pros**

| |
| :--- |
| **Perfect Consistency:** Because it replicates raw changes, it's byte-for-byte identical. No non-deterministic issues. |
| **Robust Recovery:** The WAL is also used for crash recovery on a single node. |
| **Hot Standby:** Enables efficient streaming replication and Hot Standby (read replicas). |

---

### **Replication**

#### Streaming: WAL (Write-Ahead Log) Shipping

**Cons**

||
| :--- |
| **Physical Replication:** Tightly coupled to the database's internal storage format. Difficult to upgrade or replicate |
| **Resource Intensive:** Can transfer a lot of data, especially for large updates <!-- (even a single byte change logs the whole page).--> |
| **Limited Flexibility:** Cannot easily filter or transform data during replication. |

---

### **Replication**

#### Streaming: Logical (Row-Based) Log Replication

* **Mechanism:** The Leader (Primary) extracts changes at a higher, **logical level** (e.g., "row with primary key X was updated, its column Y changed from old_value to new_value"). This log is typically structured.
* **Follower Action:** Followers receive these logical change sets and apply them to their own tables. This can involve matching rows by primary key and applying the specific column changes.

---
### **Replication**

#### Streaming: Logical (Row-Based) Log Replication

**Pros**

||
| :--- |
| **Flexible:** Not tied to the physical storage format. Allows replication between different database versions, or even different database systems <!-- (e.g., Postgres $\to$ MySQL via a CDC tool).--> |
| **Granular:** Can replicate specific tables or even specific columns. <!-- Enables **data filtering** and **transformation**. --> |
| **Reduced Data Transfer:** Can be more efficient than WAL shipping for certain workloads, only logging changed rows/columns. |

---

### **Replication**

#### Streaming: Logical (Row-Based) Log Replication

**Cons**

||
| :--- |
| **Higher Overhead:** Generating logical logs can be more CPU-intensive for the Primary than WAL logging. |
| **Potential for Conflict:** More complex to ensure ordering and handle conflicts in multi-leader scenarios. |
| **Complexity:** Often requires additional tooling (e.g., PostgreSQL's Logical Decoding, Kafka Connect with Debezium). |

---

### **Replication**

#### Streaming: The challange

_Which is the main one ?_ <!-- Replication Lag <=> consistency -->

---

### **Replication**

#### Consistency

> _Consistency_ is a guarantee that defines how and when changes to data become visible to all users or processes in a system"

#### Types

* **Read-your-writes/read-after-write** - a guarantee between writes and reads within a single user.
* **Consistent Prefix Reads** - a user sees causally related data in the correct order
* **Monotonic Reads** - a user never sees time go backward.

---

### **Replication**

#### Consistency: Read-Your-Writes

* **What it is**: A user can always see the result of their own recent writes.

* **Problem it Solves**: It prevents the common "I just submitted my post, but I don't see it on the page!" problem.

* **How it's Implemented**: For a short time after a write, any read requests from that user are routed directly to the leader (or the replica that just confirmed the write), bypassing any lagging read replicas.

---

### **Replication**

#### Consistency: Consistent Prefix Reads


* **What it is**: If a write (B) happens after a write (A), a user reading both writes will see A before B. They will never see B before seeing A.

* **Problem it Solves**: It prevents seeing a reply to a message before the original message has appeared. It ensures a logical, causal flow of information.

* **How it's Implemented**: This is often solved by partitioning, ensuring that writes that belong to the same causal "conversation" (like posts in a single thread) are always routed to the same partition and written in order.

---

### **Replication**

#### Consistency: Monotonic Reads

* **What it is**: Once a user reads a piece of data, any subsequent reads they make will return either the same data or newer data. They will never see an older version (a value they saw in the past).

* **Problem it Solves**: It prevents the scenario where a user refreshes a webpage and a comment they just saw suddenly disappears (because their read request was routed to a more lagging replica).

* **How it's Implemented**: Usually by ensuring a user's session always reads from the same replica, or from replicas that are at least as up-to-date as the one they last queried.

---

### **Replication**

#### Consistency: Conflicts

What happens when **concurrent operations** access the **same piece of data** across **different nodes and timelines**.

---

### **Replication**

#### Consistency: Conflicts: When

* Each leader processes its operations independently. <!-- (write conflicts) -->
* Reads can happen from multiple nodes containing different versions of data. <!-- (read conflicts) -->
* Writes are asynchronously replicated to other leaders. <!-- (write conflicts) -->

---
### **Replication**

#### Consistency: Conflicts: Why

1.  **Causal Order:** It's difficult to determine the true causal order of events when leaders are processing writes in parallel.
2.  **Concurrency:** Concurrent writes on different leaders are often invisible to each other until replication occurs, making real-time prevention impossible.
3.  **Ambiguity:** Without a clear rule, deciding which version is "correct" is ambiguous.

---

### **Replication**

#### Consistency: Conflicts: Types

<!--  most multi-leader replication tools let you write conflict resolution logic using application code -->

* **On Read**: the client sees data that doesn't reflect the system's true, latest state
* **On Write**: clients write to the same portion of data on different nodes simultaneously

---

### **Replication**

#### Consistency: Conflicts: Resolution

A database must **converge towards a consistent state** <!-- Every replication scheme must ensure that the data is eventually the same in all replicas -->

---

### **Replication**

#### Consistency: Convergence: Conflict Detection

| Strategy | Mechanism| How Conflict is Detected
| :--- | :--- | :--- |
| **Last Write Wins (LWW)** | Adds a timestamp or globally unique transaction ID to every write operation or node receiving write operations.| The write or node with the highest timestamp or ID wins |  <!-- This is the simplest but least safe form of detection -->

---


### **Replication**

#### Consistency: Convergence: Conflict Detection

| Strategy | Mechanism| How Conflict is Detected
| :--- | :--- | :--- |
| **Version Vectors** | Each record maintains a map of version numbers for every replica that has written to it | "A write from Replica A conflicts if Replica B's version vector shows it committed a write that Replica A was not aware of | <!-- (i.e., the versions are logically concurrent). -->

---

### **Replication**

#### Consistency: Convergence: Conflict Detection

| Strategy | Mechanism| How Conflict is Detected
| :--- | :--- | :--- |
| **Causal Ordering** | Uses dependencies (e.g., Lamport clock or vector clock) to ensure writes are applied in a strict, causally-related sequence.| If a reply is seen before the original post, it's a causal violation that indicates a conflict or misapplication."

---

### **Replication**

#### Consistency: Convergence: Conflict Resolution

| Strategy | Description |
| :--- | :--- |
| **Automatic Resolution** | [LWW](https://www.linkedin.com/pulse/last-write-wins-database-systems-yeshwanth-n-emc8c/) | <!-- "Fast, but loses data if the earlier write was important. Prone to clock skew issues." -->
| **Merging** | Uses a set of predefined rules (e.g., list append, set union) to combine divergent values. | <!-- "Complex, but preserves the most data. Requires data to be stored in a Conflict-Free Replicated Data Type (CRDT), Mergeable Data Structures <!-- GIT --> or using algorithm like [Operational Transformation](https://www.youtube.com/watch?v=OHd8M54-mNQ)" -->
| **Application-Level** | The system rejects the transaction or marks the record as needing review. | <!-- "Safest, but slow and requires human or application code intervention to fix. Used for critical data (e.g., bank balance)."

---

### **Replication**

#### Consistency: Convergence: Conflict Resolution

| Strategy | Description |
| :--- | :--- |
| **Avoidance (By Design)** | Ensure all writes for a given entity (e.g., all updates to user_id=101) are routed to the same Leader/Partition. | <!-- Best Practice (eliminates the concurrent write possibility), but sacrifices the ability to write to any node. -->

<!-- The **Replication Topology** defines the path and speed of data flow, profoundly impacting *when* and *where* a conflict must be detected and resolved. -->
---

### **Replication**

<!-- Leader/Multi-Leader Replication -->

#### Consistency: Convergence: Replication Topology: Circular <!-- (Ring) --> Topology

**Description**: Replication flows in a single direction, forming a closed loop where each node receives changes from one neighbor and forwards them to the next.

**Trade-off**: Simple to manage but suffers from the slowest convergence time, as changes must traverse the entire ring sequentially. Fault tolerance is low, as a single link failure partitions the entire replication system.

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Star <!-- (Hub-and-Spoke) --> Topology

**Description**: One central node (the Hub) manages all replication traffic. All other nodes (Spokes) send their changes to the Hub, and the Hub is responsible for replicating the authoritative state back out to all Spokes.

**Trade-off**: Offers centralized control for simplified conflict resolution and management. However, the Hub is a single point of failure (SPOF) and an absolute bottleneck for the entire system's write traffic.

---

### **Replication**

#### Consistency: Convergence: Replication Topology: All-to-All <!-- (Full Mesh) --> Topology

**Description**: Every replica is connected directly to every other replica in the cluster. A write on any node is simultaneously sent to all N−1 other nodes in parallel.

**Trade-off**: Provides the fastest possible convergence time and high fault tolerance. However, it generates massive network traffic and dramatically increases the complexity of resolving concurrent write conflicts.


---

<!-- Leaderless Replication -->

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum

What's the conceptual difference ?

<!-- Quorum Replication removes the single point of control (the Leader) and replaces it with a consensus rule across a majority of nodes. -->

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum

**Core Mechanism**: N, W, and R

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum

| Parameter | Definition | What for |
| :--- | :--- | :--- |
| N | Number of total replicas <!-- The total number of nodes storing a copy of the data --> | Defines the cluster capacity |
| W | Write Quorum | The minimum number of replicas that must successfully confirm the write before the coordinator returns ""Success"" to the client.| <!-- Controls Write Latency and RPO -->
| R | Read Quorum | The minimum number of replicas that must be contacted for a read operation | <!-- Controls Read Latency and Staleness. -->

<!-- How about the consitency ? -->
---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum

<!-- Consistency is tunable by configuring read/write nodes -->

| Condition | Resulting Consistency |
| :--- | :--- | :--- |
| **Strong Consistency** | W+R>N (e.g., N=3,W=2,R=2).| <!--Guarantees that the read set (R) and the write set (W) always overlap, ensuring the client retrieves the latest version. --> 
| **Eventual Consistency** | W+R≤N (e.g., N=3,W=1,R=1) | <!-- Prioritizes speed and availability by minimizing the number of nodes required for a successful operation. Reads may return stale data. -->
| **Conflict Handling** | Concurrent writes are inevitable | <!-- Conflicts are detected using Vector Clocks and resolved by the client, application logic, or Last Write Wins (LWW). -->

<!-- What to do when divergence happens ? -->

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum: State Divergence

When a replica node is down or disconnected, it misses write updates, leading to State Divergence.

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum: Read Repair <!-- (Repair on Access) -->

Mechanism: A lazy, pull-based method. When a client reads data, the coordinator checks all R nodes in the quorum, detects any stale versions, and immediately writes the newest version back to the lagging node.

Trade-off:

    Pro: Repairs "hot data" efficiently, using client traffic to drive the fix.

    Con: Stale data persists indefinitely on replicas that are not actively read ("cold data").

---

### **Replication**

#### Consistency: Convergence: Replication Topology: Quorum: Anti-Entropy <!-- (Periodic Background Repair) -->

Mechanism: An active, push-based background process. Nodes periodically compare their entire data set using checksums or Merkle Trees to quickly identify divergent data ranges.

Trade-off:

    Pro: Guarantees that all data (hot and cold) eventually converges.

    Con: Generates significant, constant background network and disk I/O load, increasing operational costs and resource consumption.

---


