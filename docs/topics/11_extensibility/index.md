# Extensibility: Adapting Kind to Diverse Domains

The `Kind` framework is designed with a strong emphasis on extensibility, allowing it to be adapted and integrated into a wide array of applications and domains. This extensibility is achieved through well-defined protocols, dynamic mixin capabilities, and compatibility with external data formats like enum reflections and Domain-Specific Languages (DSLs).

## `Kindable` Type for Robust Callable Integration

The `Kindable` protocol defines a clear contract for objects that can be seamlessly integrated into a `Kind` instance. By adhering to this protocol, external callable entities (functions, methods, or even classes with a `__call__` method) can be treated as first-class citizens within the `Kind` ecosystem. This promotes a clean separation of concerns, allowing complex behaviors to be encapsulated in external modules while still being accessible and manageable through `Kind`.

### Purpose and Usage
To ensure that any callable object can be consistently used within the `Kind` framework, particularly when dynamically attaching behaviors or processing data.

### Code Example
```python
from kind import Kind
from typing import Protocol, Any, Union, Awaitable
from kind.core.mixinability import register_mixin

# Define a custom Kindable class
class MyCustomAction(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Union[Any, Awaitable[Any]]:
        ...

class LogActionMixin:
    def log_message(self, message: str):
        print(f"[LOG] {message}")

class CalculateSumMixin:
    def calculate_sum(self, a: int, b: int) -> int:
        return a + b

# Register mixins
register_mixin(LogActionMixin, expand=True)
register_mixin(CalculateSumMixin, expand=True)

log_kind = Kind('Logger')
calc_kind = Kind('Calculator')

# Using the integrated Kindable objects
log_kind.log_message("Application started.")
result = calc_kind.calculate_sum(10, 20)
print(f"Calculation result: {result}")
```
<details>
<summary>Outcome</summary>

```text
[LOG] Application started.
Calculation result: 30
```
</details>

### Diagram
```mermaid
graph TD
    A[External Callable] --> B{Adheres to Kindable Protocol};
    B --> C[Can be Integrated];
    C --> D[Kind Instance];
    D -- "Executes" --> A;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `MixinFunction` Protocol for Formal Mixin Interface

The `MixinFunction` protocol provides a formal interface for defining mixin functions within the `Kind` framework. This protocol ensures that mixins conform to a predictable structure, especially concerning asynchronous operations and execution contexts (new processes or threads). By adhering to `MixinFunction`, developers can create robust and interoperable mixins that seamlessly extend `Kind`'s capabilities while maintaining system stability.

### Purpose and Usage
To define a standard for mixin functions, particularly those that might involve asynchronous operations or require specific execution environments.

### Code Example
```python
from kind import Kind
from kind.core.mixinability import register_mixin
from kind.core.protocols import MixinFunction
import asyncio

# A mixin function conforming to MixinFunction protocol
class AsyncDataFetcher(MixinFunction):
    async def __call__(self, url: str, new_process: bool = False, new_thread: bool = True) -> str:
        print(f"Fetching data from {url} in a new thread: {new_thread}, new process: {new_process}")
        await asyncio.sleep(0.1) # Simulate async I/O
        return f"Data from {url}"

# Register the mixin
register_mixin(AsyncDataFetcher, expand=True)

# Use the mixin
async def main():
    web_kind = Kind('WebResource')
    data = await web_kind.fetch_data("https://example.com")
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
```
<details>
<summary>Outcome</summary>

```text
Fetching data from https://example.com in a new thread: True, new process: False
Data from https://example.com
```
</details>

### Diagram
```mermaid
graph TD
    A[Mixin Function] --> B{Adheres to MixinFunction Protocol};
    B --> C[Supports Async/Await];
    B --> D[Handles new_process/new_thread];
    C --> E[Robust Mixin];
    D --> E;
    E --> F[Kind Extensibility];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## `KindAdapter` Mixinable Interface Enables Different Logical Structures

While not explicitly defined as a separate class in the provided code, the concept of a `KindAdapter` is implicitly supported through the framework's mixinability. This allows `Kind` instances to dynamically adopt different logical structures or behaviors, effectively acting as adapters for various data models or interaction patterns. By applying specific mixins, a generic `Kind` can be transformed to behave like a database record, a network endpoint, or a UI component, without altering its core identity.

### Purpose and Usage
To dynamically change the logical interpretation or behavior of a `Kind` instance by applying specific mixins. This enables a single `Kind` to represent different types of entities based on context.

### Code Example

```python
from kind import Kind
from kind.core.mixinability import register_mixin
from kind.builtin import apply_builtins


# Define mixins for different logical structures
class DatabaseRecordMixin:
    def save(self):
        print(f"Saving {self.name} as a database record.")

    def load(self):
        print(f"Loading {self.name} from database.")


class NetworkEndpointMixin:
    def send_request(self, data):
        print(f"Sending request from {self.name} with data: {data}")

    def receive_response(self):
        print(f"Receiving response for {self.name}.")


# Register mixins
register_mixin(DatabaseRecordMixin, expand=True)
register_mixin(NetworkEndpointMixin, expand=True)

apply_builtins()

# Create a kind and apply behaviors dynamically
db_entity = Kind('UserAccount')
db_entity.save()
db_entity.load()

network_node = Kind('API_Gateway')
network_node.send_request({"query": "status"})
network_node.receive_response()
```
<details>
<summary>Outcome</summary>

```text
Saving UserAccount as a database record.
Loading UserAccount from database. 
Sending request from API_Gateway with data: {'query': 'status'}
Receiving response for API_Gateway.
```
</details>

### Diagram
```mermaid
graph TD
    A[Generic Kind] --> B{Apply Mixin &#40Adapter&#41};
    B -- "DatabaseRecordMixin" --> C[Behaves as Database Record];
    B -- "NetworkEndpointMixin" --> D[Behaves as Network Endpoint];
    C --> E[Specific Operations];
    D --> E;

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## Compatible with Enum Reflection and External DSL Inputs

The `Kind` framework's extensibility extends to its compatibility with external data sources and declarative formats. It can seamlessly integrate with Python's `enum` types through reflection, allowing enumeration members to be directly converted into `Kind` instances. Furthermore, its flexible design enables the ingestion and interpretation of external Domain-Specific Language (DSL) inputs, facilitating the definition of complex symbolic structures and relationships using declarative syntax.

### Purpose and Usage
To easily convert `enum` members into `Kind` instances and to allow external DSLs to define `Kind` structures, enhancing interoperability and declarative modeling.

### Code Example

```python
from kind import Kind
import enum
from kind.builtin import apply_builtins

apply_builtins()


# Enum Reflection
class TrafficLight(enum.Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


# Convert enum members to Kinds
traffic_kinds = Kind.from_enum(TrafficLight)
for kind in traffic_kinds:
    print(f"Enum Kind: {kind.name}")


def parse_dsl(dsl_string: str):
    kinds = {}
    for line in dsl_string.split(','):
        parts = line.strip().split('->')
        if len(parts) == 2:
            source_name = parts[0].strip()
            target_name = parts[1].strip()
            source_kind = kinds.get(source_name, Kind(source_name))
            target_kind = kinds.get(target_name, Kind(target_name))
            source_kind.append(target_kind)
            kinds[source_name] = source_kind
            kinds[target_name] = target_kind
    return kinds


dsl_input = "user -> post, post -> comment, user -> like"
parsed_kinds = parse_dsl(dsl_input)

user_kind = parsed_kinds['user']
print("\nDSL-defined graph:")
for kind in user_kind.tree():
    print(kind.name)
```
<details>
<summary>Outcome</summary>

```text
Enum Kind: RED
Enum Kind: YELLOW
Enum Kind: GREEN

DSL-defined graph:
user
post
comment
like
```
</details>

### Diagram
```mermaid
graph TD
    A[Enum Type] --> B{Kind.from_enum&#40&#41};
    B --> C[Kind Instances];

    X[External DSL Input] --> Y{DSL Parser};
    Y --> Z[Kind Graph Construction];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;

    style X fill:#FF4500,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style Y fill:#8A2BE2,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style Z fill:#FF1493,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## Conclusion

The `Kind` framework's commitment to extensibility empowers developers to build highly adaptable and interoperable systems. By providing clear protocols for callable integration, formal interfaces for mixins, and seamless compatibility with external data formats, `Kind` facilitates the creation of flexible, domain-specific solutions that can evolve with changing requirements. This design philosophy ensures that `Kind` remains a versatile tool for a wide range of symbolic data manipulation tasks.

For a comprehensive overview of the Kind's extensibility, refer to the [Extensibility Overview Diagram](extensibility_overview.mmd).

--
