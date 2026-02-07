# %% [markdown]
# # **Goal**: OLTP Persistence & ACID Compliance
# **Structure:** B-Tree + Heap Storage
# Agenda:
# 1. Setup
# 2. Basic Usage
# 3. Isolation Levels
# 4. Locking & Partitioning
# 5. Use cases

# %% [setup]
# ### Setup the environment
%load_ext sql
%config SqlMagic.feedback = False

# Create aliases
%sql postgresql+psycopg2://admin:password@localhost:5432/acid_test --alias pg
%sql postgresql+psycopg2://admin:password@localhost:5432/acid_test --alias session_a
%sql postgresql+psycopg2://admin:password@localhost:5432/acid_test --alias session_b

print("✅ Sessions A and B are ready.")

# %% [markdown]
# Case: Basic Usage
# Every row in the Heap is a "tuple" with metadata.
# %%
%%sql pg
CREATE EXTENSION IF NOT EXISTS pageinspect;
DROP TABLE IF EXISTS pg_users;
CREATE TABLE pg_users (id INT PRIMARY KEY, name TEXT);
INSERT INTO pg_users VALUES (1, 'Alice');

# %% [markdown]
# ### Transactional DDL (WAL Logged)
# In Postgres, DDL commands (CREATE, ALTER, DROP) are written to the Write-Ahead Log (WAL).
# This means they are fully transactional and can be rolled back.
# %%
%%sql pg
BEGIN;
CREATE TABLE pg_ghost (id int);
-- Oops, changed my mind
ROLLBACK;

-- The table does not exist (returns NULL)
SELECT to_regclass('pg_ghost');

# %% [markdown]
# ### Current Transaction ID
# To see the current transaction identifier (which increments globally), use `txid_current()`.
# This helps compare against `xmin` values in rows.
# %%
%%sql pg
SELECT txid_current();

# %% [markdown]
# ### Examine MVCC "Snapshot"
# Observe `xmin` (ID of the transaction that created the row).
# %%
%%sql pg
SELECT ctid, xmin, xmax, * FROM pg_users;

# %% [markdown]
# Locate the tuples on physical pages to track the lineage
# %%
%%sql pg
SELECT lp, t_xmin, t_xmax, t_ctid FROM heap_page_items(get_raw_page('pg_users', 0));

# %% [markdown]
# ### MVCC In-Place Update (Actually an Append)
# When we update, Postgres creates a new version.
# %%
%%sql pg
UPDATE pg_users SET name = 'Bob' WHERE id = 1;

-- Notice xmin increased; Bob is a new version.
-- Alice is physically still there but invisible (dead).
SELECT *, xmin, xmax FROM pg_users;

# %% [markdown]
# ### 4. Vacuum (The Cleanup)
# In Postgres, dead versions stay until 'Vacuum' clears them.
# %%
%%sql pg
VACUUM FULL pg_users;
SELECT ctid, xmin, xmax, * FROM pg_users;
SELECT lp, t_xmin, t_xmax, t_ctid FROM heap_page_items(get_raw_page('pg_users', 0));

# %% [markdown]
# ### Case: The "Dead Row" (Bloat) Effect
# Postgres stores old versions of rows in the same data file.
# %%
%%sql pg
-- 1. Create a table and insert a row
CREATE TABLE pg_demo (id Int, val Text);
INSERT INTO pg_demo VALUES (1, 'Version 1');

-- 2. Observe xmin (Transaction ID)
SELECT *, xmin FROM pg_demo;

-- 3. Intersecting Update: $T1$ updates the row
UPDATE pg_demo SET val = 'Version 2' WHERE id = 1;

-- 4. Result: The old row is still physically on disk but marked 'dead'
-- We can see the version change via xmin.
SELECT *, xmin FROM pg_demo;


# %% [markdown]
# ## Case: TOAST (The Oversized-Attribute Storage Technique)
# Postgres pages are fixed size (usually 8KB). Rows cannot span pages.
# If a row is too big, Postgres moves large columns to a separate "TOAST" table.

# %%
%%sql pg
DROP TABLE IF EXISTS pg_toast_demo;
CREATE TABLE pg_toast_demo (id INT, content TEXT);

-- 1. Insert a small row (Stored inline)
INSERT INTO pg_toast_demo VALUES (1, 'Small string');

-- 2. Insert a massive row (Larger than 8KB page)
-- repeat('A', 20000) creates a string ~20KB, forcing TOAST
INSERT INTO pg_toast_demo VALUES (2, repeat('A', 20000));

# %%
%%sql pg
-- 3. Check storage usage
-- pg_relation_size('table') = Main Heap size
-- pg_table_size('table') = Main Heap + TOAST (excluding indexes)
SELECT 
    pg_size_pretty(pg_relation_size('pg_toast_demo')) as heap_size,
    pg_size_pretty(pg_table_size('pg_toast_demo') - pg_relation_size('pg_toast_demo')) as toast_size;

# %% [markdown]
# ## Case: Isolation Levels
# %%

# %% [markdown]
# ## Isolation: Read Commited
# ## Side Effect: Non-Repeatable Read
# We show that Session A sees data change *during* its transaction because Session B committed.

# %%
# Create a table for tracking balance
# %%
%%sql pg
DROP TABLE IF EXISTS accounts;
CREATE TABLE accounts (id INT, balance INT);
INSERT INTO accounts VALUES (1, 1000);

# %%
# First user starts a transaction
# %% 
%%sql session_a
BEGIN ISOLATION LEVEL READ COMMITTED;
-- Snapshot 1
SELECT balance FROM accounts WHERE id = 1;

# %%
%%sql session_b
-- Session B updates the balance and commits
UPDATE accounts SET balance = 500 WHERE id = 1;

# %%
%%sql session_a
-- Snapshot 2: Even though Session A is in a transaction, it sees the new value!
-- This is a "Non-Repeatable Read".
SELECT balance FROM accounts WHERE id = 1;
COMMIT;

# %% [markdown]
# ## Isolation: Read Committed
# ## Side Effect: Phantom Read
# Logic: Session A is checking a range. Session B "sneaks" a new record into that range.

# %%
%%sql session_a
DROP TABLE IF EXISTS sales;
CREATE TABLE sales (id INT, amount INT, category TEXT);
INSERT INTO sales VALUES (1, 100, 'Electronics'), (2, 200, 'Electronics');

# %%
%%sql session_a
-- Session A starts a transaction to sum up Electronics
BEGIN;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED; -- Standard level
SELECT SUM(amount) FROM sales WHERE category = 'Electronics'; -- Result: 300

# %%
%%sql session_b
-- Session B inserts a NEW record that matches Session A's filter
INSERT INTO sales VALUES (3, 500, 'Electronics');

# %%
%%sql session_a
-- Session A runs the same query again.
-- The "Phantom" (the 500 row) now appears in the result!
SELECT SUM(amount) FROM sales WHERE category = 'Electronics'; -- Result: 800
COMMIT;


# %% [markdown]
# ### Isolation: Repeatable Read
# ### Side Effect: No (due to Snapshot Isolation)
# Prevents Non-repeatable reads, but can fail on concurrent updates.
# %%
%%sql pg
-- Transaction A
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT SUM(amount) FROM sales WHERE category = 'Electronics'; -- Initial: 800

-- [Transaction B (Session 2) updates and commits]
-- UPDATE sales SET amount = 500 WHERE id = 1; COMMIT;

-- Transaction A executes again
SELECT SUM(amount) FROM sales WHERE category = 'Electronics'; -- Initial: 800

-- BUT: If Transaction A tries to update that same row:
UPDATE sales SET amount = 600 WHERE id = 1;
-- ERROR: could not serialize access due to concurrent update
ROLLBACK;

# %% [markdown]
# ## Isolation: Repeatable Read
# ## Side Effect: Write Skew (Snapshot Isolation vs Serializable)
# This is the classic "Doctor On-Call" problem where logic is violated.

# %%
%%sql session_a
DROP TABLE IF EXISTS doctors;
CREATE TABLE doctors (name TEXT, on_call BOOLEAN);
INSERT INTO doctors VALUES ('Alice', true), ('Bob', true);

# %%
%%sql session_a
-- Doctor Alice wants to go off-call
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; -- High but vulnerable
SELECT count(*) FROM doctors WHERE on_call = true; -- Sees 2

# %%
%%sql session_b
-- Doctor Bob wants to go off-call at the same time
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM doctors WHERE on_call = true; -- Sees 2

# %%
%%sql session_a
UPDATE doctors SET on_call = false WHERE name = 'Alice';
COMMIT;

# %%
%%sql session_b
UPDATE doctors SET on_call = false WHERE name = 'Bob';
COMMIT;

# %%
%%sql session_a
-- Result: 0 doctors on call. The business rule (at least 1) is broken.
-- If you repeat this with SERIALIZABLE, Session B will fail on COMMIT.
SELECT * FROM doctors;

# %% [markdown]
# ## Case: Write Skew (The "Distributed Balance" Problem)
# Logic: Total (Checking + Savings) must be >= 0.
# Initial: Checking ($100), Savings ($100). Total = $200.

# %%
%%sql session_a
DROP TABLE IF EXISTS bank_accounts;
CREATE TABLE bank_accounts (account_type TEXT PRIMARY KEY, balance INT);
INSERT INTO bank_accounts VALUES ('Checking', 100), ('Savings', 100);

# %%
%%sql session_a
-- Session A wants to withdraw $150 from Checking
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- Checks total: 100 + 100 = 200. "I can withdraw $150."
SELECT SUM(balance) FROM bank_accounts;

# %%
%%sql session_b
-- Session B simultaneously wants to withdraw $150 from Savings
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- Checks total: 100 + 100 = 200. "I can withdraw $150."
SELECT SUM(balance) FROM bank_accounts;

# %%
%%sql session_a
UPDATE bank_accounts SET balance = balance - 150 WHERE account_type = 'Checking';
COMMIT;

# %%
%%sql session_b
UPDATE bank_accounts SET balance = balance - 150 WHERE account_type = 'Savings';
COMMIT;

# %%
%%sql session_a
-- THE ANOMALY: Total balance is now -$100.
-- Neither transaction "violated" the rule in their own snapshot,
-- but together they skewed the result.
SELECT * FROM bank_accounts;
SELECT SUM(balance) as total_now FROM bank_accounts;

# %% [markdown]
# ## Case: Locking & Partitioning

# %% [markdown]
# ### Partitioning (The Logical vs. Physical)
# We create a parent table and specific children (partitions).
# %%
%%sql pg
-- 1. Create the parent table (The Logical Layer)
CREATE TABLE orders (
    id SERIAL,
    order_date DATE NOT NULL,
    amount DECIMAL
) PARTITION BY RANGE (order_date);

-- 2. Create independent partitions (The Physical Layer)
CREATE TABLE orders_2023 PARTITION OF orders
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE orders_2024 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 3. Insert data: Postgres routes the transaction to the correct partition
INSERT INTO orders (order_date, amount) VALUES ('2023-06-15', 100.00);
INSERT INTO orders (order_date, amount) VALUES ('2024-02-10', 250.00);

# %% [markdown]
# ### Visualizing the Lock Tree
# We will lock a single row and see how many "Intent" locks are created.
# %%
%%sql pg
-- Transaction 1
BEGIN;
-- Updating a single row in a specific partition
UPDATE orders_2024 SET amount = 99.99 WHERE id = 1;

-- Now, look at the lock 'Mode'.
-- You'll see RowExclusiveLock on the partition AND the parent table.
SELECT
    relname as table_name,
    mode,
    locktype,
    granted
FROM pg_locks l
JOIN pg_class c ON l.relation = c.oid
WHERE relname LIKE 'orders%';

# %% [markdown]
# ### Concurrent Access to Partitions
# Different transactions can modify different partitions simultaneously.
# Locking is granular (per-partition), not global (parent table).
# %%
%%sql session_a
BEGIN;
-- Update Row in Partition A (2023)
UPDATE orders SET amount = 555 WHERE id = 1;

# %%
%%sql session_b
BEGIN;
-- Update Row in Partition B (2024)
-- This proceeds immediately, proving that Session A did not lock the whole 'orders' table.
UPDATE orders SET amount = 666 WHERE id = 2;

# %%
%%sql session_a
COMMIT;

# %%
%%sql session_b
COMMIT;
