# 1.4 Per-Instance Indexing: Sophisticated Data Structuring

The `Kind` framework introduces the concept of **per-instance indexing**, where each `Kind` object possesses its own private, weighted index of other kinds. This advanced feature enables the creation and efficient management of sophisticated, nested data structures, moving beyond simple parent-child relationships to allow for more complex, context-specific associations.

## The `KindIndex` Mechanism

At the heart of per-instance indexing is the `KindIndex` class, located in `kind/builtin/index.py`. Each `Kind` instance gets its own `KindIndex` object, created lazily on first access to `kind.index` (see the `index` property in `kind/core/kind.py`); the index keeps its Kinds sorted by weight in an AVL tree. This `KindIndex` acts as a localized, internal data store for the `Kind`, allowing it to maintain a structured collection of references to other `Kind` instances, potentially with associated weights or metadata.

```mermaid
graph TD
    A[Kind Instance] --> B{KindIndex #40;Private#41;};
    B --> C[IndexNode 1];
    B --> D[IndexNode 2];
    B --> E[...];
    C -- "references" --> F[Other Kind];
    D -- "references" --> G[Another Kind];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style G fill:#00FFFF,stroke:#333,stroke-width:2px,color:#000000;
```
## Key Features and Benefits

-   **Private Context**: Each `Kind` can maintain its own unique view or organization of related kinds, independent of global relationships. This is crucial for modeling complex domains where relationships are highly contextual.
-   **Weighted Associations**: The ability to assign weights to indexed kinds allows for the representation of strength, relevance, or priority in relationships. This facilitates advanced algorithms for ranking, recommendation, or decision-making.
-   **Sophisticated Traversal and Querying**: With a dedicated index, a `Kind` can perform highly optimized local traversals and queries on its directly associated kinds, without needing to traverse the entire global graph.
-   **Nested Data Structures**: This feature enables the construction of hierarchical or nested data structures where a `Kind` can encapsulate a complex internal organization of other kinds.

### Code Example: Product Configuration with Weighted Features

Imagine a product configurator where a `Product` kind needs to index its `Features` with associated `weights` (e.g., importance, cost impact).

```python
from kind import Kind, k
from kind.builtin import apply_builtins

apply_builtins()

# Create product and feature kinds
product_laptop = k.Laptop
feature_ssd = k.SSD
feature_ram = k.RAM
feature_gpu = k.GPU

# The product's KindIndex is created on first access to product_laptop.index
importance = {feature_ssd: 0.8, feature_ram: 0.6, feature_gpu: 0.9}

# Insert features into the product's private index with weights
for feature, weight in importance.items():
    product_laptop.index.insert(feature, weight=weight)

# Traverse the product's index in weight order (the AVL tree stays balanced on insert)
print("Laptop features by importance:")
for feature_kind in product_laptop.index.traverse(order="in"):
    print(f"- {feature_kind.name} (Weight: {importance[feature_kind]})")
```
<details>
<summary>Outcome</summary>

```text
Laptop features by importance:
- RAM (Weight: 0.6)
- SSD (Weight: 0.8)
- GPU (Weight: 0.9)
```
</details>

### Industry Applications

**High-Tech: Recommendation Systems**

```python
from kind import k
from kind.builtin import apply_builtins

apply_builtins()

# User and Product kinds
user_alice = k.Alice
product_book = k.Book_A
product_movie = k.Movie_B

# User's private index of liked products with preference scores
user_alice.index.insert(product_book, weight=0.9)
user_alice.index.insert(product_movie, weight=0.7)

print(f"Alice's liked items: {[item.name for item in user_alice.index.traverse()]}")
```
<details>
<summary>Outcome</summary>

```text
Alice's liked items: ['Movie_B', 'Book_A']
```
</details>

**Low-Tech: Library Cataloging and Cross-Referencing**

```python
from kind import k
from kind.builtin import apply_builtins

apply_builtins()

# Book and Keyword kinds
book_history = k.History_of_Time
keyword_physics = k.Physics
keyword_cosmology = k.Cosmology

# Book's private index of keywords with relevance
book_history.index.insert(keyword_physics, weight=0.8)
book_history.index.insert(keyword_cosmology, weight=0.95)

print(f"Keywords for 'History of Time': {[kw.name for kw in book_history.index.traverse()]}")
```
<details>
<summary>Outcome</summary>

```text
Keywords for 'History of Time': ['Physics', 'Cosmology']
```
</details>

## Conclusion

Per-instance indexing significantly enhances the expressive power of the `Kind` framework. By providing each `Kind` with its own localized, weighted index, it facilitates the modeling of intricate, contextual relationships and the construction of sophisticated, nested data structures. This capability is paramount for applications requiring fine-grained control over symbolic associations and efficient, localized data retrieval.
