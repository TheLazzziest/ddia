---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
marp: true
style: |
  section {
    font-size: 30px;
  }
  code {
    font-size: 80%;
  }
---

# **Encoding and Evolution**

### Chapter 4

*Handling data changes in long-running systems*

---

# **The Reality of Change**

In a complex system, change is constant:

1.  **Code changes**: New features, bug fixes.
2.  **Data changes**: New fields, structure updates.

**The Challenge**:
Code and data rarely change at the exact same instant across all nodes (Rolling Upgrades).

We need **Compatibility**.

---

# **Types of Compatibility**

To allow "Rolling Upgrades" (no downtime), we need two directions of compatibility:

### 1. Backward Compatibility
**Newer code** can read data written by **older code**.
*(You can read history)*

### 2. Forward Compatibility
**Older code** can read data written by **newer code**.
*(You can handle the future)*

---

# **Formats for Encoding Data**

How do we turn in-memory objects into bytes?

1. **Language-specific** (Java `Serializable`, Python `pickle`)
   * ⛔️ **Bad**: Security risks, tied to one language, no versioning.

2. **Textual** (JSON, XML, CSV)
   * ✅ **Pros**: Human-readable, ubiquitous.
   * ⚠️ **Cons**: Verbose, ambiguous types, weak schema evolution.

3. **Binary Schema-Driven** (Protobuf, Thrift, Avro)
   * ✅ **Pros**: Compact, fast, clear documentation.
   * ⭐️ **Best for**: Internal APIs and long-term storage.

---

# **Binary Encoding**
### Thrift & Protocol Buffers

They rely on **Field Tags** (numbers), not field names.

message Person {
    required string user_name = 1;
    optional int64 favorite_number = 2;
    repeated string interests = 3;
}*   **Encoded data**: Contains the field tag (`1`) and the type, but NOT the field name (`user_name`).
*   **Result**: Extremely small size compared to JSON.

---

# **Schema Evolution in Binary**

How to change the schema without breaking compatibility?

**Adding a Field:**
*   Give it a new tag number (e.g., `4`).
*   **Old code** reads new data: Ignores tag `4` (Forward Compatible).
*   **New code** reads old data: Tag `4` is missing, fills default/null (Backward Compatible).

**Removing a Field:**
*   You can only remove optional fields.
*   **CRITICAL**: Never reuse the tag number again.

---

# **Modes of Data Flow**

Data flows between processes in three main ways. Each handles evolution differently.

1.  **Databases** (Data at Rest)
2.  **Services / RPC** (Data in Motion - Sync)
3.  **Message Passing** (Data in Motion - Async)

---

# **1. Databases (Data Outlives Code)**

*   **Scenario**: Process A writes data. Process B reads it 5 years later.
*   **Problem**: Rewriting all data (migration) is expensive for big datasets.
*   **Solution**:
    *   Most relational DBs allow simple schema changes (add column null).
    *   New code must handle reading old rows (missing new columns).
    *   *Data dumping/restoring*: Always encode in the latest format.

---

# **2. Services (REST & RPC)**

*   **Scenario**: Client sends request to Server.
*   **REST (JSON)**: Loose schemas. Adding fields usually fine.
*   **RPC (gRPC/Thrift)**: Strong schemas.
    *   **Rolling Update**: Servers are updated first.
    *   Old clients must talk to New Servers (**Backward Compatibility**).
    *   New clients might talk to Old Servers (**Forward Compatibility**).

*RPC frameworks handle this by ignoring unknown fields.*

---

# **3. Message Passing (Async)**

*   **Tools**: Kafka, RabbitMQ.
*   **Scenario**: Asynchronous decoupling.
*   **Challenge**: The sender (Producer) and receiver (Consumer) are loosely coupled.
    *   A consumer might crash and restart days later (processing old messages).
    *   A producer might be updated to a new schema before consumers.

**Solution**:
Central Schema Registry (e.g., Confluent Schema Registry) ensures encoded data matches a valid schema version.

---

# **Summary**

1.  **Rolling Upgrades** require both Backward and Forward compatibility.
2.  **JSON/XML** are good for APIs, but **Binary (Protobuf/Avro)** are superior for internal efficiency and strict evolution.
3.  **Field Tags** are the key to evolution in binary formats.
4.  **Data outlives code**: Your database contains data written by code that no longer exists. Treat schemas with care.