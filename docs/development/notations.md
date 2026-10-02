# Performance Notations and Empirical Validation

This document provides empirical validation of the Big O notations asserted for key operations within the `Kind` framework. It includes detailed measurements and analysis of time and space complexity for various operations, along with a discussion of potentially slow callables.

## O(1) Kind Instantiation

**Assertion**: Retrieving an interned Kind by name is an O(1) operation; creating a new Kind is O(log n), because it is also inserted into the creation-order index (an AVL tree) behind `Kind.first()`, `Kind.seek()` and `Kind.each()`.

**Methodology**: We measure the time taken to instantiate a large number of unique and repeated kinds. The pool is weak, so the measurement keeps references to the Kinds it creates. Timings below are from one run (2026-10-02); they vary by machine.

**Empirical Results**:

```python
import time
from kind import Kind, k

def measure_kind_instantiation(num_kinds):
    kept = []  # the pool is weak: an unreferenced Kind is collected and would be created anew
    start_time = time.perf_counter_ns()
    for i in range(num_kinds):
        kept.append(Kind(f"test_kind_{num_kinds}_{i}")) # Unique kinds
    end_time = time.perf_counter_ns()
    time_unique = (end_time - start_time) / 1_000_000 # milliseconds

    repeated = Kind("repeated_kind")  # held, so the loop below measures retrieval from the pool
    start_time = time.perf_counter_ns()
    for i in range(num_kinds):
        Kind("repeated_kind") # Repeated kind
    end_time = time.perf_counter_ns()
    time_repeated = (end_time - start_time) / 1_000_000 # milliseconds

    return time_unique, time_repeated

print("\n--- Kind Instantiation Performance ---")
for n in [1000, 10000, 100000]:
    time_u, time_r = measure_kind_instantiation(n)
    print(f"N={n}: Unique Kinds: {time_u:.4f} ms, Repeated Kind: {time_r:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- Kind Instantiation Performance ---
N=1000: Unique Kinds: 4.7220 ms, Repeated Kind: 0.1607 ms
N=10000: Unique Kinds: 55.2010 ms, Repeated Kind: 1.6028 ms
N=100000: Unique Kinds: 943.8003 ms, Repeated Kind: 15.8094 ms
```
</details>

**Analysis**: Retrieval stays at a constant ~0.16 µs per call, validating O(1). Creation grows from ~4.7 µs to ~9.4 µs per Kind as N grows 100-fold, consistent with the O(log n) index insert plus allocation and garbage-collector overhead.

## O(1) Relationship Linking

**Assertion**: Establishing relationships between kinds (e.g., via `append()`) is an O(1) operation.

**Methodology**: We measure the time taken to append a new child to a kind. This operation adds to two `OrderedKindSet`s (the parent's children and the child's parents): a set insert plus a list append, both amortized O(1).

**Empirical Results**:

```python
import time
from kind import Kind, k

def measure_relationship_linking(num_links):
    root = k.root_node
    children = [getattr(k, f"child_{i}") for i in range(num_links)]

    start_time = time.perf_counter_ns()
    for child in children:
        root.append(child)
    end_time = time.perf_counter_ns()
    time_taken = (end_time - start_time) / 1_000_000 # milliseconds
    return time_taken

print("\n--- Relationship Linking Performance ---")
for n in [1000, 10000, 100000]:
    time_t = measure_relationship_linking(n)
    print(f"N={n}: Time to link {n} children: {time_t:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- Relationship Linking Performance ---
N=1000: Time to link 1000 children: 0.8707 ms
N=10000: Time to link 10000 children: 8.6695 ms
N=100000: Time to link 100000 children: 91.3839 ms
```
</details>

**Analysis**: The time taken to link relationships scales linearly with the number of links, confirming the amortized O(1) complexity per link. This is consistent with Python's set insert and list append performance characteristics.


## O(log n) Insert/Search in the AVL-backed Index

**Assertion**: Insert and search operations within `KindIndex` (backed by a balanced AVL tree) are O(log n).

**Methodology**: We measure the time taken to insert and search for elements in a `KindIndex` as the number of elements increases. The expectation is a logarithmic growth in time.

**Empirical Results**:

```python
import time
import random
from kind import k
from kind.builtin.index import KindIndex


def measure_index_performance(num_elements):
    idx = KindIndex(k.index_root)
    elements = [getattr(k, f"element_{i}") for i in range(num_elements)]
    weights = list(range(num_elements))
    random.shuffle(weights)

    # Measure insertion
    insert_start_time = time.perf_counter_ns()
    for element, weight in zip(elements, weights):
        idx.insert(element, float(weight))
    insert_end_time = time.perf_counter_ns()
    insert_time = (insert_end_time - insert_start_time) / 1_000_000

    # Measure search by weight (for existing elements)
    search_start_time = time.perf_counter_ns()
    for weight in weights:
        idx.tree.search(float(weight))
    search_end_time = time.perf_counter_ns()
    search_time = (search_end_time - search_start_time) / 1_000_000

    return insert_time, search_time


print("\n--- KindIndex Performance (O(log n)) ---")
for n in [1000, 10000, 100000]:
    insert_t, search_t = measure_index_performance(n)
    print(f"N={n}: Insert: {insert_t:.4f} ms, Search: {search_t:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- KindIndex Performance (O(log n)) ---
N=1000: Insert: 2.3334 ms, Search: 0.4733 ms
N=10000: Insert: 29.8964 ms, Search: 5.9381 ms
N=100000: Insert: 415.2549 ms, Search: 103.4067 ms
```
</details>

**Analysis**: Per operation, insertion grows from ~2.3 µs to ~4.2 µs and search from ~0.5 µs to ~1.0 µs as N grows 100-fold, a growth consistent with O(log n) (plus cache effects at the largest size).

## Potentially Slow Callables and Their Complexity

This section identifies and analyzes operations that might exhibit higher time or space complexity, providing insights into their behavior and potential optimizations.

### `Kind.tree()` and `Kind.graph()` (Graph Traversal)

**Complexity**: O(V + E), where V is the number of vertices (kinds) and E is the number of edges (relationships) reachable from the starting kind.

**Analysis**: These methods perform a full traversal of the reachable graph. In the worst case (a dense graph), every vertex and every edge must be visited. While efficient for their purpose, their performance is directly proportional to the size and density of the traversed subgraph.

```python
import time
from kind import k, Kind

def build_dense_graph(num_nodes):
    nodes = [Kind(f"node_{i}") for i in range(num_nodes)]
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            nodes[i].append(nodes[j])
    return nodes[0]

def measure_graph_traversal(num_nodes):
    root = build_dense_graph(num_nodes)
    start_time = time.perf_counter_ns()
    list(root.tree()) # Convert iterator to list to force full traversal
    end_time = time.perf_counter_ns()
    time_taken = (end_time - start_time) / 1_000_000
    return time_taken

print("\n--- Graph Traversal Performance (O(V + E)) ---")
for n in [100, 200, 400]: # Keep N small due to O(N^2) edges in dense graph
    time_t = measure_graph_traversal(n)
    print(f"N={n}: Time for traversal: {time_t:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- Graph Traversal Performance (O(V + E)) ---
N=100: Time for traversal: 1.0434 ms
N=200: Time for traversal: 2.4492 ms
N=400: Time for traversal: 13.6653 ms
```
</details>

### `Kind.patch()` (Shallow Merge)

**Complexity**: O(c + p + r), where c, p and r are the numbers of children, parents and relations of the *other* Kind.

**Analysis**: The `patch()` method is not recursive: it copies the other Kind's origin (if this one has none), links its direct children and parents, and copies its forward relations. The descendants come along by reference, not by copying, so a long chain behind the other Kind costs nothing extra — as the flat timings below show.

```python
import time
from kind import k, Kind

def build_linear_graph(num_nodes, prefix):
    nodes = [Kind(f"{prefix}_node_{i}") for i in range(num_nodes)]
    for i in range(num_nodes - 1):
        nodes[i].append(nodes[i+1])
    return nodes[0]

def measure_patch_performance(num_nodes):
    kind1 = build_linear_graph(num_nodes, "kind1")
    kind2 = build_linear_graph(num_nodes, "kind2")

    start_time = time.perf_counter_ns()
    kind1.patch(kind2)
    end_time = time.perf_counter_ns()
    time_taken = (end_time - start_time) / 1_000_000
    return time_taken

print("\n--- Kind.patch() Performance ---")
for n in [100, 200, 400]:
    time_t = measure_patch_performance(n)
    print(f"N={n}: Time for patch: {time_t:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- Kind.patch() Performance ---
N=100: Time for patch: 0.0054 ms
N=200: Time for patch: 0.0036 ms
N=400: Time for patch: 0.0024 ms
```
</details>

### `Kind.to_mmd()` and `Kind.to_ascii()` (Visualization)

**Complexity**: O(V + E) for generating the string representation, where V is the number of vertices and E is the number of edges in the visualized subgraph.

**Analysis**: These methods traverse the graph to generate a textual representation. Their performance is directly proportional to the size of the subgraph being visualized. For very large graphs, generating these strings can consume significant time and memory.

```python
import time
from kind import k, Kind

def measure_visualization_performance(num_nodes):
    root = Kind("viz_root")
    nodes = [Kind(f"viz_node_{i}") for i in range(num_nodes)]
    for node in nodes:
        root.append(node)

    start_time = time.perf_counter_ns()
    root.to_mmd()
    end_time = time.perf_counter_ns()
    mmd_time = (end_time - start_time) / 1_000_000

    start_time = time.perf_counter_ns()
    root.to_ascii()
    end_time = time.perf_counter_ns()
    ascii_time = (end_time - start_time) / 1_000_000

    return mmd_time, ascii_time

print("\n--- Visualization Performance (O(V + E)) ---")
for n in [1000, 5000, 10000]:
    mmd_t, ascii_t = measure_visualization_performance(n)
    print(f"N={n}: to_mmd: {mmd_t:.4f} ms, to_ascii: {ascii_t:.4f} ms")
```
<details>
<summary>Outcome</summary>

```text

--- Visualization Performance (O(V + E)) ---
N=1000: to_mmd: 1.5134 ms, to_ascii: 1.8185 ms
N=5000: to_mmd: 8.5232 ms, to_ascii: 9.1434 ms
N=10000: to_mmd: 15.7913 ms, to_ascii: 17.9667 ms
```
</details>

## Conclusion

The empirical measurements largely validate the theoretical Big O notations for `Kind` operations. Retrieval and linking demonstrate constant time complexity, while creation and indexed operations show logarithmic behavior. Graph traversal and visualization, as expected, scale with the size of the graph. The `patch()` operation is shallow and costs only the direct links of the patched Kind. Understanding these complexities is crucial for designing efficient applications leveraging the `Kind` framework.
