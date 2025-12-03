# Chapter 4 Workshop: Schema Evolution Nightmare

This workshop demonstrates how data encoding (Serialization) works and what happens when schemas change. While we run everything locally for simplicity (data passed in memory), these concepts apply directly to distributed systems where services communicate via message queues or databases.

We use **Protocol Buffers** (protobuf) as the encoding format.

## Prerequisites

*   Docker
*   Docker Compose

## Scenarios

The workshop consists of 4 scenarios demonstrating different aspects of evolution.

Navigate to the `evolution` directory:

```bash
cd evolution
```

## Setup

**First time setup** - Build the Docker image:

```bash
docker compose build
```

This will install all dependencies and configure the environment. Protobuf schemas are automatically compiled when you run a container - the entrypoint checks if compilation is needed and only compiles if `.proto` files have changed.

## Running Scenarios

Run scenarios using Docker:

**Scenario 1: The Basics**

See how an object is turned into Hex bytes.

```bash
docker compose run --rm workshop python3 main.py 1
```

**Scenario 2: Forward Compatibility**

See how old code (V1) gracefully handles data written by new code (V2).

```bash
docker compose run --rm workshop python3 main.py 2
```

**Scenario 3: Breaking Changes (Silent Failure)**

See what happens when you reuse a Tag ID with a different data type. Spoiler: The app won't crash, but data will be silently lost!

```bash
docker compose run --rm workshop python3 main.py 3
```

**Scenario 4: Size Battle (JSON vs Protobuf)**

Compare the memory footprint of JSON vs Protobuf encoding. See how much space you can save by using binary formats!

```bash
docker compose run --rm workshop python3 main.py 4
```

## gRPC Client/Server Demo

This workshop also includes a gRPC client/server demonstration that shows schema evolution over a real network connection.

**Starting the gRPC Server:**

```bash
docker compose up -d server
```

The server will start on port 50051 and use `person_v2` schema internally.

**Running the gRPC Client:**

```bash
docker compose run --rm client
```

The client uses `person_v1` schema to demonstrate forward compatibility - it can successfully interact with the server even though the server uses a newer schema version.

This demonstrates how schema evolution works in real distributed systems where clients and servers may be running different versions of the schema.

**Stopping the server:**

```bash
docker compose down
```

## Key Concepts

1.  **Field Tags**: The most important part of binary encoding. Names don't matter, tags do.
2.  **Forward Compatibility**: Old code reading new data. Crucial for rolling upgrades.
3.  **Wire Types**: How Protobuf stores data types (Varint vs Length Delimited).
4.  **Silent Data Loss**: When types mismatch, parsers might just drop the data instead of crashing. This is dangerous!
5.  **Memory Efficiency**: Binary formats like Protobuf are typically 2-3x smaller than JSON because they don't store field names and use compact number encoding.
6.  **Network Interaction**: gRPC demonstrates how schema evolution works in real distributed systems with network communication.
