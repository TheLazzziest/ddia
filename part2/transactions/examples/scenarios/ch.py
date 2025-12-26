# %% [markdown]
# **Goal**: OLAP Persistence & ACID Compliance
# **Structure:** MergeTree (LSM-style)
# Agenda:
# 1. Setup
# 2. Basic Usage
# 3. Isolation Levels
# 4. Locking & Partitioning
# 5. Mutations (The Anti-Pattern)
# 6. Use cases

# %% [setup]
# ### Setup the environment
%load_ext sql

# Connect to ClickHouse using the 'ch' alias
%sql clickhouse://default:@localhost:8123/default --alias ch

%config SqlMagic.feedback = False
print("✅ Sessions A and B are ready.")

# %% [markdown]
# Case: Basic Usage
# ### 1. Create the MergeTree
# %%
%%sql ch
DROP TABLE IF EXISTS ch_users;
CREATE TABLE ch_users (id UInt32, name String)
ENGINE = MergeTree() ORDER BY id;

# %% [markdown]
# ### 2. Batch Ingestion
# Every INSERT creates a physical folder called a 'Part'.
# %%
%%sql ch
INSERT INTO ch_users VALUES (1, 'Batch 1');
INSERT INTO ch_users VALUES (2, 'Batch 2');

# %% [markdown]
# ### 3. Inspecting the persistence layer
# Unlike Postgres, we look at `system.parts` to see the versions.
# %%
%%sql ch
SELECT name, active, rows, bytes_on_disk
FROM system.parts
WHERE table = 'ch_users';

# %% [markdown]
# ### 4. The Merge Cycle
# ClickHouse achieves ACID consistency by merging parts in the background.
# %%
%%sql ch
OPTIMIZE TABLE ch_users FINAL;

-- After optimization, old parts are marked inactive.
SELECT name, active, rows FROM system.parts WHERE table = 'ch_users';


# %% [markdown]
# ## Case: Isolation Levels

# %% [markdown]
# ### Atomic Inserts
# Even without 'BEGIN' and 'COMMIT', ClickHouse ensures block atomicity.
# %%
%%sql ch
-- If this fails halfway, no rows will appear in the table.
INSERT INTO users_ch (id, username, balance) VALUES
(10, 'User10', 100),
(11, 'User11', 200),
(12, 'User12', 300);

-- You will never see a "partial" result from a single INSERT block.
SELECT count() FROM users_ch WHERE id >= 10;

# %% [markdown]
# ### Snapshot Reads
# A query sees only the "Parts" that were active when the query began.
# %%
%%sql ch
-- Start a long-running query (simulated)
SELECT sleep(3), username FROM users_ch;

-- [In another window, run an INSERT]
-- INSERT INTO users_ch VALUES (99, 'LateArrival', 500);

-- Result: 'LateArrival' will NOT appear in the SELECT output
-- because it wasn't in the snapshot when the query started.


# %% [markdown]
# ## Mutation (The Anti-Pattern)
# In Postgres, UPDATE is a standard ACID operation.
# In ClickHouse, UPDATE is a "Mutation"—a heavy background rewrite of data parts.

# %%
%%sql ch
-- Create a logs table
DROP TABLE IF EXISTS service_logs;
CREATE TABLE service_logs (
    event_time DateTime,
    service_name String,
    status_code UInt16,
    response_ms UInt32
) ENGINE = MergeTree() ORDER BY (service_name, event_time);

-- Insert 1 million rows of mock data instantly
INSERT INTO service_logs
SELECT
    now() - rand() % 86400,
    'API-Gateway',
    200,
    rand() % 500
FROM numbers(1000000);

# %%
%%sql ch
-- PRODUCING AN ANOMALY: The "Slow Update"
-- In Postgres, this is instant. In ClickHouse, this is an asynchronous "Mutation".
ALTER TABLE service_logs UPDATE status_code = 500 WHERE response_ms > 450;

-- Notice: If you run this immediately, the data might NOT be changed yet.
-- ClickHouse does not guarantee "Read-Your-Writes" for Mutations.
SELECT count() FROM service_logs WHERE status_code = 500;

# %% [markdown]
# ## Case: Locking & Partitioning
# Clickhouse doesn't have locks due to its non-blocking nature. Instead, .

# %% [markdown]
# ### Independent Partition Creation
# Each batch creates a new "Part" on disk. They are independent and don't block.
# %%
%%sql ch
-- 1. Create a partitioned table
CREATE TABLE ch_partitions (id UInt32, category String, timestamp DateTime)
ENGINE = MergeTree()
PARTITION BY category
ORDER BY id;

-- 2. Independent Transaction A: Insert into Category 'Electronics'
INSERT INTO ch_partitions VALUES (1, 'Electronics', now());

-- 3. Independent Transaction B: Insert into Category 'Books'
INSERT INTO ch_partitions VALUES (2, 'Books', now());

-- 4. Inspect the filesystem (system.parts)
-- You will see two distinct 'active' parts on disk.
SELECT partition, name, active FROM system.parts
WHERE table = 'ch_partitions';

# %% [markdown]
# ### Partition Manipulation
# This is a 'Metadata' operation. It is near-instant and doesn't
# require scanning rows.
# %%
%%sql ch
-- Detach a partition (it moves to a 'detached' folder, off the active table)
ALTER TABLE orders_ch DETACH PARTITION '2023';

-- Re-attach it
ALTER TABLE orders_ch ATTACH PARTITION '2023';

-- Observe how 'Parts' are grouped by partition
SELECT partition, name, active FROM system.parts WHERE table = 'orders_ch';

# %% [markdown]
# ### The Cost of Intersecting "Updates" (Mutations)
# Mutations are asynchronous and heavy because they rewrite data parts.
# %%
%%sql ch
-- 1. Update all 'Electronics' (Mutation)
ALTER TABLE ch_partitions UPDATE timestamp = now() WHERE category = 'Electronics';

-- 2. Check mutation status
-- Unlike Postgres, this is NOT instant. It happens in the background.
-- If you run 1000 of these, the CPU will spike as it rewrites files.
SELECT command, is_done FROM system.mutations
WHERE table = 'ch_partitions';

# %% [markdown]
# ### Independent Multi-Partition Operations
# These are two separate 'events' with no shared safety net.
# %%
%%sql ch
-- Command 1: Targets Partition 2023
ALTER TABLE orders_ch UPDATE amount = 0 WHERE partition_key = 2023;

-- Command 2: Targets Partition 2024
ALTER TABLE orders_ch UPDATE amount = 500 WHERE partition_key = 2024;

-- If Command 2 fails (e.g., server restart), Command 1 stays applied!

# %% [markdown]
# ### Automatic Batch Splitting
# A single block of data is physically split into multiple partitions.
# %%
%%sql ch
INSERT INTO orders_ch (order_date, amount) VALUES
('2023-12-31', 10.0),
('2024-01-01', 20.0);

-- ClickHouse creates two separate 'parts' in two different directories.
SELECT partition, name, path FROM system.parts WHERE table = 'orders_ch' AND active = 1;

# %% [markdown]
# ## Case: Real-time Analytics (The True Use Case)
# This is where ClickHouse wins. We create a "Materialized View" (MV).
# In ClickHouse, an MV is an "Insert Trigger" that updates an aggregate table in real-time.

# %%
%%sql ch
-- 1. Create the destination table for our aggregates
CREATE TABLE daily_stats (
    day Date,
    avg_response AggregateFunction(avg, UInt32)
) ENGINE = AggregatingMergeTree() ORDER BY day;

-- 2. Create the Materialized View
-- This "pipes" incoming data into the daily_stats table automatically
CREATE MATERIALIZED VIEW daily_stats_mv TO daily_stats AS
SELECT toDate(event_time) AS day, avgState(response_ms) AS avg_response
FROM service_logs
GROUP BY day;

# %%
%%sql ch
-- 3. Insert more data and see the ACID "Trigger" work
INSERT INTO service_logs VALUES (now(), 'API-Gateway', 200, 1000);

-- Query the aggregate (requires -Merge suffix for AggregateFunctions)
SELECT day, avgMerge(avg_response) FROM daily_stats GROUP BY day;
