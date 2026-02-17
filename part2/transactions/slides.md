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

### Transactions

Why do we need them ? <!-- Guarantee data consistency -->

---

### Transactions

What is a transaction ? <!-- A set of operations that are executed as a single unit of work -->

---

### Transactions: Implications

Either all operations succeed <!-- commit --> or none of them do <!-- rollback -->.

---

### Transactions: Implications: Why

What is the purpose of a transaction ? <!-- No partial changes -> Simplify programming model for concurrent access -->

---

### Transactions: ACID 

What is ACID ?
<!--
- Atomicity: Either all operations succeed or none of them do
- Consistency: Transactions ensure that the database remains in a consistent state.
- Isolation: Transactions are isolated from each other, preventing interference.
- Durability: Once a transaction is committed, its changes are permanent.
-->

---

### Transactions: ACID: Atomicity

When it applies ? <!-- In case of failure in the middle of a transaction -->
What is the goal ? <!-- State enforcement: either previous or the next one -->

---

### Transactions: ACID: Consistency

When it applies ? <!-- When data integrity of business data is critical -->
What is the goal ? <!-- Preserve data invariants which must comply with business rules -->

---

### Transactions: ACID: Isolation

When it applies ? <!-- When concurrent access to the very same piece of data is required -->
What is the goal ? <!-- To ensure that transactions do not interfere with each other to some degree -->

---

### Transactions: ACID: Durability

When it applies ? <!-- When data storage is critical -->
What is the goal ? <!-- To ensure that committed transactions are not lost or corrupted by system failures, power outages, or other unexpected events -->

---

### Transactions: Theory vs Practice

We defined the rules (ACID).

**How do storage engines actually implement them?**

### Transactions: ACID: Persistence

When it comes to persistance data structures: LSM-Tree vs B+Tree; how ACID is achieved ? What are the trade-offs between the two?
<!--
Both Writes to the WAL, then:
* modifies a page in memory.
* adds to the MemTable.

- LSM-Tree: Consistency is achieved through the use of a write-ahead log (WAL) and a compaction process. Isolation is achieved through the use of a snapshot isolation level.

- B+Tree: Consistency is achieved through the use of a locking mechanism. Isolation is achieved through the use of a multi-version concurrency control (MVCC) mechanism.
-->

---

### Transactions: ACID: Persistence: Atomicity

* **B+Tree**: Uses Page Shadowing or Undo Logs. When a page split happens, the database ensures the "old" version is safe until the "new" version is fully linked.

* **LSM-Tree**: Naturally atomic at the Batch level. Because you write to a memory buffer (MemTable) and flush it as a single file, the write either exists in the new file or it doesn't.

---

### Transactions: ACID: Persistence: Consistency

* **B+Tree**: Immediate enforcement. <!-- Since there is only one physical location for a row, the database can instantly check if a UNIQUE constraint is violated by looking at one specific leaf. -->

* **LSM-Tree**: Delayed/Read-time enforcement. <!-- Because many versions of a row can exist in different levels, the database must "resolve" the truth during a read (picking the latest timestamp). Strict constraints (like Foreign Keys) are harder/slower to enforce. -->

---

### Transactions: ACID: Persistence: Isolation

* **B+Tree**: Relies on Locks and Latches. <!-- To change a row, you must lock the physical page it lives on. This prevents others from seeing a "half-written" row but causes waiting (contention). -->

* **LSM-Tree**: Uses MVCC (Multi-Version Concurrency Control) by design. Since you never overwrite, a "Reader" simply looks at a snapshot of files from a specific timestamp while "Writers" create brand-new files. They never touch the same physical data.

---

### Transactions: ACID: Persistence: Durability

**Both: Use a WAL. <!-- A write is only "committed" once it hits the sequential log on the disk. Even if the MemTable (LSM) or Buffer Pool (B+Tree) is lost in a crash, the log replays the data. -->

---

### Transactions: ACID: Persistence: Recap

Why B+Tree is better in ensuring stronger consistency guarantees ?
<!--
It updates "in-place," there is only ever one "truth" for a specific row on the disk enforcing constraints quite efficiently.
-->
What is the downside of using B+Tree where LSM-Tree just excels ?
<!--
B+Tree always keeps the same data at the exact same location on disk, which can lead to fragmentation and slower performance. This is where LSM-Tree offers better solution by appending new chunks to MemTable followed by flushing to SSTable upon fill factor in append-only mode. So convergence happened in the background upon compaction stage. This is better suited for write-heavy workloads because it can handle a large number of writes efficiently. It also has a simpler data structure and is easier to implement than B+Tree.
-->
What workload isolation implications do they impose ?
<!--
B+Tree provides better capabilities because the object address is fixed in terms of pages which can be locked upon access to proper isolation, but it leads to operation contention. 

LSM-Tree, on the other hand, are inherently lock-free due to their append-only nature and the use of compaction in the background in most implementations. However, to achive consistency, many of them use conflict resolution based on Timestamps, so the latest version wins always.
-->

---

### Transactions: Concurrency

We know how to store data safely.

**But what happens when everyone tries to touch it at the same time?**

---

### Transactions: Isolation Levels

What is isolation ? 
<!-- Isolation is a property of a database transaction that ensures that concurrent transactions do not interfere with each other. -->

What are the isolation levels in a database transaction ?
<!--
Isolation levels are a set of rules that define how transactions interact with each other. There are four isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable. Each level provides a different level of isolation, with Read Uncommitted providing the least isolation and Serializable providing the most isolation.
-->

What are the implications of isolation levels on consistency ?
<!--
Isolation levels gives you a trade-off between performance and consistency. For example, 
* Read Uncommitted can lead to dirty reads, which can cause data inconsistencies and errors, but improves performance as both transactions can read uncommitted data.
* Read Committed can prevent dirty reads but can also lead to phantom reads, penalizing performance of concurrent transactions.
* Repeatable Read can prevent both dirty reads and phantom reads but can also lead to serialization anomalies. 
* Serializable can prevent all of these issues but can also lead to significant performance degradation.
-->

---

### Transactions: Isolation Levels: Locking

Is Serializable level used in practice ? How does it differ from locking ? When is it used ?

<!--

Serializable isolation level is used in production. Cases:
* Financial & Banking (The Core Ledger)
* Inventory & Booking (The "Oversell" Problem)
* Medical & Safety Systems (The "Write Skew" Classic)

Locking vs Serializable Isolation:
* **Manual Locking** (Pessimistic Concurrency Control): prevents anomalies by physically blocking access to specific resources (rows, pages, or tables) using commands like SELECT ... FOR UPDATE

* **Serializable Isolation** (Highest Level of ANSI Isolation): provides a logical guarantee by ensuring that the execution of any concurrent set of transactions is equivalent to some serial (one-by-one) execution. 

-->

---

### Transactions: Isolation Levels: Read Committed

What guarantees does Read Committed isolation level provide?
<!--
* transactions see only committed pieces of data
* only committed data is overwritten by newer transactions
-->

What side effects does Read Commited prevent ?
<!--
* Prevents dirty reads/writes
* Prevents non-repeatable reads
-->

What side effects does Read Commited allow ?
<!--
* Allows phantom reads
* Allows read skew
-->

---

### Transactions: Isolation Levels

Why read skew can become a problem ?
<!--
* Read skew occurs when two transactions read the same data at different times, but the data has changed between the reads.
* This can lead to inconsistent results and incorrect decisions.
-->

What is the common solution to this problem ?
<!--
Snapshot isolation (SSI) is a common solution to this problem. It ensures that each transaction sees a consistent snapshot of the database at the start of the transaction, and any changes made by other transactions are not visible until the transaction commits.
-->

---

### Transactions: Isolation Levels: SI

Snapshot isolation (SSI) is a technique to provide a consistent snapshot of the database at the start of each transaction.

**Principle** - readers never block writers and vice versa

---

### Transactions: Isolation Levels: Gotcha

What side effect does Snapshot Isolation allow ? Why ?

<!--
Allows write skew - it's not serializable allowing race conditions
-->

---

### Transactions: Isolation Levels: Repeatable Read

What guarantees does Repeatable Read isolation level provide?
<!-- 
* implies READ COMMITTED guarantees
* read data is immutable within a transaction
-->

What side effects does Repeatable Read isolation level allow?
<!-- 
* lost update - two concurrent transactions do read-modify-write cycles on the same row, leading to a lost update
-->

---

### Transactions: Isolation Levels: Countermeasures

**Cursor Stability** isolation level guarantees that the data read by a transaction remains consistent throughout its execution. Ensures that each transaction reads the most recent committed version of the data, and locks only the row that it is currently updating.

**Cursor Stability is a typical isolation level in non-MVCC databases**

Which side effects does Cursor Stability isolation level allow?
<!-- 
* phantom reads - a transaction reads a row that was inserted by another transaction after the first transaction started
-->

---

### Transactions: Isolation Levels: Countermeasures

**Explicit Locking** isolation level allows transactions to explicitly acquire locks on resources they need to modify. This ensures that no other transaction can modify the same resource until the lock is released.

**Explicit Locking** requires manual management of locks, which can lead to deadlocks if not handled properly.

---

### Transactions: Isolation Levels: Countermeasures

**Serializable** isolation level guarantees that transactions are executed in a way that is equivalent to a single transaction. This ensures that no two transactions can interfere with each other.

**Serializable** isolation level requires that all transactions are executed in a serial order, which can lead to performance issues.

---

### Transactions: Isolation Levels: Distributed Environment

Why ACID doesn't work (or partially work) in a distributed environment ? 
<!-- 
* Network partitions - a network partition can cause transactions to be split across multiple nodes, leading to inconsistencies
* Time drift - Clock synchronization is required to ensure that transactions are executed in a consistent order across all nodes.
-->

---

### Transactions: Isolation Levels: Write skew

**Write skew** occurs when two transactions read the same data, each transaction modifies the data, and then commits. The result is that the data is modified in a way that is not consistent with the original data.

**Write skew** can be prevented by using **Serializable** isolation level.

---

### Transactions: Isolation Levels: Phantoms

**Phantom Read** occurs when a transaction (T1) retrieves a set of rows based on a search condition, but a concurrent transaction (T2) inserts or deletes rows that match that condition and commits.

**Phanton** reads can be prevented by using **Serializable** isolation level.

---

### Transactions: Isolation Levels: Lost Updates

**Lost Updates** occur when two transactions read the same data, each transaction modifies the data, and then commits. The result is that the data is modified in a way that is not consistent with the original data.

**Lost Updates** can be prevented by using **Serializable** isolation level.

---

### Transactions: Isolation Levels: Serializable

**Serializable** isolation level ensures that transactions are executed in a serial order.

When is **Serializable** isolation level used?
<!--
Serializable isolation level is used when the application requires that all transactions are executed in a serial order to minimize the overhead of serializing transactions.
-->

How is the workload managed? Why can it work ?
<!--
Serialized transactions are processed by a single CPU, which ensures that transactions are executed in a serial order.

The reason behind this efficiency is there is no need in managing synchronization overhead among transactions.
-->

What are the constraints for its application ?
<!--
To achieve a comparable performance, the workload must share the following properties:
* Transactions are short-lived.
* Transactions are not nested.
* Transactions are not write-heavy.
* Transactions do not have side effects.
* Transactions should be partitioned (or have the least amount of intersections with other partitions in terms of other transactions).
-->

---

### Transactions: Isolation Levels: Stored Procedures

Why not to cover statements in a single block instead of Serializable isolation level ? Will it solve the isolation problem ?

<!--
Stored Procedures are logical units of work rather a single statement where isolation level is enforced.
-->

---

### Transactions: Isolation Levels: Stored Procedures

**Stored Procedures** are a set of SQL statements that are stored in the database and can be executed as a single unit of work. They can be used to enforce business rules and ensure data consistency.

**Stored Procedures** can be used to enforce **Serializable** isolation level by using **Transaction** control statements.

---

### Transactions: Isolation Levels: Stored Procedures

Stored procedures are implemented by vendors. No standardization is required because they are specific to the database management system.

* T-SQL
* PL/SQL
* PL/pgSQL

### Transactions: Isolation Levels: 2PL

What is 2PL ? 

<!--
Two-Phase Locking (2PL) is a concurrency control protocol used in database systems to ensure data consistency and prevent conflicts between transactions.
-->

Is it still in use nowadays?

<!--
Yes, some database management systems still use Two-Phase Locking (2PL) as their default concurrency control protocol for serializable isolation level.
-->

---

### Transactions: Isolation Levels: Predicate Locking

What is it?

<!--
A technique used in database management systems (DBMS) to ensure data integrity and consistency by locking specific rows or sets of data based on predicates
-->

How does it work ?

<!--
It locks rows defined by predicates in WHERE clause.
-->

What are the advantages of Predicate Locking?

<!--
It reduces the amount of locks required, which can improve performance.
-->

What are the disadvantages of Predicate Locking?

<!--
It can lead to deadlocks if not implemented carefully.
-->

### Transactions: Isolation Levels: Index Locking

What is it?

<!--
A technique used in database management systems (DBMS) to ensure data integrity and consistency by locking specific rows or sets of data based on indexes
-->

How does it work ?

<!--
It locks rows defined by indexes.
-->

What are the advantages of Index Locking?

<!--
It reduces the amount of locks required, which can improve performance.
-->

What are the disadvantages of Index Locking?

<!--
It can lead to deadlocks if not implemented carefully.
-->

### Transactions: Isolation Levels: Optimistic Concurrency Control

What is it?

<!--
A technique used in database management systems (DBMS) to ensure data integrity and consistency by locking specific rows or sets of data based on indexes
-->

How does it work ?

<!--
It locks rows defined by indexes.
-->

What are the advantages of Optimistic Concurrency Control?

<!--
It reduces the amount of locks required, which can improve performance.
-->

What are the disadvantages of Optimistic Concurrency Control?

<!--
It can lead to deadlocks if not implemented carefully.
-->


### Transactions: Isolation Levels: SSI

Serializable Snapshot Isolation (pioneered by PostgreSQL) - inherits the abilities of SI allows transactions to proceed in parallel and only aborts them if a "serializability violation" is detected at commit time.

How it improves SI model ?
<!--
It improves the SI model by allowing transactions to proceed in parallel and only aborting them if a "serializability violation" is detected at commit time.
-->

---

### Transactions: Isolation Levels: SSI

SSI builds Dependency Graph of Read Write Operations to detect dangerous operations within different transactions upon common objects

How does a query work with Snapshot Isolation ?

<!--
Each query uses a separate snapshot within a transaction, while the later reference employs Snapshot Isolation to lock in the state across the transaction. Any changes made by other transactions are not visible until the transaction commits.
-->

---

### Transactions: Isolation Levels: MVCC

MVCC - an architectural method which allows multiple users to read and write to the same data simultaneously without locking each other out.

It's a manifestation of the Snapshot Isolation principle.

---

### Transactions: Isolation Levels: MVCC

Its work is based on a unique Transaction ID (txid) or timestamp assigned to each transaction upon starting a transaction. Basically, it allows new transactions to read only committed data, while writes are always visible to the current transaction.

What benefits does MVCC offer?
<!--
* Detecting stale reads
* Detecting lost updates
* Detecting write skew
-->
