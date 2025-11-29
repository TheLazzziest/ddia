# Chapter 4 Workshop: Schema Evolution Nightmare

This workshop demonstrates how data encoding (Serialization) works and what happens when schemas change. While we run everything locally for simplicity (data passed in memory), these concepts apply directly to distributed systems where services communicate via message queues or databases.

We use **Protocol Buffers** (protobuf) as the encoding format.

## Prerequisites

*   Docker
*   Docker Compose

## Scenarios

The workshop consists of 4 scenarios demonstrating different aspects of evolution.

### How to Run

Navigate to the `evolution` directory:

```bash
cd evolution
```

Run scenarios using Docker:

**Scenario 1: The Basics**

See how an object is turned into Hex bytes.

```bash
docker compose run --rm workshop python main.py 1
```

**Scenario 2: Forward Compatibility**

See how old code (V1) gracefully handles data written by new code (V2).

```bash
docker compose run --rm workshop python main.py 2
```

**Scenario 3: Breaking Changes (Silent Failure)**

See what happens when you reuse a Tag ID with a different data type. Spoiler: The app won't crash, but data will be silently lost!

```bash
docker compose run --rm workshop python main.py 3
```

**Scenario 4: Size Battle (JSON vs Protobuf)**

Compare the memory footprint of JSON vs Protobuf encoding. See how much space you can save by using binary formats!

```bash
docker compose run --rm workshop python main.py 4
```

## Key Concepts

1.  **Field Tags**: The most important part of binary encoding. Names don't matter, tags do.
2.  **Forward Compatibility**: Old code reading new data. Crucial for rolling upgrades.
3.  **Wire Types**: How Protobuf stores data types (Varint vs Length Delimited).
4.  **Silent Data Loss**: When types mismatch, parsers might just drop the data instead of crashing. This is dangerous!
5.  **Memory Efficiency**: Binary formats like Protobuf are typically 2-3x smaller than JSON because they don't store field names and use compact number encoding.
