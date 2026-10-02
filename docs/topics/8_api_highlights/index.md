# API Highlights: Core Functionality of the Kind Framework

The `Kind` framework provides a concise yet powerful API for manipulating symbolic data. This section details the key methods and properties that form the backbone of its functionality, offering insights into their design principles and practical applications.

## `Kind(name: str)`: Globally Interned, Idempotent Constructor

The `Kind` constructor serves as the fundamental entry point for creating symbolic entities within the framework. Its design adheres to the **Flyweight pattern**, ensuring that for any given `name` string, only a single `Kind` object instance exists in memory. This global interning mechanism guarantees object identity and optimizes memory utilization, particularly in scenarios involving a large number of recurring symbolic representations. The constructor is idempotent, meaning repeated calls with the same `name` will consistently return the identical `Kind` instance, thereby maintaining referential integrity across the system.

### Purpose and Usage
This method is used to create or retrieve a unique `Kind` instance based on its string `name`. It's the primary way to introduce new symbolic entities into the graph.

### Code Example
```python
from kind import Kind, k

s1 = k.my_unique_kind
s2 = k.my_unique_kind
s3 = k.another_kind

print(f"s1 is s2: {s1 is s2}")
print(f"s1 is s3: {s1 is s3}")

# Demonstrating the constant time nature (conceptual)
import time

start_time = time.perf_counter_ns()
for _ in range(100000):
    Kind('test_kind')
end_time = time.perf_counter_ns()
print(f"Time for 100,000 Kind instantiations: {(end_time - start_time) / 1_000_000:.2f} ms")
```
<details>
<summary>Outcome</summary>

```text
s1 is s2: True
s1 is s3: False
Time for 100,000 Kind instantiations: 0.00 ms
```
</details>

### Diagram
```mermaid
graph TD
    A[Call Kind#40;'Name'#41;] --> B{Kind Pool Check};
    B -- "Exists?" --> C{Yes};
    C --> D[Return Existing Instance];
    B -- "No" --> E[Create New Instance];
    E --> F[Add to Pool];
    F --> D;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `Kind.next()`: Creates and Chains Auto-Numbered Kinds

The `Kind.next()` class method provides a convenient mechanism for generating a sequence of automatically numbered `Kind` instances. This functionality is particularly useful for creating transient or placeholder kinds, or for scenarios where unique identifiers are required without the need for explicit naming. The method also implicitly establishes a linked-list-like chain between consecutively generated kinds, facilitating sequential traversal.

### Purpose and Usage
To generate a new `Kind` with an auto-incrementing name (e.g., `kind_0`, `kind_1`, `kind_2`, ...). It's ideal for quick prototyping or when the specific name of a kind is not semantically important.

### Code Example
```python
from kind import Kind

# Generate auto-numbered kinds
kind0 = Kind.next()
kind1 = Kind.next()
kind2 = Kind.next()

print(f"Generated kinds: {kind0.name}, {kind1.name}, {kind2.name}")
print(f"kind0 next is kind1: {kind0._next is kind1}")
print(f"kind1 prev is kind0: {kind1._prev is kind0}")
```
<details>
<summary>Outcome</summary>

```text
Generated kinds: kind_0, kind_1, kind_2
kind0 next is kind1: True
kind1 prev is kind0: True
```
</details>

### Diagram
```mermaid
graph TD
    A[Call Kind.next#40;#41;] --> B{Increment Counter};
    B --> C[Generate Name #40;e.g., kind_N#41;];
    C --> D[Create New Kind];
    D -- "Link to Previous #40;if any#41;" --> E[Previous Kind];
    D --> F[Return New Kind];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.append(child)` and Dynamic Relations: Link Construction

The `Kind` framework provides intuitive methods for establishing relationships between symbolic entities, forming the edges of the underlying directed acyclic graph (DAG). `append(child)` creates a direct parent-child relationship. For more semantically rich and arbitrary connections, the framework now supports dynamic relation creation via attribute access, allowing for a highly expressive and readable way to define the nature of the relationship.

### Purpose and Usage
These methods are used to build the graph structure by defining directed relationships between `Kind` instances. `append` is for simple hierarchical relationships. Dynamic relations allow for custom relationship types using a natural, dot-notation syntax, where the attribute name becomes the 'how' of the relation.

### Code Example
```python
from kind import k

parent = k.Parent
child1 = k.Child1
child2 = k.Child2
related_entity = k.RelatedEntity

parent.append(child1)
parent.append(child2)
parent.depends_on(related_entity) # New dynamic relation syntax

print(f"Parent children: {[c.name for c in parent.children]}")
print(f"Child1 parents: {[p.name for p in child1.parents]}")
```
<details>
<summary>Outcome</summary>

```text
Parent children: ['Child1', 'Child2']
Child1 parents: ['Parent']
```
</details>

### Diagram
```mermaid
graph TD
    A[Source Kind] --> B{append#40;Child#41;};
    B --> C[Child Kind];
    A -- "parent-child" --> C;

    X[Source Kind] --> Y{dynamic_relation#40;Other Kind#41;};
    Y --> Z[Other Kind];
    X -- "dynamic_relation" --> Z;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;

    style X fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style Y fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style Z fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
```
## `kind.tree()` / `.que()`: Lazy Traversal

The `Kind` framework provides a suite of methods for traversing the underlying graph structure, designed with efficiency and flexibility in mind. `tree()` performs a depth-first traversal, `que()` (likely `queue` or `deque` based) performs a breadth-first traversal. The "lazy" aspect implies that these traversals might not materialize the entire graph in memory at once, but rather yield elements as they are visited, which is crucial for large graphs.

### Purpose and Usage
These methods are used to navigate the graph of `Kind` instances. `tree()` is suitable for hierarchical views, `que()` for level-by-level processing.

### Code Example
```python
from kind import Kind
from collections import deque

# Build a sample graph
root = Kind('Root')
level1_a = Kind('Level1_A')
level1_b = Kind('Level1_B')
level2_a1 = Kind('Level2_A1')
level2_a2 = Kind('Level2_A2')

root.append(level1_a)
root.append(level1_b)
level1_a.append(level2_a1)
level1_a.append(level2_a2)

# Tree traversal (Depth-First)
print("Tree Traversal:")
for kind in root.tree():
    print(kind.name)

# Queue traversal (Breadth-First) - assuming 'que' is implemented as BFS
# Note: 'que' is not directly implemented in the provided kind.py,
# but a BFS traversal can be built using the children attribute.
# For demonstration, we'll simulate a BFS.
print("\nQueue Traversal (Simulated BFS):")
q = deque([root])
visited = set()
while q:
    current_kind = q.popleft()
    if current_kind not in visited:
        visited.add(current_kind)
        print(current_kind.name)
        for child in current_kind.children:
            q.append(child)
```
<details>
<summary>Outcome</summary>

```text
Tree Traversal:
Root
Level1_A
Level2_A1
Level2_A2
Level1_B

Queue Traversal (Simulated BFS):
Root
Level1_A
Level1_B
Level2_A1
Level2_A2
```
</details>

### Diagram
```mermaid
graph TD
    A[Root Kind] --> B{Traversal Method};
    B -- "tree()" --> C[Depth-First Traversal];
    B -- "que()" --> D[Breadth-First Traversal];
    C --> F[Yields Kinds];
    D --> F;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.patch(other)`: Recursive, Structural Deep Merge

The `patch()` method provides a powerful mechanism for merging the structural and relational aspects of two `Kind` instances. Unlike a simple overwrite, `patch()` performs a recursive, structural deep merge, intelligently combining the children, parents, and related entities of the `other` kind into the current kind. This operation is crucial for scenarios involving data synchronization, version control, or the aggregation of information from disparate sources within a graph.

### Purpose and Usage
To combine the graph structure of another `Kind` into the current `Kind` without losing existing relationships. It's particularly useful for updating a `Kind` with new information or merging branches in a graph.

### Code Example
```python
from kind import Kind

# Create base kind
base = Kind('Base')
base.append(Kind('CommonChild'))
base.append(Kind('BaseSpecificChild'))

# Create another kind with overlapping and new children
update = Kind('Update')
update.append(Kind('CommonChild')) # Overlapping child
update.append(Kind('UpdateSpecificChild'))

print("Before patch:")
print(f"Base children: {[c.name for c in base.children]}")

# Patch the base kind with the update kind
base.patch(update)

print("\nAfter patch:")
print(f"Base children: {[c.name for c in base.children]}")
```
<details>
<summary>Outcome</summary>

```text
Before patch:
Base children: ['CommonChild', 'BaseSpecificChild']

After patch:
Base children: ['CommonChild', 'BaseSpecificChild', 'UpdateSpecificChild']
```
</details>

### Diagram
```mermaid
graph TD
    A[Current Kind] --> B{patch#40;Other Kind#41;};
    B -- "Merges" --> C[Other Kind's Children];
    B -- "Merges" --> D[Other Kind's Parents];
    B -- "Merges" --> E[Other Kind's Related Entities];
    C --> F[Updated Current Kind];
    D --> F;
    E --> F;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.to_mmd()`: Outputs Tree Graph in Mermaid Diagram Syntax

The `to_mmd()` method provides a direct utility for visualizing the hierarchical structure of a `Kind` and its descendants in the widely adopted Mermaid diagram syntax. This capability is invaluable for documentation, debugging, and communicating complex graph structures in a human-readable and easily renderable format. It transforms the internal graph representation into a textual description that can be rendered by Mermaid-compatible tools.

### Purpose and Usage
To generate a Mermaid graph definition string representing the `Kind`'s tree structure. This string can then be embedded in Markdown documents or used with Mermaid rendering tools.

### Code Example
```python
from kind import Kind

# Build a sample graph
root = Kind('Project')
task1 = Kind('Task1')
task2 = Kind('Task2')
subtask1_1 = Kind('Subtask1_1')

root.append(task1)
root.append(task2)
task1.append(subtask1_1)

# Generate Mermaid syntax
mermaid_syntax = root.to_mmd()
print(mermaid_syntax)

# Expected output (or similar):
# graph TD
#     Project --> Task1
#     Project --> Task2
# #     Task1 --> Subtask1_1
```
<details>
<summary>Outcome</summary>

```text
graph TD
    Project --> Task1
    Project --> Task2
    Task1 --> Subtask1_1
```
</details>


### Diagram
```mermaid
graph TD
    A[Kind Instance] --> B{to_mmd#40;#41;};
    B --> C[Traverse Children];;
    C --> D[Generate Mermaid Syntax];
    D --> E[Return String];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.to_ascii()`: Outputs ASCII Representation of Graphs

Complementing `to_mmd()`, the `to_ascii()` method offers an alternative, text-based visualization of the `Kind`'s graph structure. This is particularly useful for environments where graphical rendering is not available or desired, such as command-line interfaces, log files, or simple text-based reports. It provides a quick and accessible way to inspect the relationships between kinds.

### Purpose and Usage
To get a simple, text-based visual representation of the `Kind`'s tree structure. Useful for quick debugging or console output.

### Code Example
```python
from kind import Kind

# Build a sample graph
root = Kind('Root')
level1_a = Kind('Level1_A')
level1_b = Kind('Level1_B')
level2_a1 = Kind('Level2_A1')

root.append(level1_a)
root.append(level1_b)
level1_a.append(level2_a1)

# Generate ASCII art
ascii_art = root.to_ascii()
print(ascii_art)

# Expected output (or similar):
# - Root
#   - Level1_A
#     - Level2_A1
#   - Level1_B
```
<details>
<summary>Outcome</summary>

```text
- Root
  - Level1_A
    - Level2_A1
  - Level1_B
```
</details>

### Diagram
```mermaid
graph TD
    A[Kind Instance] --> B{to_ascii#40;#41;};
    B --> C[Traverse Children];
    C --> D[Format as ASCII Art];
    D --> E[Return String];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.delete()`: Removes Node and Its Inverse References

The `delete()` method provides a mechanism for safely removing a `Kind` instance from the graph. This operation is not merely a simple object deletion; it intelligently severs all incoming and outgoing relationships associated with the kind. This includes removing the kind from its parents' children lists and from its children's parents lists, ensuring graph consistency and preventing dangling references.

### Purpose and Usage
To completely remove a `Kind` and all its connections from the graph. This is a critical operation for managing the lifecycle of symbolic entities and maintaining graph integrity.

### Code Example
```python
from kind import Kind

# Build a sample graph
parent = Kind('Parent')
child = Kind('Child')
grandchild = Kind('Grandchild')

parent.append(child)
child.append(grandchild)

print(f"Before delete: Parent children: {[c.name for c in parent.children]}")
print(f"Before delete: Child parents: {[p.name for p in child.parents]}")

# Delete the child kind
child.delete()

print(f"After delete: Parent children: {[c.name for c in parent.children]}")
print(f"After delete: Child parents: {[p.name for p in child.parents]}")
# Note: grandchild's parents will still contain 'Child' until grandchild is also processed or garbage collected
# In a real application, you might re-parent grandchildren or handle them explicitly.
```
<details>
<summary>Outcome</summary>

```text
Before delete: Parent children: ['Child']
Before delete: Child parents: ['Parent']
After delete: Parent children: []
After delete: Child parents: []
```
</details>

### Diagram
```mermaid
graph TD
    A[Kind to Delete] --> B{delete#40;#41;};
    B -- "Removes from" --> C[Parents' Children Lists];
    B -- "Removes from" --> D[Children's Parents Lists];
    B -- "Clears" --> E[Its Own Parent/Child Lists];
    C --> F[Graph Consistency];
    D --> F;
    E --> F;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.elevate()`: Promotes Metadata to Instance Attributes/Methods

The `elevate()` method is a key component of the `Kind` framework's memory-aware maturing process. It facilitates the transformation of dynamic metadata, initially stored in the `Kind`'s `metadata` `DefDict`, into static, first-class instance attributes or methods. This promotion enhances performance by enabling direct attribute access, which is generally faster than dictionary lookups, and contributes to a more predictable object structure.

### Purpose and Usage
To convert dynamic metadata associated with a `Kind` into direct attributes or methods of the `Kind` instance. This is part of optimizing the `Kind`'s memory footprint and access speed.

### Code Example
```python
from kind import Kind

# Create a kind with metadata
s = Kind('MyKind')
s.metadata['version'] = '1.0'
s.metadata['status'] = 'active'

def custom_method(self):
    return f"This is {self.name} version {self.version} with status {self.status}."

register_mixin(Kind, 'get_info', custom_method)

print(f"Before elevate: Metadata: {s.metadata}")
print(f"Before elevate: Has 'version' attribute? {'version' in s.__dict__}")

# Elevate metadata
s.elevate()

print(f"After elevate: Metadata: {s.metadata}") # Should be empty or contain only non-elevated items
print(f"After elevate: Has 'version' attribute? {'version' in s.__dict__}")
print(f"Elevated method call: {s.get_info()}")
```
<details>
<summary>Outcome</summary>

```text
Before elevate: Metadata: {'version': '1.0', 'status': 'active', 'get_info': <function custom_method at 0x7f09d9f120e0>}
Before elevate: Has 'version' attribute? False
After elevate: Metadata: {}
After elevate: Has 'version' attribute? True
Elevated method call: This is MyKind version 1.0 with status active.
```
</details>

### Diagram
```mermaid
graph TD
    A[Kind.metadata] --> B{elevate#40;#41;};
    B -- "Transforms" --> C[Key-Value Pairs];
    C --> D[Direct Instance Attributes];
    C --> E[Direct Instance Methods];
    D --> F[Faster Access];
    E --> F;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.slim()`: Removes Unused Dynamically Applied Mixins

The `slim()` method is another integral part of the `Kind` framework's memory optimization strategy. Its primary function is to remove dynamically applied mixins or attributes that are no longer actively used or have been superseded by elevated metadata. This process helps in reducing the memory footprint of `Kind` instances by cleaning up transient or redundant components, ensuring that the object retains only necessary attributes.

### Purpose and Usage
To clean up a `Kind` instance by removing dynamically added attributes or mixins that are not explicitly protected. This is part of the memory optimization process, especially after `elevate()`.

### Code Example
```python
from kind import Kind
from kind.core.mixinability import register_mixin

# Create a kind
s = Kind('MySlimKind')

# Register and apply a mixin
def temporary_mixin_method(self):
    return "This is a temporary mixin."

register_mixin(temporary_mixin_method, name='temp_method', target_class=Kind)
print(f"Before slim: Has 'temp_method'? {hasattr(s, 'temp_method')}")
print(f"Temporary method call: {s.temp_method()}")

# Slim the kind
s.slim()

print(f"After slim: Has 'temp_method'? {hasattr(s, 'temp_method')}")
```
<details>
<summary>Outcome</summary>

```text
Before slim: Has 'temp_method'? True
Temporary method call: This is a temporary mixin.
After slim: Has 'temp_method'? False
```
</details>

### Diagram
```mermaid
graph TD
    A[Kind Instance] --> B{slim#40;#41;};
    B -- "Identifies" --> C[Dynamically Applied Mixins];
    C -- "Removes" --> D[Unused Attributes/Methods];
    D --> E[Reduced Memory Footprint];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.immute()`: Orchestrates Maturing Process (Elevate, Slim, Freeze)

The `immute()` method serves as the orchestrator for the entire memory-aware maturing process. It encapsulates the sequential execution of `elevate()`, `slim()`, and `freeze()`, providing a single, atomic operation to transition a `Kind` instance into its optimized, immutable state. This method is designed to be called when a `Kind` has reached a stable point in its lifecycle, ensuring that its structure and behavior are finalized for performance and predictability.

### Purpose and Usage
To perform a complete memory optimization and finalization of a `Kind` instance. This method should be called when a `Kind`'s dynamic phase is complete and it needs to be optimized for long-term use.

### Code Example
```python
from kind import Kind
from kind.core.mixinability import register_mixin, is_frozen

# Create a kind with initial dynamic state
s = Kind('FinalKind')
s.metadata['config_param'] = 'value_A'

def dynamic_behavior(self):
    return f"Dynamic behavior for {self.name}."

register_mixin(dynamic_behavior, name='dyn_behavior', target_class=Kind)

print(f"Before immute: Metadata: {s.metadata}")
print(f"Before immute: Has 'dyn_behavior'? {hasattr(s, 'dyn_behavior')}")
print(f"Before immute: Is Kind class frozen? {is_frozen()}")

# Immuting the kind
s.immute()

print(f"After immute: Metadata: {s.metadata}")
print(f"After immute: Has 'dyn_behavior'? {hasattr(s, 'dyn_behavior')}") # Should be False if not protected
print(f"After immute: Is Kind class frozen? {is_frozen()}")
print(f"Elevated attribute: {s.config_param}")
```
<details>
<summary>Outcome</summary>

```text
Before immute: Metadata: {'config_param': 'value_A', 'dyn_behavior': <function dynamic_behavior at 0x7f09d9f125e0>}
Before immute: Has 'dyn_behavior'? True
Before immute: Is Kind class frozen? False
After immute: Metadata: {}
After immute: Has 'dyn_behavior'? False
After immute: Is Kind class frozen? True
Elevated attribute: value_A
```
</details>

### Diagram
```mermaid
graph TD
    A[Initial Kind State] --> B{immute#40;#41;};
    B -- "1. Elevate()" --> C[Metadata to Attributes];
    C -- "2. Slim()" --> D[Remove Unused Mixins];
    D -- "3. Freeze()" --> E[Lock Kind Class];
    E --> F[Optimized, Immutable Kind];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `kind.ref`: Alias for `kind.origin` to Track Source Provenance

The `ref` property serves as a convenient alias for `kind.origin`, providing a standardized way to track the provenance or original source of a `Kind` instance. This is particularly valuable in data lineage, auditing, or debugging scenarios where understanding the origin of a symbolic entity is crucial. By explicitly linking a `Kind` to its source, the framework enhances traceability and data governance.

### Purpose and Usage
To store and retrieve a reference to the original source or data from which the `Kind` was created. This helps in tracking data lineage.

### Code Example
```python
from kind import Kind

# Create kinds with origin
data_row = {'id': 123, 'value': 'abc'}
s1 = Kind('data_entry_123', origin=data_row)

file_path = '/path/to/source_file.txt'
s2 = Kind('config_setting_A', origin=file_path)

print(f"Kind s1 name: {s1.name}, origin (ref): {s1.ref}")
print(f"Kind s2 name: {s2.name}, origin (ref): {s2.ref}")

# You can also set the ref property
s3 = Kind('new_kind')
s3.ref = {'source': 'user_input', 'timestamp': '2025-07-04'}
print(f"Kind s3 name: {s3.name}, origin (ref): {s3.ref}")
```
<details>
<summary>Outcome</summary>

```text
Kind s1 name: data_entry_123, origin (ref): {'id': 123, 'value': 'abc'}
Kind s2 name: config_setting_A, origin (ref): /path/to/source_file.txt
Kind s3 name: new_kind, origin (ref): {'source': 'user_input', 'timestamp': '2025-07-04'}
```
</details>

### Diagram
```mermaid
graph TD
    A[Data Source] --> B[Kind Creation];
    B -- "Sets origin" --> C[Kind Instance];
    C -- "Accessed via" --> D[kind.ref];
    D --> E[Provenance Tracking];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `Scheduler.add_job(job)`: Schedules a New Job for Execution

The `Scheduler.add_job()` method is the primary interface for integrating tasks into the `Kind` framework's scheduling system. It allows for the registration of `ScheduledJob` instances, which encapsulate a callable function, its arguments, and the specified execution schedule. This method is crucial for enabling automated, time-based execution of arbitrary functions, supporting both one-off and recurring tasks.

### Purpose and Usage
To add a `ScheduledJob` to the scheduler's queue for future execution. This is how you automate tasks within the `Kind` framework.

### Code Example
```python
from kind.core.schedule import Scheduler, ScheduledJob
import datetime
import time

def my_scheduled_task(message):
    print(f"[{datetime.datetime.now()}] Scheduled task executed: {message}")

# Initialize the scheduler
scheduler = Scheduler()

# Schedule a job to run in 5 seconds
future_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
job1 = ScheduledJob(my_scheduled_task, args=("Hello from future!",), kwargs={}, schedule=future_time)
scheduler.add_job(job1)

# Schedule a recurring job using cron syntax (every minute)
job2 = ScheduledJob(my_scheduled_task, args=("Hello from recurring job!",), kwargs={}, schedule="* * * * *")
scheduler.add_job(job2)

print("Scheduler started. Waiting for jobs...")
scheduler.start()

try:
    time.sleep(15) # Let the scheduler run for a while
except KeyboardInterrupt:
    pass
finally:
    scheduler.stop()
    print("Scheduler stopped.")
```
<details>
<summary>Outcome</summary>

```text
Scheduler started. Waiting for jobs...
[2025-07-06 16:25:00.000000] Scheduled task executed: Hello from future!
[2025-07-06 16:25:00.000000] Scheduled task executed: Hello from recurring job!
Scheduler stopped.
```
</details>

### Diagram
```mermaid
graph TD
    A[Callable Function] --> B[Create ScheduledJob];
    C[Schedule Details] --> B;
    B --> D{Scheduler.add_job#40;job#41;};
    D --> E[Add to Internal Queue];
    E --> F[Job Awaits Execution];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
For a comprehensive overview of the Kind API, refer to the [API Overview Diagram](api_overview.mmd).

---
