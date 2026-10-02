# `«kind»` Tutorial
## An Introduction to Symbolic Modeling

### Abstract

This tutorial provides a comprehensive introduction to the `Kind` library, guiding users through its fundamental concepts and practical applications. Through a series of progressively complex examples drawn from diverse industries, we will demonstrate how `Kind` facilitates the creation of clear, maintainable, and extensible symbolic models. This document is designed for a broad audience, including software engineers, data scientists, and domain experts seeking to leverage symbolic representation in their projects.

### 1. Getting Started: Setup and Basic Kind Creation and Relationships

`Kind` is built around the concept of unique, interned symbolic entities. Every time you create a `Kind` with a given name, you get back the exact same object. This ensures consistency and efficiency.

Simply install kind with pip
```bash
# For generic everyday usage
python -m pip install kind

# for some graphical enhancements
python -m pip install kind[visual]

# for package or mixin development 
python -m pip install kind[dev]
```

#### 1.1. Creating Kinds

Kinds can be created directly or via the convenient `k` namespace.

```python

from core.kind_namespace import k
from kind.core.kind import Kind

# Direct creation
project_alpha = Kind("ProjectAlpha")
task_design = Kind("TaskDesign")

# Using the 'k' namespace (recommended for brevity)
project_beta = k.ProjectBeta
task_development = k.TaskDevelopment

print(f"Project Alpha: {project_alpha}")
print(f"Task Design: {task_design}")
print(f"Project Beta: {project_beta}")
print(f"Task Development: {task_development}")

# Interning in action: same name, same object
project_alpha_again = Kind("ProjectAlpha")
assert project_alpha is project_alpha_again
```
<details>
<summary>Outcome</summary>

```text
Project Alpha: <Kind: ProjectAlpha>
Task Design: <Kind: TaskDesign>
Project Beta: <Kind: ProjectBeta>
Task Development: <Kind: TaskDevelopment>
```
</details>

#### 1.2. Building Relationships: Parent-Child

Kinds can be linked to form directed graphs, representing relationships like parent-child, dependency, or containment. The `append()` method establishes a one-way link, automatically managing bidirectional references.

```python

from core.kind_namespace import k
from kind.core.kind import Kind
from kind.builtin import apply_builtins

apply_builtins()

# Example: Project Management (Business Services)
# Modeling project phases and tasks

project_alpha = Kind("ProjectAlpha")
task_design = Kind("TaskDesign")
task_development = k.TaskDevelopment

project_alpha.append(task_design)
project_alpha.append(task_development)

task_development.append(k.SubTaskCoding)
task_development.append(k.SubTaskTesting)

print(f"Children of {project_alpha}: {list(project_alpha.children)}")
print(f"Parents of {task_design}: {list(task_design.parents)}")

# Visualize the project structure
print(project_alpha.to_mmd())
```
<details>
<summary>Outcome</summary>

```text
Children of <Kind: ProjectAlpha>: [<Kind: TaskDesign>, <Kind: TaskDevelopment>]
Parents of <Kind: TaskDesign>: [<Kind: ProjectAlpha>]
graph TD
    ProjectAlpha --> TaskDesign
    ProjectAlpha --> TaskDevelopment
    TaskDevelopment --> SubTaskCoding
    TaskDevelopment --> SubTaskTesting
```
</details>

```mermaid
graph TD
    A[ProjectAlpha] --> B(TaskDesign)
    A --> C(TaskDevelopment)
    C --> D(SubTaskCoding)
    C --> E(SubTaskTesting)

    style A fill:#FF6347,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style B fill:#FF6347,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#FF6347,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style D fill:#FF6347,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#FF6347,stroke:#333,stroke-width:2px,color:#FFFFFF;
```

### 2. Extending Kind Functionality with Mixins

`Kind`'s power lies in its extensibility. You can dynamically add new behaviors and properties to `Kind` instances using mixins. This keeps the core `Kind` class lean while allowing for rich, domain-specific functionality.

#### 2.1. Enabling Built-in Mixins

The `apply_builtins()` function integrates a set of standard mixins, providing common functionalities like time dimension handling, indexing, and pathfinding.

```python

from kind.core.kind import Kind
from kind.builtin import apply_builtins

apply_builtins()

# Example: Telecommunications (Network Event Logging)
# Analyzing event timestamps

network_event_1 = Kind("2023-10-26T14:05:10Z_ConnectionDrop")
network_event_2 = Kind("2023-10-26T14:05:35Z_Reconnection")

print(f"Event 1 Datetime: {network_event_1.as_datetime}")
print(f"Event 2 Datetime: {network_event_2.as_datetime}")
print(f"Time difference: {network_event_2.as_datetime - network_event_1.as_datetime}")

# Visualize a timeline of events (conceptual, requires more complex Kind relationships)
# This would typically involve a series of events linked chronologically.
```
<details>
<summary>Outcome</summary>

```text
Event 1 Datetime: 2023-10-26 14:05:10
Event 2 Datetime: 2023-10-26 14:05:35
Time difference: 0:00:25
```
</details>

```mermaid
graph TD
    subgraph Network Events
        E1[2023-10-26T14:05:10Z_ConnectionDrop]
        E2[2023-10-26T14:05:35Z_Reconnection]
    end


    E1 -- occurs_before --> E2

    style E1 fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style E2 fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
```
#### 2.2. Pathfinding in Graphs

With the pathfinding mixin, you can easily find paths between connected Kinds, useful for dependency analysis or tracing flows.

```python

from core.kind_namespace import k
from kind.builtin import apply_builtins

apply_builtins()

# Example: Supply Chain Logistics (Transportation and Logistics)
# Tracing a product's journey through a supply chain

warehouse_a = k.WarehouseA
factory_b = k.FactoryB
distribution_c = k.DistributionCenterC
retail_d = k.RetailStoreD

warehouse_a.append(factory_b)
factory_b.append(distribution_c)
distribution_c.append(retail_d)

path = warehouse_a.path_to(retail_d)
print(f"Path from Warehouse A to Retail Store D: {[str(kind) for kind in path]}")

# Visualize the supply chain path
print(warehouse_a.to_mmd())
```
<details>
<summary>Outcome</summary>

```text
Path from Warehouse A to Retail Store D: ['<Kind: WarehouseA>', '<Kind: FactoryB>', '<Kind: DistributionCenterC>', '<Kind: RetailStoreD>']
graph TD
    WarehouseA --> FactoryB
    FactoryB --> DistributionCenterC
    DistributionCenterC --> RetailStoreD
```
</details>

```mermaid
graph LR
    W[WarehouseA] --> F(FactoryB)
    F --> D(DistributionCenterC)
    D --> R(RetailStoreD)

    style W fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF; 
    style F fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF; 
    style D fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF; 
    style R fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF; 
```

### 3. Advanced Concepts: Indexing and Custom Behaviors

`Kind` allows for more sophisticated data structures and custom logic to be integrated.

#### 3.1. Kind Indexing

The `KindIndex` allows you to create weighted, searchable indexes of Kinds, enabling efficient retrieval and rebalancing based on various strategies.

```python

from core.kind_namespace import k

# Example: Financial Portfolio Management (Asset and Wealth Management)
# Indexing assets by risk score

portfolio = k.MyInvestmentPortfolio

# Insert assets with their risk scores (weights)
portfolio.index.insert(k.StockA, 0.7)  # High risk
portfolio.index.insert(k.BondB, 0.2)  # Low risk
portfolio.index.insert(k.MutualFundC, 0.5)  # Medium risk

# Traverse in-order (by weight)
print(f"Assets by risk (in-order): {[str(kind) for kind in portfolio.index.traverse()]}")

```
<details>
<summary>Outcome</summary>

```text
Assets by risk (in-order): ['<Kind: BondB>', '<Kind: MutualFundC>', '<Kind: StockA>']
```
</details>

```mermaid
graph TD
    P[MyInvestmentPortfolio]
    P --> S1(StockA: 0.7)
    P --> B1(BondB: 0.2)
    P --> M1(MutualFundC: 0.5)

    style P fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style S1 fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style B1 fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style M1 fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
```

### Conclusion

This introduction has covered the core aspects of the `Kind` library, from basic creation and relationship building to leveraging built-in mixins for time dimension handling, pathfinding, and indexing. `Kind` provides a flexible and powerful foundation for modeling complex systems across various domains. For more in-depth exploration of advanced features and custom extensions, please refer to the Advanced Tutorial and API Documentation.

---
