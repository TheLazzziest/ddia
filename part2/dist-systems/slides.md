---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
marp: true
---

# Welcome

![bg right](assets/ddia.png)

---

## Challenges

* Unreliable networks
<!-- Request/Response" Uncertainty -->
<!-- The Network Partition (Split Brain) -->
<!-- Partial failure: Power outage, Crash, etc. -->
* Unreliable clocking
<!-- Clock Skew -->
<!-- The Leap Second Glitch -->
* Knowledge of Truth and Lies
<!-- The "Zombie" Leader (STONITH) -->
<!-- Byzantine Faults -->

---

## Challenges: Unreliable networks

**Reasons**: Variadic Timeoutes, Network Congestion, Network Partitioning
 
* Unnecessary Rebalancing
* Increased Load
* The "Zombie" Problem 

**Solution**: monitor network delay variance -> Phi Accrual Failure Detector

---

### Estimates

We can detect network failures.
But can we measure **when** they happened?
Do we know what time it is?

---

## Challenges: Unreliable Clocking

What clock types do we have ?

* **Time-of-Day clock**: Used for human-readable timestamps
* **Monotonic Clocks**: Used for measuring durations

Why those are not enough ? 
What kind of issues can they experience ?

---

## Challenges: Unreliable Clocking

<!--

Has this request timed out yet?

What’s the 99th percentile response time of this service?

How many queries per second did this service handle on average in the last five minutes?

How long did the user spend on our site?

When was this article published?

At what date and time should the reminder email be sent?

When does this cache entry expire?

What is the timestamp on this error message in the log file?

-->

**Reasons**: Network Jitter, Synchronization issues, Jump Problems, Virtualization issues, Remote devices, HTP Servers misconfiguration

* Last Write Wins (LWW) <!-- Why: Silent disregard the new data due to timestamp differences--> 
* Ghost Reads <!-- Why: Lack of consistency in Snapshot Isolation due to an invalid order of timestamps assigned to transactions -->
* Process pauses 
<!-- Reasons:
* stop the world done by GC
* suspension of VMs done by schedulers
* OS context switching 
* Synchronous IO operations 
-->

---

## Challenges: Unreliable Clocking: Solution

**Logical clocks** - a mechanism keeping the relative order of events across a cluster

What problem does it solve primarily ?
<!--  It tracks causality (which event happened before another) even when physical time stamps can’t be trusted. -->

What are the popular kinds of logical clocks do we have ?

---

## Challenges: Unrelialbe Clocking: Solution

* **Lamport Timestamps**: A simple way to give every event a unique, increasing number so we can always say "A happened before B."

* **Vector Clocks**: A more advanced version that helps us detect "concurrent" writes (when two things happen at once and neither knows about the other).

* **Fencing Tokens**: A practical way to stop a "zombie" node from writing data after its lease has expired due to a clock jump or GC pause.

---

### Challenges: Unreliable Clocking: Question

We can order events using Logical Clocks.
But what if the node sending the event is **wrong**?
What if it thinks it's the leader, but it's not?

---

## Challenges: Knowledge of Truth and Lies

How truthfullness is achived in a leader-based systems ?
<!-- Keeping the leader clocks in sync -->
How is it different from a truth in a distributed environment ? <!-- By achieving consensus among the nodes in a cluster -->

---

## Challenges: Knowledge of Truth and Lies

**Reasons:** Network partitioning, GC stop-the-world, Node malfunctioning, Malicious codebase, Natural Conditions

* **The "Zombie" Leader (STONITH)**: A node might be experience pauses (e.g.: by a Garbage Collection (GC) stop-the-world event).
<!-- While it's "frozen," its lease expires and a new leader is elected. When the old leader "wakes up," it still thinks it's in charge and starts writing data, unaware it has been replaced. -->

* **Byzantine Faults**: This is when a node doesn't just crash, but stays alive and sends incorrect or malicious data. 
<!-- While rare in data centers, it's a huge challenge for peer-to-peer systems like Blockchains. -->

**Solution:** Design sophisticated algorithms that can tolerate faults in distributed systems

---

### Transition

The world is messy.
* Networks are unreliable.
* Clocks are unreliable.
* Nodes can be truthful or deceitful.

How do we build systems we can trust?
<!-- We need a Model -->

---

## Design

How to design such algorithms ? 
<!-- We need to design them to work undependently from any hardware/software -->

What is a system model ?
<!-- it is an abstraction that describes what things an algorithm may assume-->

What aspects of a distributed system should be covered by system models ?
<!-- Timing assumptions, Node Failure assumptions, -->

---

## Design: System Models: Timing

* **Synchronous**: Assumes there is a known upper bound on network delay and processing time (rare in real-world internet systems).

* **Asynchronous**:  an algorithm is not allowed to make any timing assumptions 
<!-- in fact, it does not even have a clock -->

* **Partially Synchronous**: a system behaves like a synchronous system most of the time, but it
sometimes exceeds the bounds for network delay, process pauses, and clock drift

---

## Design: System Models: Node Failure

* **Crash-stop faults** -  may assume that a node can fail in only one way, namely by crashing.

* **Crash-recovery faults** - may assume a node may crash at any moment, and perhaps start responding again after some
unknown time. 

* **Byzantine (arbitrary) faults** - may assume that a node may do absolutely anything, including trying to trick and deceive other nodes.

---

## Design: Safety and Liveness

* **Safety** ("Nothing bad happens"): For example, two different leaders are never elected at the same time. If a safety property is violated, the damage is often permanent (like corrupted data).

* **Liveness** ("Something good eventually happens"): For example, every request eventually receives a response. If a liveness property is violated (like a system hanging), it might just be "stuck" rather than "broken."

---

### Design: Reality Check

Which model fits the real world (Internet/Datacenter)?

* **Synchronous?** <!-- No. Delays are unbounded. -->
* **Asynchronous?** <!-- Too hard. We can't distinguish crash from delay. -->
* **Partially Synchronous?** **Yes.** <!-- We assume the system eventually behaves well enough to make progress. -->

---
