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

# **Data Distribtion**

### Why: To overcome single-node limitations.

* Scalability <!-- read/write throughput, data volume, resource limitations-->
* High Availability (HA) <!-- Fault Tolerance -->
* Low Latency <!-- different regions, inbalanced traffic distribution-->

---

# **What is Scalability?**

**A system's ability to handle a growing workload (users, data, or traffic) while maintaining acceptable performance** 

**Criteria**: _how effectively performance metrics change relative to increased load or resources_

### Metrics:

1.  **Compute capacity/Throughput**: Amount of concurrent operations (reads/writes) per second. 
    <!-- Metrics: TPS (Transactions per Second), CPU/RAM utilization --> 
2.  **Storage capacity/Volume**: storage capacity, the performance of the underlying storage.
    <!-- Metics: IOPS - OLTP, Bandwidth - read from or written to the disk, Latency: a time delay a request being issued and the disk starting to respond.-->

---

# **What is Scalability?**

### Metrics:

3.  **Quality of Service** (Latency & Response Time): the increased load causes response times to slow down to unacceptable levels, even if the total throughput is high.
4.  **Efficiency and Cost**: a proportion between the hardware price and efficiency of the hardware
    <!-- Metric: Performance/Cost Ratio or Workload per Core.-->

---

# **What is HA?**

**An system's ability to to remain operational and accessible despite the failure of one or more of its components.**

**Criteria**: _measuring the system's tolerance for failure and its ability to recover quickly without interrupting the user experience._

---

# **What is HA?**

### Metrics:

1.  **The Nines**: percentage of time the system is operational in a given period (usually a year). <!-- 99%:3.65d 99.9%:8.76h -->
2.  **Recovery Metrics**: show how quickly you recover from a failure
    <!-- Recovery Time Object (RTO), Mean Time to Recovery (MTTR)-->
3. **Consistency/Data Integrity**: define maximum acceptable age of data loss from a system failure
    <!-- Recovery Point Objective (RPO) -->

---

# **What is Low Latency?**

**A system's ability to deliver data efficitently with respect to the speed and consistency of responses**

**Criteria**: _ response times remain stable under load and consistently satisfy the application's requirements_

### Metrics

1. **Distribution** - a response time distribution for judging low latency
    <!-- Percetile/Mean -->
2. **Stability** - ability to maintain its speed even as the total load increases
    <!-- Contention - num of users can block or queue the access to resource -> spikes -->
---

# Approaches

### Two Ways to Scale

| Type of Scaling | How It Works | Implications |
| :--- | :--- | :--- |
| **Vertical Scaling** (Shared-Memory Approach) | Adding more **CPU, RAM, or disk** to a *single* server. | A shared-memory approach is easy to implement in exchange to the cost grows faster than linearly |

---

### Two Ways to Scale

| Type of Scaling | How It Works | The CPU/RAM Connection |
| :--- | :--- | :--- |
| **Horizontal Scaling** (Shared-Nothing Approach) | Adding more **servers (nodes)** to distribute the load across a cluster. |  Each node uses its CPUs, RAM, and disks independently. Coordination
between nodes is done at the software level increasing the complexity and network overhead. |

---

# Replication vs Partitioning

Replication vs. Partitioning (Sharding)

**Replication** and **Partitioning** are the two main strategies to scale data-intensive systems **to solve different core problems**.

---


### **Replication**


| Criterion | Function | Primary Benefit |
| :--- | :--- | :--- |
| **Data Copy** | Full, identical copies of the same data across multiple nodes. | **Redundancy** (High Availability). If one node fails, others take over. |
| **Scales** | Read throughput (Horizontal Scaling). | **Latency:** Read queries can be distributed to all replicas, lowering contention. |

---

### **Partitioning / Sharding (Capacity & Write Load)**

| Criterion | Function | Primary Benefit |
| :--- | :--- | :--- |
| **Data Copy** | Unique subsets of data are stored on different nodes (e.g., users A-M on Node 1, N-Z on Node 2). | **Capacity:** Total storage capacity becomes the sum of all nodes. |
| **Scales** | Write throughput and total storage (Horizontal Scaling). | **Throughput:** Write queries are isolated to a single shard, reducing I/O contention. |

---

### **Complexity**

| Approach | Replication | Partitioning |
| :--- | :--- | :--- |
| **Replication** | Consistency management (synchronous vs. asynchronous). | **No Change** to application logic (data is all in one logical place). |
| **Partition/Sharding** | Routing queries, managing re-sharding, distributed transactions. | **Application Logic** must be aware of the partitioning scheme. |

---

## In Summary

Data distribution is the architectural strategy that enables modern applications to handle:

- Massive user bases
- Enormous data volumes
- Stringent availability requirements

It's the foundation for building systems that are impossible to achieve with a single-server approach.