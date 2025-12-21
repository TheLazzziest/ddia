---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
marp: true
---

## Welcome

![bg right](../assets/ddia.png)

---

### **Partitioning**

**Partitioning** - breaking data up into physically small chunks of data.

**When do we need this ? What is the reason ?**

<!-- Large Datasets/High throughput. Scalability -->

---

### **Partitioning: Terminology**

Different systems use different names for what is essentially the same concept: a partition. This can be a source of confusion.

- **Shard**: MongoDB, Elasticsearch, SolrCloud
- **Region**: HBase
- **Tablet**: Bigtable
- **vnode**: Cassandra, Riak, Scylla
- **vBucket**: Couchbase

**Partition** - the most generally accepted term.

---

### **Partitioning: Goal**

**To distribute** data and query load as evenly as possible across the available nodes.

**Distribution** - employing different partition keys to point records to different nodes.

---

### **Partitioning: Evaluation**

- **Load Distribution** <!-- Eveneness --> - prove the partitioning key successfully avoids "hot spots" by spreading activity evenly across all nodes
- **Query Performance** <!-- Effectiveness --> - confirm that dividing the data has actually improved performance
- **Operational overhead** <!-- Complexity --> - measure the complexity and reliability of managing the partitioned system

**Which metrics can describe each of these factors?**

---

### **Partitioning: Evaluation: Load Distribution**

| Metric            | Description                                                                                      | Goal                  | Why it Matters                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------ | --------------------- | ---------------------------------------------------------------------------------------- |
| **Data Skew (σ)** | The difference in data size (GB or record count) between the largest partition and the smallest. | Keep σ close to zero. | High skew leads to "hot shards" that run out of space or have disproportionate I/O load. |

---

### **Partitioning: Evaluation: Load Distribution**

| Metric           | Description                                                                                   | Goal                                   | Why it Matters                                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Request Skew** | The difference in query volume (QPS) directed at the busiest partition versus the least busy. | Keep request skew low (<20% variance). | Measures the effectiveness of the partitioning key in handling traffic; the busiest partition is the system's bottleneck. |

---

### **Partitioning: Evaluation: Load Distribution**

| Metric                         | Description                                                                                            | Goal                                             | Why it Matters                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| **Cross-Partition Query Rate** | The percentage of queries that require accessing more than one partition (e.g., a JOIN across shards). | Keep this rate as low as possible (ideally <5%). | Multi-shard queries are slow, complex, and negate the performance gain of partitioning. |

---

### **Partitioning: Evaluation: Query Performance**

| Metric            | Description                                                                        | Goal                                                       | Why it Matters                                                                                   |
| ----------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Latency (p99)** | The time taken to execute queries that access only one partition (the target key). | Must be significantly lower than pre-partitioning latency. | Confirms that the smaller index size and reduced volume per node are improving read/write speed. |

---

### **Partitioning: Evaluation: Query Performance**

| Metric                     | Description                                                                    | Goal                                                   | Why it Matters                                                                                                                        |
| -------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Write Throughput (TPS)** | The total number of transactions the system can process across all partitions. | Must scale linearly with the number of partitions (N). | If doubling partitions (N→2N) does not roughly double TPS, there is an underlying bottleneck in the networking or coordination layer. |

---

### **Partitioning: Evaluation: Query Performance**

| Metric                       | Description                                                             | Goal                                                  | Why it Matters                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Index Size Per Partition** | The actual physical size of the B-tree or index structure on each node. | Keep this small enough to fit into RAM (for caching). | "Smaller indexes reduce disk I/O, which is the single largest performance gain from partitioning." |

---

### **Partitioning: Evaluation: Operational overhead**

| Metric              | Description                                                                       | Goal                                                      | Why it Matters                                                                                                    |
| ------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Resharding Time** | The time required to add a new partition or redistribute data across the cluster. | Must be predictable and low (ideally near-zero downtime). | High efficiency requires the ability to quickly rebalance the cluster when data or request skew becomes too high. |

---

### **Partitioning: Evaluation: Operational overhead**

| Metric             | Description                                                                                    | Goal                                              | Why it Matters                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Cost Per Query** | "The cumulative cost (CPU, I/O, network) across all nodes required to execute a single query." | Minimize the cost multiplier for complex queries. | Ensures that horizontal scaling remains cost-effective compared to simply scaling up one massive machine. |

---

### **Partitioning: Strategies**

Main factors that determine a system's efficiency:

- **Distribution** - How evenly data and query load are spread across partitions. <!-- The goal is to utilize all nodes equally, preventing any single node from becoming a bottleneck. -->
- **Skewness** - The measure of how unevenly data is distributed. <!-- High skew leads to "hot spots," where some partitions receive a disproportionate amount of load, degrading performance and capacity. -->
- **Locality** - The principle of keeping related data together on the same partition <!-- High locality is crucial for efficient range queries, as it allows a query to be answered by a single node, minimizing network overhead and latency. -->

---

### **Partitioning: Strategies: Hashing**

<!-- Modulo Hashing, Consistent Hashing, Rendezvous Hashing (HRW) -->

| Aspect                      | Description                                                                                                 |
| --------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Mechanism**               | Applies a hash function to the key (e.g., `user_id % N`) to determine the partition bucket.                 |
| **Distribution Uniformity** | High <!-- Near-perfect mathematical uniformity. -->                                                         |
| **Skewness Risk**           | Low. <!-- Distributes heavy users across all nodes, minimizing hotspots. -->                                |
| **Query Locality**          | Low. <!-- Queries for sequential keys (ranges) are spread across all partitions, requiring a full scan. --> |
| **Best Use Cases**          | Distributing massive, arbitrary data (e.g., user profiles) to ensure even load.                             |

---

### **Partitioning: Strategies: Random**

<!-- High-Entropy Hashed Key, UUID -->

| Aspect                      | Description                                                                                                                   |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Mechanism**               | use a random number or a high-entropy key (like a UUID) to determine the bucket <!-- effectively spreading data randomly. --> |
| **Distribution Uniformity** | Highest <!-- Guarantees maximal spread -->                                                                                    |
| **Skewness Risk**           | Lowest <!-- Inherently prevents any hot spot based on data content -->                                                        |
| **Query Locality**          | Lowest. Zero query locality. <!-- Requires index lookups across all partitions to find any range of data. -->                 |
| **Best Use Cases**          | Distributed logging systems or data ingestion pipelines where sequence and range queries are irrelevant.                      |

---

### **Partitioning: Strategies: Range**

<!-- Physical Range Partitioning, Logical Range Partitioning, -->

| Aspect                      | Description                                                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Mechanism**               | use a contiguous range of key values (e.g., date ranges, alphabet ranges).                                                  |
| **Distribution Uniformity** | Low. <!-- Highly dependent on data being uniformly spread in real-time. -->                                                 |
| **Skewness Risk**           | High. <!-- Very susceptible to hot spots (e.g., today's date or a popular user segment). -->                                |
| **Query Locality**          | High. <!-- All related range queries (e.g., last 30 days of data) are isolated to a single partition, making them fast. --> |
| **Best Use Cases**          | Time-series data, archival, and large tables where range deletes are frequent.                                              |

---

### **Partitioning: Strategies: List**

<!-- Static List Partitioning, Default List Partitioning, Logical List Partitioning, -->

| Aspect                      | Description                                                                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Mechanism**               | an explicit list of acceptable key values (e.g., `state = 'CA', 'TX', 'NY'`).                                                         |
| **Distribution Uniformity** | Medium. <!-- Depends entirely on the administrator's prior knowledge of the source data volumes. -->                                  |
| **Skewness Risk**           | High. <!-- If one list value (e.g., a specific product category) contains 50% of the data, that partition becomes the bottleneck. --> |
| **Query Locality**          | High. <!-- Queries for a specific known category are isolated to one partition. -->                                                   |
| **Best Use Cases**          | Categorical data, compliance boundaries (data must live in a specific geography).                                                     |

---

### **Partitioning: Strategies: Composite**

<!-- Range-Hash Composite Partitioning, List-Hash Composite Partitioning (Categorical Distribution), List-Range Composite Partitioning (Categorical Archival)-->

| Aspect                      | Description                                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Mechanism**               | Combines two strategies (e.g., Range → Hash) to subdivide partitions hierarchically.                                            |
| **Distribution Uniformity** | High <!-- Excellent uniformity within the primary range -->                                                                     |
| **Skewness Risk**           | Medium/Low <!-- Reduces the risk of a single overwhelming hot spot by hashing the range. -->                                    |
| **Query Locality**          | Medium/High <!-- Range queries are isolated first, and then point queries are efficiently handled by the secondary hash -->     |
| **Best Use Cases**          | Large-scale, transactional tables that need both efficient range queries and uniform distribution (e.g., large logging tables). |

---

### **Partitioning: Strategies: Directory Based**

<!--Relational Database Lookup Table, Distributed Consensus Service, Client-Side Metadata Cache -->

| Aspect                      | Description                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Mechanism**               | queries the directory (a central lookup service) first, then the data based on the key <!-- for the physical network address -->           |
| **Distribution Uniformity** | Medium <!-- Depends entirely on the uniformity of the underlying partitioning scheme (usually Hash or Range). -->                          |
| **Skewness Risk**           | Medium <!-- Routing Bottleneck: becomes a high-demand point => SPOF or latency bottleneck for every single query. -->                      |
| **Query Locality**          | High <!-- Point Lookups: query itself is local to one partition, but every read/write requires use two network hops (Directory → Data) --> |
| **Best Use Cases**          | Systems requiring flexible resharding and seamless data migration that must be achieved without changing the application's configuration.  |

---

### **Partitioning: Strategies**

What if we strugle or fail to achieve a solid partitioning strategy from a get-go ?

---

### **Partitioning: Rebalancing**

When a partitioning strategy (like Hash or Range) fails to maintain a balanced workload, the operational response is **Rebalancing** (Resharding).

---

### **Partitioning: Rebalancing: Static**

This applies to fixed, non-elastic partitioning schemes (like Modulo N), which are difficult to change.

- **Mechanism**: When scaling up (N→N+1), the system recalculates the partition ID for almost every key in the database based on the new modulus.

- **The Problem**: The entire dataset must be physically moved because the formula changes for nearly all existing data.

- **Impact**: This process is extremely brittle and requires significant downtime. It is avoided in highly available production environments because it's too slow to run online.

---

### **Partitioning: Rebalancing: Shifting**

This is the standard approach for large, complex systems that need to maintain zero downtime while migrating data from one partition to a new one.

- **Mechanism**: The rebalancing is performed iteratively through three phases:

  - **Dual Writes**: New data is written to both the old partition and the new partition.

  - **Backfill**: A background process copies all historical data from the old partition to the new one.

  - **Atomic Cutover**: The routing layer is instantly switched to point all traffic to the new partition.

---

### **Partitioning: Rebalancing: Shifting**

- **Impact**: Achieves zero downtime for the application, but it is operationally complex. The extra load from Dual Writes and Backfilling consumes resources and requires careful consistency management.

---

### **Partitioning: Rebalancing: Consistent Hashing**

This method is the structural solution to the limitations of static hashing, enabling online elasticity.

- **Mechanism**: The database uses a Consistent Hashing algorithm to map both data keys and nodes onto an abstract ring.

- **The Fix**: When a new node is added, it is placed on the ring and only receives the small fraction of data keys whose hash position falls between the new node and its clockwise neighbor.

- **Impact**: Only a fraction (≈1/N) of the data needs to be moved when scaling up or down. This makes rebalancing online, highly efficient, and transparent to the application. This is the preferred strategy for systems requiring high elasticity.

---

### **Partitioning: Rebalancing**

**How run queries on partitioned and/or rebalanced data?**

---

### **Partitioning: Querying**

**Goal** - to minimize the amount of data the database has to scan

---

### **Partitioning: Querying: Why**

**Maximizing Query Locality**

To run queries faster by forcing them to look in fewer places.

- **Partition Pruning**: A query engine analyzes the WHERE clause and eliminate (prune) all partitions that could not possibly contain the data

- **Reduced I/O**: By accessing only one or a few partitions, the system dramatically reduces the amount of disk I/O and data scanned.

---

### **Partitioning: Querying: Why**

**Improving Throughput and Latency**

To handle concurrent high load and provide a predictable performance.

- **Increased Write Throughput** Partitioning allows to scale horizontally avoiding cluster-wide contention.

- **Stable Latency (p99)** partitioning prevents a slow query on one partition from impacting transactions on others

- **Load Distribution** partitioning prevents any single node from becoming a CPU or I/O bottleneck.

---

### **Partitioning: Querying: Why**

**Maintaining Availability**

To simplify administrative benefits of using partitioned data structures.

- **Fault Isolation**: The failure of one partition only affects the subset of data on that partition

- **Efficient Maintenance**: dropping the entire partition is much faster and simpler, than performing an expensive, locking DELETE statement.

---

### **Partitioning: Querying: Challenge**

To ensure the query router can reliably and quickly find the correct partition for any given query. 

<!-- This becomes complex because the routing metadata must remain consistent and accurate even as data is moved during rebalancing, without adding significant latency to every request. -->

---

### **Partitioning: Querying: Strategies**

* **Centralized Coordination** - uses a dedicated external service (the coordinator) to store the entire partition map.
* **Decentralized Coordination** - distribute the entire partition map across all data nodes in order to sync a cluster state.
* **Client-Side Routing** - placing the entire partition map within the client application itself.

---

### **Partitioning: Querying: Centralized Coordination**


* **Mechanism**: Uses a highly available, external cluster (like ZooKeeper or etcd) to store metadata mapping key ranges to specific server addresses. This is your "external service coordinator."

* **Routing Flow**:
```mermaid
flowchart LR
    Client --> ​Coordinator
    Coordinator --> ​DataNode
```

---

### **Partitioning: Querying: Centralized Coordination**


* **Pros**: 
  * **Easy to manage**. 
  * **Failover is simple**: the coordinator updates the central map, and all routers instantly see the change.

* **Cons**: 
  * **N+1 Problem**: Two network hops are required for every query. 
  * **SPOF**: The coordinator cluster becomes a central bottleneck for routing integrity.

* **Example Use**: CockroachDB (uses Raft consensus internally for its range metadata).

---

### **Partitioning: Querying: Decentralized Coordination**

* **Mechanism**: Uses a gossip protocol (like those found in Cassandra and Riak) to share cluster state and partition ownership changes peer-to-peer. Every node eventually knows the entire map.
* **Routing Flow**:
```mermaid
flowchart LR
    Client --> ​Data Node (Local or Redirect)
    Data Node --> ​Coordinator
```

---

### **Partitioning: Querying: Decentralized Coordination**

* **Pros**: 
  * **High Availability (HA)**. 
  * **No SPOF**. <!-- The cluster can tolerate high node failure rates. Excellent for horizontal scaling. -->

* **Cons**: 
  * **Eventual Consistency**. The map takes time to propagate via gossip. <!-- A client might be routed to a node that has stale map data, requiring a redirect or a retry. -->

* **Example Use**: Apache Cassandra (which uses **Hinted Handoff** and **Quorum** checks to ensure writes are eventually durable).

---

### **Partitioning: Querying: Decentrailized Coordination: Raft vs Gossip**

* **Raft** <!-- Strong Consistency -->: is a consensus algorithm designed for replicated state machines.
* **Gossip** <!-- Eventual Consistency -->: is a distributed protocol designed for information dissemination in distributed systems.

[Read More](https://medium.com/@dhanyakrishnan8109/raft-vs-gossip-protocol-2c109fcd00f2)

---

### **Partitioning: Querying: Client-Side Routing**

* **Mechanism**: The client driver downloads a copy of the partition map metadata on startup. The client calculates the key-to-shard mapping locally.
* Routing Flow:
```mermaid
flowchart LR
    Client (with Map) --> ​Data Node (Shard)
```

---

### **Partitioning: Querying: Client-Side Routing**

* **Pros**: 
  * **Single Network Hop**. <!-- Fastest possible routing for point queries, as the lookup latency is absorbed by the client's local memory. -->

* **Cons**: 
  * **Stale Routing Risk**. If a node fails or a partition is moved (resharding), the client's cached map becomes outdated. 
<!-- The client receives an error on the first attempt and must then refresh its map by asking the cluster for the latest topology. -->

* **Example Use**: Apache Kafka clients, modern RDBMS sharding proxies, and certain proprietary NoSQL drivers.

---

### **Partitioning: Execution**

**Goal** - maximize the efficiency and performance of the entire query operation across a distributed system.

---

### **Partitioning: Execution: Query Routing**

| Aspect           | Description                                                                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Requirements** | Required for high-throughput, low-latency transactional workloads where queries are designed to look up data by its primary partitioning key.                                                     |
| **Mechanism**    | The application or query router examines the `WHERE` clause to identify the partitioning key value (e.g., `WHERE user_id = 123`) and uses the partition map to find the exact physical partition. |

---

### **Partitioning: Execution: Query Routing**

| Aspect            | Description                                                                                                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Efficiency**    | This is an O(1) or O(log N) operation (where N is the number of partitions), resulting in the lowest latency and highest throughput. <!-- The query is sent to only one machine. --> |
| **Best Used For** | Point lookups (`SELECT * WHERE id = X`) or small range lookups that fit entirely within one partition (e.g., `SELECT * WHERE date BETWEEN Y AND Z` if partitioned by date).          |

---

### **Paritioning: Execution: Scatter-Gather**

| Aspect            | Description                                                                                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Requirements**  | a query cannot be fulfilled by a single partition, usually because the query does not include the partitioning key or spans multiple key ranges                                             |
| **Mechanism**     | The router sends the query to all partitions simultaneously. Each partition executes it locally, and the router gathers, merges, and sorts the results before returning them to the client. |

---

### **Paritioning: Execution: Scatter-Gather**

| Aspect            | Description                                                                                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|
| **Efficiency**    | Low. Latency is determined by the slowest partition, and network/CPU overhead for gathering results is high. This approach does not scale well with the number of partitions.               |
| **Best Used For** | Analytical queries or queries that cannot use the partitioning key, requiring a full scan of the dataset. To be avoided for high-throughput transactional workloads.                        |



### **Paritioning: Execution: Broadcast and Join**

| Aspect          | Description                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Requirements**  | Required when joining data that resides on different partitions. It is the most complex and least efficient strategy.                                                                                |
| **Mechanism**     | Involves either broadcasting a small table to all partitions or exchanging/shuffling data between partitions based on the join key for large-to-large table joins.                                    |

---

### **Paritioning: Execution: Broadcast and Join**

| Aspect          | Description                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Efficiency**    | Introduces significant network latency and CPU overhead. This operation negates most benefits of partitioning and should be avoided for high-volume transactions.                                     |
| **Best Used For** | Analytical workloads (OLAP) where latency is tolerable, and the goal is to process massive datasets.                                                                                               |
---

### **Paritioning: Execution: Partition Pruning (Range Optimization)**

| Aspect          | Description                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Requirements**  | This is a specialized optimization that applies only to Range and List partitioned data.                                                                                                             |
| **Mechanism**     | The query executor analyzes the `WHERE` clause before execution and uses the known boundaries of the partitions to eliminate (prune) unnecessary partitions from the scan list.                       |

---

### **Paritioning: Execution: Partition Pruning (Range Optimization)** 

| Aspect          | Description                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|
| **Efficiency**    | Reduces the scatter-gather overhead by only querying the relevant subset of partitions.                                                                                                              |
| **Best Used For** | Time-series databases partitioned by date. A query for data in March 2025 will only hit the partition covering March 1-31, 2025, even if the cluster has 100 other partitions.                        |

---

### **Partitioning: Routing vs. Execution**

| Routing Approach        | Best for Execution Strategy                                                                      | Worst for Execution Strategy                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| **Centralized/Client-Side** | Query Routing <!-- (Single Partition) --> and Partition Pruning <!-- (Fast lookup to eliminate servers). -->                 | Broadcast and Join <!-- The central router struggles to manage massive data transfers -->        |

---

### **Partitioning: Routing vs. Execution**

| Routing Approach        | Best for Execution Strategy                                                                      | Worst for Execution Strategy                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| **Decentralized (Gossip)**  | Scatter-Gather <!-- Highly resilient—if one node fails, the gather still proceeds with the remaining nodes --> | Query Routing <!-- Prone to stale reads, as the route might point to an old version of the partition map --> |

---

### **Partitioning**

**How** to implement the execution strategies mentioned above ?

---

### **Partitioning: Parallelization**
<!-- Recall shared-nothing architecture -->

**MPP** - a database architecture where a computation is divided into many sub-problems, each executed simultaneously by independent processors and memory units.

**Goal** - to achieve near-linear scalability for complex analytical workloads (OLAP).

---

### **Partitioning: MPP: Why**

To eliminate the contention and resource limits inherent in single-server or shared-memory architectures, allowing the system to handle petabytes of data.

---

### **Partitioning: MPP: Principles**

* **Shared-Nothing Architecture** - eliminates resource contention
* **Horizontal Workload Parallelization** - enables the system to drastically reduce the time taken for complex analytical computations
* **Decoupling from Persistent Storage** - ability to instantly scale compute up or down based on query load
* **Optimization for Query Speed** - processing petabytes of data as quickly as possible

---

### **Partitioning: MPP: Types**

* **Stateless** - system does not retain data in memory between successive queries.
* **Stateful** - must retain and manage internal data <!-- (e.g., current window sums, aggregations, user session status) --> across multiple steps and processing windows for correctness and fault tolerance.

---

### **Partitioning: MPP: Stateless**

* **Cloud-Native Platforms**:
  * **[Snowflake](https://www.snowflake.com/en/)**
  * **[Google BigQuery](https://cloud.google.com/bigquery)**
  * **[Amazon Redshift](https://aws.amazon.com/redshift/)**

* **Distributed Query Engines**

  * **[Trino](https://trino.io/)**
  * **[StarRocks](https://www.starrocks.com/)**
  * **[AWS Athena](https://aws.amazon.com/athena/)**

---

### **Partitioning: MPP: Stateful**

* **Distributed Execution Engines**
  * **[Apache Spark](https://spark.apache.org/)**
  * **[Apache Storm](https://storm.apache.org/)**

* **Distributed Streaming Databases**
  * **[ksqlDB](https://ksqldb.io/)**
  * **[Materialize](https://materialize.com/)**
  * **[Apache Flink](https://flink.apache.org/)**
  * **[RaisingWave](https://risingwave.com/)**
