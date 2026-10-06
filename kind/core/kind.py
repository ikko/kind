"""This module defines Kind: an interned, name-identified graph node.

A Kind stands for a category as data. It has one identity per name (see BaseKind),
children and parents (a directed graph; cycles allowed), named relations with inverses, lazily created
metadata/context/index, attributes attached at runtime, and a per-instance freeze.
"""
import ast
import datetime
import hashlib
import inspect
import re
import sys
import warnings
import contextlib
import contextvars
from collections.abc import Mapping
from collections import deque
from itertools import chain
from sys import getsizeof
from typing import Any, Iterable, Iterator, Literal, Optional, Set, Type, TypeVar, Union

import orjson
import tomli_w
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10
    import tomli as tomllib

from kind.builtin.collections import OrderedKindSet
from kind.builtin.index import KindIndex
from kind.core.base_kind import BaseKind
from kind.core.space import KindSpace, SpaceError, current_space
from kind.core.graph_traversal import GraphTraversal
from kind.core.lazy_kind import SENTINEL, LazyKind
from kind.core.maturing import DefDict, _apply_merge_strategy
from kind.core.mixinability import get_applied_mixins
from kind.core.protocols import TIME_MIXINS
from kind.core.relations import Relations

T = TypeVar("T")
MergeStrategy = Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth']

INVERSE_PREFIX = "_inverse_"

# Mermaid node shapes: node_shape -> (opening, closing) around the label.
MERMAID_SHAPES = {
    "round": ("(", ")"),
    "stadium": ("([", "])"),
    "subroutine": ("[[", "]]"),
    "cylindrical": ("[(", ")]"),
    "circle": ("((", "))"),
    "double_circle": ("(((", ")))"),
    "asymmetric": (">", "]"),
    "rhombus": ("{", "}"),
    "hexagon": ("{{", "}}"),
    "parallelogram": ("[/", "/]"),
    "parallelogram_alt": ("[\\", "\\]"),
    "trapezoid": ("[/", "\\]"),
    "trapezoid_alt": ("[\\", "/]"),
}
DEFAULT_SHAPE = ("[", "]")

# Mermaid ids and labels. A plain name (letters, digits, `_`, spaces) keeps the id `name` with
# spaces as `_` and an unquoted label. Any other name, a plain name whose id is taken ("A B"
# vs "A_B"), and the reserved word `end` get a stable hash suffix; unsafe labels are quoted with
# `#`, `"` and newlines written as Mermaid entity codes.
_MMD_PLAIN = re.compile(r'[A-Za-z0-9_ ]+')
MMD_ESCAPES = (("#", "#35;"), ('"', "#quot;"), ("\n", "#10;"))


def _mmd_ids(kinds: Iterable['Kind']) -> dict['Kind', str]:
    """One Mermaid node id per Kind, unique and stable across runs."""
    ids: dict['Kind', str] = {}
    taken = {"end"}
    exact_first = sorted(kinds, key=lambda kind: (kind.name.replace(" ", "_") != kind.name, kind.name))
    for kind in exact_first:
        node_id = kind.name.replace(" ", "_") if _MMD_PLAIN.fullmatch(kind.name) else ""
        if not node_id or node_id in taken:
            base = re.sub(r'\W', '_', kind.name, flags=re.ASCII)
            digest = hashlib.sha256(kind.name.encode()).hexdigest()
            length = 6
            node_id = f"{base}_{digest[:length]}"
            while node_id in taken:
                length += 2
                node_id = f"{base}_{digest[:length]}"
        ids[kind] = node_id
        taken.add(node_id)
    return ids


def _mmd_label(name: str) -> str:
    if _MMD_PLAIN.fullmatch(name):
        return name
    for raw, code in MMD_ESCAPES:
        name = name.replace(raw, code)
    return f'"{name}"'

# Slots that make up a Kind's identity and place in the graph: never set from metadata.
STRUCTURAL_SLOTS = frozenset({'name', 'parents', 'children', '_position', '_next', '_prev', '_space'})


def _is_settable(class_attribute: Any) -> bool:
    """True for slots and properties with a setter: the class-level attributes an instance may set."""
    if isinstance(class_attribute, property):
        return class_attribute.fset is not None
    return inspect.ismemberdescriptor(class_attribute)


_EDITING: contextvars.ContextVar[bool] = contextvars.ContextVar("kind_editing", default=False)


@contextlib.contextmanager
def _internal_edit():
    """Marks a Kind method changing edge sets; outside it, the sets refuse changes."""
    token = _EDITING.set(True)
    try:
        yield
    finally:
        _EDITING.reset(token)


class _SettledMapping(Mapping):
    """metadata/context of a frozen Kind or a closed space: reading never creates a key,
    writing raises the same error as any other change. Nested values stay mutable."""

    def __init__(self, mapping: Any, owner: 'Kind'):
        self._mapping, self._owner = mapping, owner

    def __getitem__(self, key: Any) -> Any:
        if key in self._mapping:  # never through DefDict.__missing__, which would insert the key
            return self._mapping[key]
        raise KeyError(key)

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self) -> int:
        return len(self._mapping)

    def __setitem__(self, key: Any, value: Any) -> None:
        self._owner._ensure_mutable()

    def __delitem__(self, key: Any) -> None:
        self._owner._ensure_mutable()

    def __repr__(self) -> str:
        return f"{type(self._mapping).__name__}(settled, {dict(self._mapping)!r})"


class FrozenKindError(AttributeError):
    """Raised when a frozen Kind is asked to change."""


class Kind(BaseKind):
    __slots__ = (
        '_index',
        '_metadata',
        '_context',
        '_elevated_attributes',
        '_relations',
        '_frozen',
    )

    def _init_slots(self, name: str, origin: Optional[Any], space: KindSpace) -> None:
        super()._init_slots(name, origin, space)
        set_slot = object.__setattr__
        set_slot(self, 'parents', OrderedKindSet(guard=self._guard_edge_set))
        set_slot(self, 'children', OrderedKindSet(guard=self._guard_edge_set))
        set_slot(self, '_elevated_attributes', {})
        set_slot(self, '_index', SENTINEL)
        set_slot(self, '_metadata', SENTINEL)
        set_slot(self, '_context', SENTINEL)
        set_slot(self, '_relations', SENTINEL)
        set_slot(self, '_frozen', False)

    # --- lazily created parts ----------------------------------------------

    @property
    def index(self) -> KindIndex:
        if self._index is SENTINEL:
            object.__setattr__(self, '_index', KindIndex(self))
        return self._index

    @property
    def metadata(self) -> Any:
        """A DefDict; read-only (top level) once the Kind is frozen or its space is closed."""
        if self._metadata is SENTINEL:
            object.__setattr__(self, '_metadata', DefDict())
        return self._read_only_if_settled(self._metadata)

    @property
    def context(self) -> Any:
        """A DefDict; read-only (top level) once the Kind is frozen or its space is closed."""
        if self._context is SENTINEL:
            object.__setattr__(self, '_context', DefDict())
        return self._read_only_if_settled(self._context)

    def _read_only_if_settled(self, mapping: DefDict) -> Any:
        return _SettledMapping(mapping, self) if self._frozen or self._space.closed else mapping

    @property
    def relations(self) -> Relations:
        if self._relations is SENTINEL:
            object.__setattr__(self, '_relations', Relations(self))
        return self._relations

    @property
    def ref(self) -> Optional[Any]:
        """Alias for .origin: the source this Kind was made from."""
        return self.origin

    @ref.setter
    def ref(self, value: Any) -> None:
        self.origin = value

    # --- attribute protocol ------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """Elevated attributes first; any other public name is a dynamic relation verb.

        `a.has_kind(b)` relates a to b with how='has_kind'. Private names and names the
        class defines (e.g. a property whose getter failed) raise AttributeError instead.
        """
        try:
            elevated = object.__getattribute__(self, '_elevated_attributes')
        except AttributeError:
            raise AttributeError(name) from None
        if name in elevated:
            return elevated[name]
        if name.startswith('_') or hasattr(type(self), name):
            raise AttributeError(f"{type(self).__name__} {self.name!r} has no attribute {name!r}")
        if name in TIME_MIXINS:
            raise AttributeError(f"{name!r} is a time property, and time is opt-in. Hint: `import kind.time`.")
        return getattr(self.relations, name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._ensure_mutable()
        if name in STRUCTURAL_SLOTS:
            raise AttributeError(f"{name!r} is part of Kind {self.name!r}'s identity or structure and cannot be "
                                 f"assigned. Hint: use append/insert/relate/delete to change edges; a different "
                                 f"name is a different Kind.")
        if _is_settable(getattr(type(self), name, None)):
            object.__setattr__(self, name, value)
        else:
            self._elevated_attributes[name] = value

    def __delattr__(self, name: str) -> None:
        self._ensure_mutable()
        if name in STRUCTURAL_SLOTS:
            raise AttributeError(f"{name!r} is part of Kind {self.name!r}'s identity or structure and cannot be deleted.")
        if name in self._elevated_attributes:
            del self._elevated_attributes[name]
        else:
            object.__delattr__(self, name)

    # --- freezing ----------------------------------------------------------

    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> 'Kind':
        """Makes this Kind immutable: no attribute, edge or relation changes on it afterwards."""
        object.__setattr__(self, '_frozen', True)
        return self

    def _guard_edge_set(self) -> None:
        """Run by children/parents/relation sets before a change: only Kind's own edge methods may
        change them, because those keep both ends of every edge in step."""
        if not _EDITING.get():
            raise AttributeError(f"The edge sets of Kind {self.name!r} change only through append, insert, relate, "
                                 f"unrelate, reparent and delete, which keep both ends of every edge. "
                                 f"Hint: call one of those instead of changing children/parents/relations directly.")
        self._ensure_mutable()

    def _ensure_mutable(self) -> None:
        if object.__getattribute__(self, '_space').closed:
            raise SpaceError(f"Kind {self.name!r} belongs to a closed space; it can be read but not changed.")
        if object.__getattribute__(self, '_frozen'):
            raise FrozenKindError(f"Kind {self.name!r} is frozen (immute()/freeze()); it cannot change. "
                                  f"Hint: change it before maturing, or build a new Kind.")

    # --- graph construction ------------------------------------------------

    def _same_space(self, other: 'Kind') -> None:
        for end in (self, other):
            if end._space.closed:
                raise SpaceError(f"Kind {end.name!r} belongs to a closed space; it can be read but not changed.")
        if other._space is not self._space:
            raise SpaceError(f"Cannot link {self.name!r} in {self._space!r} to {other.name!r} in {other._space!r}: "
                             f"an edge across spaces would make their lifetimes undefined. "
                             f"Hint: create both inside the same `with KindSpace():` block.")

    @classmethod
    def _coerce(cls, value: Any) -> 'Kind':
        if isinstance(value, Kind):
            return value
        if isinstance(value, LazyKind):
            return value.evaluate()
        return cls.from_object(value)

    def append(self, child: Any) -> 'Kind':
        """Links `child` under this Kind (idempotent) and returns the child."""
        child = self._coerce(child)
        self._same_space(child)
        with self._lock, _internal_edit():
            self._ensure_mutable()
            child._ensure_mutable()
            self.children.add(child)
            child.parents.add(self)
        return child

    def add(self, child: Any) -> 'Kind':
        """Like append, but returns self, so calls can be chained."""
        self.append(child)
        return self

    def insert(self, child: Any, at: Optional[int] = None) -> 'Kind':
        """Places `child` at index `at` among the children (moving it if already there)."""
        child = self._coerce(child)
        self._same_space(child)
        with self._lock, _internal_edit():
            self._ensure_mutable()
            child._ensure_mutable()
            self.children.discard(child)
            self.children.insert(len(self.children) if at is None else at, child)
            child.parents.add(self)
        return self

    def _ensure_all_mutable(self, kinds: Iterable['Kind']) -> None:
        """Checks every Kind an operation will change *before* changing any, so a refusal
        never leaves a half-applied edit."""
        for kind in kinds:
            kind._ensure_mutable()

    def reparent(self) -> None:
        """Detaches this Kind from the hierarchy, linking each of its children to each of its parents.

        Afterwards this Kind has no parents and no children, and every edge exists on both ends.
        A self-loop is dropped with the rest of this Kind's edges.
        """
        with self._lock, _internal_edit():
            parents = [parent for parent in self.parents if parent is not self]
            children = [child for child in self.children if child is not self]
            self._ensure_all_mutable([self, *parents, *children])
            for parent in parents:
                parent.children.discard(self)
                for child in children:
                    parent.children.add(child)
                    child.parents.add(parent)
            for child in children:
                child.parents.discard(self)
            self.parents.clear()
            self.children.clear()

    def rebind_linear_sequence(self) -> None:
        """Removes this Kind from the Kind.next() chain, joining its neighbours."""
        with self._lock:
            if self._prev is not None:
                object.__setattr__(self._prev, '_next', self._next)
            if self._next is not None:
                object.__setattr__(self._next, '_prev', self._prev)
            object.__setattr__(self, '_prev', None)
            object.__setattr__(self, '_next', None)

    def delete(self) -> None:
        """Removes this Kind from the graph and the pool; its children move up to its parents."""
        with self._lock, _internal_edit():
            related = [k for _, kinds in self.relations.items() for k in kinds]
            self._ensure_all_mutable([self, *self.parents, *self.children, *related])
            self.reparent()
            self.rebind_linear_sequence()
            if self._index is not SENTINEL:
                self._index.remove(self)
            for how, related_kinds in list(self.relations.items()):
                for related_kind in list(related_kinds):
                    if how.startswith(INVERSE_PREFIX):
                        related_kind.unrelate(self, how=how[len(INVERSE_PREFIX):])
                    else:
                        self.unrelate(related_kind, how=how)
            self._space.order.remove(self._position, self)
            if self._space.pool.get(self.name) is self:
                del self._space.pool[self.name]

    def pop(self) -> 'Kind':
        """Deletes this Kind (re-parenting its children) and returns it."""
        self.delete()
        return self

    def popleft(self) -> Optional['Kind']:
        """Deletes and returns the first child, or None."""
        if not self.children:
            return None
        child = self.children[0]
        child.delete()
        return child

    # --- traversal and rendering -------------------------------------------

    def graph(self) -> list['Kind']:
        return GraphTraversal(self, traverse_mode='dfs').traverse()

    def tree(self) -> list['Kind']:
        """This Kind and its descendants, depth first."""
        return GraphTraversal(self, traverse_mode='dfs', family_mode='children_only').traverse()

    def _snapshot(self) -> tuple[list['Kind'], list['Kind'], list[tuple[str, list['Kind']]]]:
        """Children, parents and relations copied under the space lock, so a read never iterates
        a collection another thread is changing."""
        with self._lock:
            relations = [] if self._relations is SENTINEL else \
                [(how, list(kinds)) for how, kinds in list(self._relations.items())]
            return list(self.children), list(self.parents), relations

    def _outgoing(self) -> Iterator[tuple['Kind', str]]:
        """Child edges (how='') then forward relations, in a deterministic order."""
        children, _, relations = self._snapshot()
        for child in children:
            yield child, ""
        for how, related_kinds in relations:
            if not how.startswith(INVERSE_PREFIX):
                for related_kind in sorted(related_kinds, key=lambda k: k.name):
                    yield related_kind, how

    def to_mmd(self) -> str:
        """Mermaid flowchart of everything reachable through children and relations."""
        links: list[tuple['Kind', str, 'Kind']] = []
        visited = {self}
        stack = [self._outgoing()]
        owners = [self]
        while stack:
            edge = next(stack[-1], None)
            if edge is None:
                stack.pop()
                owners.pop()
                continue
            target, how = edge
            links.append((owners[-1], how, target))
            if target not in visited:
                visited.add(target)
                stack.append(target._outgoing())
                owners.append(target)

        ids = _mmd_ids(visited)
        edges = [f"    {ids[owner]} {'-->' if not how else f'-- {how} -->'} {ids[target]}"
                 for owner, how, target in links]

        def declaration(kind: 'Kind') -> str:
            opening, closing = MERMAID_SHAPES.get(kind.node_shape or "", DEFAULT_SHAPE)
            return f"{ids[kind]}{opening}{_mmd_label(kind.name)}{closing}"

        declarations = sorted({declaration(kind) for kind in visited})
        return "\n".join(["graph LR", *declarations, *dict.fromkeys(edges)])

    def to_ascii(self, traverse_mode: Literal["dfs", "bfs"] = "dfs",
                 family_mode: Literal["children_first", "parents_first"] = "children_first") -> str:
        """Indented outline of the graph, then its relations; from_ascii() reads back "dfs" output exactly."""
        return GraphTraversal(self, traverse_mode=traverse_mode, family_mode=family_mode).to_ascii()

    # --- serialization -----------------------------------------------------

    def _component(self) -> list['Kind']:
        """Every Kind connected to this one by children, parents or relations (either direction)."""
        seen, queue = {self}, deque([self])
        while queue:
            kind = queue.popleft()
            children, parents, relations = kind._snapshot()
            neighbours = chain(children, parents, *(related for _, related in relations))
            for neighbour in neighbours:
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return sorted(seen, key=lambda kind: kind.name)

    def _graph_dump(self) -> list[dict]:
        nodes = []
        for kind in self._component():
            children, _, relations = kind._snapshot()
            nodes.append({
                "name": kind.name,
                "children": [child.name for child in children],
                "relations": {how: sorted(related.name for related in related_kinds)
                              for how, related_kinds in relations if not how.startswith(INVERSE_PREFIX)},
            })
        return nodes

    @classmethod
    def _graph_load(cls, nodes: list[dict], source: str) -> 'Kind':
        """Builds (or merges into, by name) the Kinds described by `nodes`; returns a root.

        Names are interned: a node named like an existing Kind extends that Kind.
        """
        if not isinstance(nodes, list):
            raise ValueError(f"{source} input must be a list of nodes, got {type(nodes).__name__}. "
                             f"Hint: produce it with to_{source.lower()}().")
        if not nodes:
            raise ValueError(f"No kinds found in the {source} input.")
        for position, node in enumerate(nodes):
            if not isinstance(node, dict) or not isinstance(node.get("name"), str) \
                    or not isinstance(node.get("children", []), list) or not isinstance(node.get("relations", {}), dict):
                raise ValueError(f"{source} node {position} is not {{'name': str, 'children': [str], "
                                 f"'relations': {{how: [str]}}}}: {node!r}. Hint: produce it with to_{source.lower()}().")
        kinds = {node["name"]: cls(node["name"]) for node in nodes}
        for node in nodes:
            current = kinds[node["name"]]
            for child_name in node.get("children", []):
                if child_name in kinds:
                    current.append(kinds[child_name])
            for how, related_names in node.get("relations", {}).items():
                for related_name in related_names:
                    if related_name in kinds:
                        current.relate(kinds[related_name], how=how)
        return cls._pick_root(kinds.values())

    @staticmethod
    def _pick_root(kinds: Iterable['Kind']) -> 'Kind':
        """The first Kind (by name) that no other parsed Kind points to; else the first by name."""
        kinds = sorted(kinds, key=lambda kind: kind.name)
        targets = {target for kind in kinds for target, _ in kind._outgoing()}
        return next((kind for kind in kinds if kind not in targets), kinds[0])

    def to_json(self) -> str:
        return orjson.dumps(self._graph_dump(), option=orjson.OPT_INDENT_2).decode("utf-8")

    @classmethod
    def from_json(cls, json_string: str) -> 'Kind':
        return cls._graph_load(orjson.loads(json_string), "JSON")

    def to_yaml(self) -> str:
        return yaml.safe_dump(self._graph_dump(), sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_string: str) -> 'Kind':
        return cls._graph_load(yaml.safe_load(yaml_string) or [], "YAML")

    def to_toml(self) -> str:
        return tomli_w.dumps({"kinds": self._graph_dump()})  # TOML needs a key above a list of tables

    @classmethod
    def from_toml(cls, toml_string: str) -> 'Kind':
        return cls._graph_load(tomllib.loads(toml_string).get("kinds", []), "TOML")

    @classmethod
    def from_ascii(cls, ascii_string: str) -> 'Kind':
        """Rebuilds a graph from the output of to_ascii(); returns the Kind on the first line.

        `- name` under a line is a child of that line's Kind, `^ name` a parent; a repeated
        name is the same Kind (it records one more edge).
        """
        kinds: dict[str, Kind] = {}
        parent_stack: list[tuple[int, Kind]] = []
        in_relations = False
        for line in ascii_string.strip().split('\n'):
            if line.strip() == "--- Relations ---":
                in_relations = True
                continue
            if in_relations:
                relation = re.match(r'^(.+) --(.+)--> (.+)$', line.strip())
                if relation:
                    source, how, target = relation.groups()
                    source_kind = kinds.setdefault(source, cls(source))
                    source_kind.relate(kinds.setdefault(target, cls(target)), how=how)
                continue
            node = re.match(r'^(\s*)([-^]) (.+)$', line)
            if not node:
                continue
            indent, marker, name = len(node.group(1)), node.group(2), node.group(3)
            kind = kinds.setdefault(name, cls(name))
            while parent_stack and parent_stack[-1][0] >= indent:
                parent_stack.pop()
            if parent_stack:
                anchor = parent_stack[-1][1]
                if marker == "-":
                    anchor.append(kind)
                else:
                    kind.append(anchor)
            parent_stack.append((indent, kind))
        if not kinds:
            raise ValueError("No kinds found in the ASCII input.")
        return next(iter(kinds.values()))

    # --- relations ---------------------------------------------------------

    def patch(self, other: 'Kind') -> 'Kind':
        """Merges another Kind's origin (if unset), children, parents and relations into this one."""
        self._ensure_all_mutable([self, *other.children, *other.parents,
                                  *(k for how, ks in other.relations.items() if not how.startswith(INVERSE_PREFIX)
                                    for k in ks)])
        if other.origin is not None and self.origin is None:
            self.origin = other.origin
        for child in list(other.children):
            self.append(child)
        for parent in list(other.parents):
            parent.append(self)
        for how, related_kinds in list(other.relations.items()):
            if not how.startswith(INVERSE_PREFIX):
                for related_kind in list(related_kinds):
                    self.relate(related_kind, how=how)
        return self

    def relate(self, other: 'Kind', how: str = 'related') -> 'Kind':
        """Relates this Kind to `other` under `how`, recording the inverse on `other`."""
        self._same_space(other)
        with self._lock, _internal_edit():
            self._ensure_mutable()
            other._ensure_mutable()
            self.relations.add(how, other)
            other.relations.add(f"{INVERSE_PREFIX}{how}", self)
        return self

    def unrelate(self, other: 'Kind', how: Optional[str] = None) -> 'Kind':
        """Removes the relation(s) to `other`: one `how`, or all of them."""
        with self._lock, _internal_edit():
            self._ensure_all_mutable([self, other])
            hows = [how] if how is not None else [h for h, kinds in self.relations.items()
                                                  if other in kinds and not h.startswith(INVERSE_PREFIX)]
            for h in hows:
                self.relations.remove(h, other)
                other.relations.remove(f"{INVERSE_PREFIX}{h}", self)
        return self

    # --- the Kind.next() sequence and creation order -----------------------

    def head(self, not_before: Optional[float] = None) -> 'BaseKind':
        """The first Kind of this Kind's Kind.next() chain, or the earliest one at or after `not_before`."""
        cur: BaseKind = self
        while cur._prev and (not_before is None or cur._prev._position >= not_before):
            cur = cur._prev
        return cur

    def tail(self, not_after: Optional[float] = None) -> 'BaseKind':
        """The last Kind of this Kind's Kind.next() chain, or the latest one at or before `not_after`."""
        cur: BaseKind = self
        while cur._next and (not_after is None or cur._next._position <= not_after):
            cur = cur._next
        return cur

    @classmethod
    def auto_date(cls) -> 'Kind':
        return cls(datetime.date.today().isoformat())

    @classmethod
    def auto_datetime(cls) -> 'Kind':
        return cls(datetime.datetime.now().isoformat())

    @classmethod
    def auto_time(cls) -> 'Kind':
        return cls(datetime.datetime.now().time().isoformat())

    @classmethod
    def next(cls) -> 'Kind':
        """Creates kind_<n> and chains it after the previous Kind.next() result."""
        space = current_space()
        with space.lock:
            previous = space.pool.get(f"kind_{space._auto_counter - 1}")
            kind = cls(f"kind_{space._auto_counter}")
            space._auto_counter += 1
            if previous is not None:
                object.__setattr__(previous, '_next', kind)
                object.__setattr__(kind, '_prev', previous)
        return kind

    @classmethod
    def first(cls) -> Optional['Kind']:
        """The earliest created Kind in the current space."""
        node = current_space().order.min_node()
        return node.kind if node else None

    @classmethod
    def last(cls) -> Optional['Kind']:
        """The most recently created Kind in the current space."""
        node = current_space().order.max_node()
        return node.kind if node else None

    @classmethod
    def len(cls) -> int:
        """The number of Kinds in the current space."""
        return len(current_space())

    @classmethod
    def forget(cls, name: str) -> bool:
        """Deletes the Kind called `name` if there is one; returns whether there was."""
        kind = current_space().get(name)
        if kind is None:
            return False
        kind.delete()
        return True

    @classmethod
    def seek(cls, pos: float) -> Optional['Kind']:
        """The Kind created at position `pos`, or None."""
        return current_space().order.search(pos)

    @classmethod
    def each(cls, start: Union[float, 'Kind', None] = None) -> Iterator['Kind']:
        """Kinds in creation order, optionally from a position or a Kind on."""
        if start is not None and not isinstance(start, (int, float, Kind)):
            raise TypeError(f"Invalid start parameter {start!r} of type {type(start).__name__} in each()")
        start_weight = start._position if isinstance(start, Kind) else start
        yield from current_space().order.traverse_inorder(start_weight)

    # --- conversion --------------------------------------------------------

    @classmethod
    def from_object(cls, obj: Any) -> 'Kind':
        """Converts a value to a Kind.

        Scalars become the Kind of their text (`123` -> Kind('123')). A container becomes
        the Kind of its canonical content (`[1, 2]` -> Kind('[1, 2]'); dict keys and set
        members sorted) with its items as children and a `has_kind` relation to the
        container's kind (Kind('list')). Equal values mean the same Kind, as for any name.
        """
        if isinstance(obj, Kind):
            return obj
        if isinstance(obj, LazyKind):
            return obj.evaluate()
        if isinstance(obj, (list, tuple, set, frozenset, dict)):
            return cls._from_container(obj)
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return cls(obj if isinstance(obj, str) else str(obj), origin=obj)
        try:
            return cls(orjson.dumps(obj).decode(), origin=obj)
        except (TypeError, orjson.JSONEncodeError) as error:
            raise TypeError(f"Cannot convert {type(obj).__name__} to Kind: {error}. "
                            f"Hint: give the object a JSON-serializable form, or pass its name.") from None

    @classmethod
    def _from_container(cls, value: Union[list, tuple, set, frozenset, dict]) -> 'Kind':
        items = sorted(value, key=canonical_repr) if isinstance(value, (set, frozenset)) else value
        kind = cls(canonical_repr(value), origin=value)
        if isinstance(value, dict):
            for key, val in value.items():
                kind.append(key).append(val)
        else:
            for item in items:
                kind.append(item)
        kind.relate(cls(type(value).__name__), how='has_kind')
        return kind

    def to(self, target_type: Type[T]) -> T:
        """Converts the Kind's name back to a value of `target_type`.

        The name is read as JSON, or else as a Python literal (`ast.literal_eval`, which evaluates
        no code), so the names `from_object` produces — `'True'`, `'None'`, `"{'a': 1}"` — convert back.
        """
        if target_type is str:
            return self.name  # type: ignore[return-value]  # T is str here
        try:
            value = orjson.loads(self.name)
        except orjson.JSONDecodeError:
            try:
                value = ast.literal_eval(self.name)
            except (ValueError, SyntaxError):
                raise TypeError(f"Cannot convert Kind '{self.name}' to {target_type.__name__}: the name is neither "
                                f"JSON nor a Python literal.") from None
        converter: Any = target_type
        return value if isinstance(value, target_type) else converter(value)

    def each_parents(self) -> Iterator['Kind']:
        return iter(self.parents)

    def each_children(self) -> Iterator['Kind']:
        return iter(self.children)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    # --- maturing: elevate, slim, immute -----------------------------------

    def elevate(self, merge_strategy: MergeStrategy = 'smooth') -> Set[str]:
        """Moves metadata entries onto the Kind as attributes; returns the keys moved.

        A key naming a Kind method or property cannot be elevated (the class attribute
        would hide it) and stays in metadata with a warning.
        """
        self._ensure_mutable()
        elevated = set()
        for key, value in list(self.metadata.items()):
            class_attribute = getattr(type(self), key, None)
            if key in STRUCTURAL_SLOTS or key.startswith('_'):
                warnings.warn(f"Cannot elevate '{key}' on Kind {self.name!r}: it is part of its identity or structure.")
                continue
            if class_attribute is not None and not _is_settable(class_attribute):
                warnings.warn(f"Cannot elevate '{key}' on Kind {self.name!r}: it is a Kind method or read-only property.")
                continue
            if class_attribute is not None:
                current = getattr(self, key)
            else:
                current = self._elevated_attributes.get(key)
            merged = value if current is None else _apply_merge_strategy(current, value, merge_strategy)
            setattr(self, key, merged)
            del self.metadata[key]
            elevated.add(key)
        return elevated

    def slim(self, protected_attributes: Optional[Set[str]] = None) -> None:
        """Drops elevated attributes that hold no value (SENTINEL) unless protected."""
        self._ensure_mutable()
        protected = protected_attributes or set()
        for name in [name for name, value in self._elevated_attributes.items()
                     if value is SENTINEL and name not in protected]:
            del self._elevated_attributes[name]

    def immute(self, merge_strategy: MergeStrategy = 'smooth') -> 'Kind':
        """Matures this Kind: elevate metadata, slim, then freeze it."""
        if self._frozen:
            return self
        self.slim(protected_attributes=self.elevate(merge_strategy=merge_strategy))
        return self.freeze()

    def clear_context(self) -> None:
        """Empties the context."""
        self._ensure_mutable()
        if self._context is not SENTINEL:
            self._context.clear()

    # --- introspection -----------------------------------------------------

    @classmethod
    def ps(cls) -> None:
        """Prints every Kind of the current space with its footprint and origin."""
        rows = ["{:<30} {:<15} {:<50}".format("Name", "Footprint (b)", "Origin"), "-" * 95]
        total = 0
        for name, kind in sorted(current_space().pool.items()):
            footprint = kind.footprint() if isinstance(kind, Kind) else getsizeof(kind)
            total += footprint
            origin = kind.origin if kind.origin is not None else f"{type(kind).__module__}.{type(kind).__name__}"
            rows.append("{:<30} {:<15} {:<50}".format(name, footprint, str(origin)))
        rows += ["-" * 95, "{:<30} {:<15}".format("Total", total)]
        print("\n".join(rows))

    @classmethod
    def ls(cls) -> None:
        """Prints the registered mixins: the names every Kind has gained at runtime."""
        print("Registered mixins:")
        for name in sorted(get_applied_mixins()):
            print(f"- {name}")

    def stat(self) -> None:
        """Prints this Kind's footprint, its own attributes and the mixins it shares."""
        rows = [f"Statistics for Kind: '{self.name}'",
                f"Footprint (with descendants): {self.footprint()} bytes",
                f"Children: {len(self.children)}  Parents: {len(self.parents)}  "
                f"Relations: {sum(1 for how in self.relations if not how.startswith(INVERSE_PREFIX))}",
                f"Own attributes: {', '.join(sorted(self._elevated_attributes)) or '-'}",
                f"Registered mixins: {len(get_applied_mixins())} (Kind.ls() lists them)",
                f"Frozen: {self._frozen}"]
        print("\n".join(rows))

    def footprint(self) -> int:
        """Bytes used by this Kind and its descendants (each object counted once)."""
        shared = (None, True, False, SENTINEL)
        memo: set[int] = set()
        total = 0
        stack: list[Any] = [self]
        while stack:
            obj = stack.pop()
            if id(obj) in memo or any(obj is s for s in shared):
                continue
            memo.add(id(obj))
            total += getsizeof(obj)
            if isinstance(obj, Kind):
                total += getsizeof(obj.parents._items) + getsizeof(obj.children._items)
                stack += [obj.name, obj.origin, obj.node_shape, obj._index, obj._metadata,
                          obj._context, obj._elevated_attributes]
                stack.extend(obj.children)
            elif isinstance(obj, dict):
                stack.extend(obj.keys())
                stack.extend(obj.values())
            elif isinstance(obj, (list, tuple, set, frozenset)):
                stack.extend(obj)
            elif hasattr(obj, '__dict__') and not inspect.isroutine(obj) and not inspect.isclass(obj):
                stack.append(vars(obj))
        return total


def canonical_repr(value: Any) -> str:
    """repr() with the order of unordered containers fixed, so equal values get equal names.

    Dict keys and set members are sorted by their own canonical form; lists and tuples
    keep their order. `{'b': 2, 'a': 1}` and `{'a': 1, 'b': 2}` both give "{'a': 1, 'b': 2}".
    """
    if isinstance(value, dict):
        pairs = sorted((canonical_repr(k), canonical_repr(v)) for k, v in value.items())
        return "{" + ", ".join(f"{k}: {v}" for k, v in pairs) + "}"
    if isinstance(value, (set, frozenset)):
        members = sorted(canonical_repr(member) for member in value)
        return f"{type(value).__name__}({{{', '.join(members)}}})" if members else f"{type(value).__name__}()"
    if isinstance(value, list):
        return "[" + ", ".join(canonical_repr(item) for item in value) + "]"
    if isinstance(value, tuple):
        inner = ", ".join(canonical_repr(item) for item in value)
        return f"({inner},)" if len(value) == 1 else f"({inner})"
    return repr(value)


def to_kind(obj: Any) -> Kind:
    """Converts an object to a Kind."""
    return Kind.from_object(obj)
