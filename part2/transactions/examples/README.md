## Why

This workshop uses PostgreSQL (OLTP) and ClickHouse (OLAP) as primary case studies because they represent the two dominant (and fundamentally different) ways of solving the ACID and Persistence challenge in modern software engineering.

1. The Architectural Divide

    PostgreSQL: Built on a B-Tree Index + Heap Storage model. It is designed for "Online Transactional Processing," where row-level accuracy, strict consistency, and the ability to update a single record in milliseconds are the priorities.

    ClickHouse: Built on a MergeTree (LSM-style) model. It is designed for "Online Analytical Processing," where the priority is ingesting millions of rows per second and querying billions of records across massive physical "Parts."

2. Different Flavors of MVCC

While both databases use Multi-Version Concurrency Control (MVCC) to allow simultaneous reads and writes, their internal persistence layers handle it differently:

    Postgres maintains row versions within the table itself (using xmin/xmax metadata), necessitating a "Vacuum" process to clean up "dead" tuples.

    ClickHouse treats data as immutable "Parts" on disk. Updates and deletions are handled by merging these physical files together in the background, a process known as "Compaction" in LSM-based systems.

3. ACID vs. Performance

    PostgreSQL provides the "Gold Standard" of ACID: Serializable Isolation. It is the tool of choice when losing a single transaction (like a bank transfer) is unacceptable.

    ClickHouse provides "Block-level" Atomicity. It is optimized for throughput over fine-grained isolation, demonstrating how databases can relax certain ACID properties to achieve order-of-magnitude speed increases in analytics.

By comparing these two, you will gain a deep understanding of the trade-offs inherent in database design: the balance between write-throughput, read-latency, and data-integrity guarantees.

## Requirements

* [SQL Notebook](https://marketplace.visualstudio.com/items?itemName=cmoog.sqlnotebook)
* [Docker Compose](https://docs.docker.com/compose/)

## Setup

1. Start Docker Compose:
   ```bash
   docker-compose up -d
   ```
2. Install [uv](https://github.com/uv/uv)
3. Sync the environment variables:
   ```bash
   uv sync
   ```
4. Open both python files and run the cells until MVCC Snapshot


## Commands

* Connect to clickhouse: `docker-compose exec clickhouse clickhouse-client`
* Connect to postgres: `docker-compose exec postgres psql -U postgres`
