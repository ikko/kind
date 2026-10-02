"""This module provides visualization capabilities for Kind objects.

It allows for rendering Kind graphs to various formats, such as DOT, SVG, PNG, and Mermaid.
"""
from __future__ import annotations
from typing import Literal
import anyio

try:
    import graphviz
    _GRAPHVIZ_AVAILABLE = True
except ImportError:
    _GRAPHVIZ_AVAILABLE = False

from kind.core.protocols import KindVisualProtocol


class KindRender(KindVisualProtocol):
    def __init__(self, root: 'Kind'):
        self.root = root

    def _build_dot_source(self, mode: Literal["tree", "graph"]) -> str:
        seen = set()
        lines = ["digraph G {"]

        def escape(kind):
            return f'"{kind.name}"'

        def walk(kind):
            if kind in seen:
                return
            seen.add(kind)
            if mode == "tree":
                for child in kind.children:
                    lines.append(f"{escape(kind)} -> {escape(child)}")
                    walk(child)
            elif mode == "graph":
                # Assuming 'related_to' or similar for generic graph traversal
                # For now, using children for simplicity, but this could be extended
                for neighbor in kind.children:
                    lines.append(f"{escape(kind)} -> {escape(neighbor)}")
                    walk(neighbor)

        walk(self.root)
        lines.append("}")
        return "\n".join(lines)

    def to_dot(self, mode: Literal["tree", "graph"] = "tree") -> str:
        if not _GRAPHVIZ_AVAILABLE:
            raise ImportError("Graphviz is not installed. Please install it with `pip install 'kind[visual]'`.")
        return self._build_dot_source(mode)

    async def a_to_svg(self, mode: Literal["tree", "graph"] = "tree") -> str:
        if not _GRAPHVIZ_AVAILABLE:
            raise ImportError("Graphviz is not installed. Please install it with `pip install 'kind[visual]'`.")
        dot = self._build_dot_source(mode)
        # Run in a thread pool to avoid blocking the event loop
        return await anyio.to_thread.run_sync(lambda: graphviz.Source(dot).pipe(format="svg").decode())

    def to_svg(self, mode: Literal["tree", "graph"] = "tree") -> str:
        return anyio.run(self.a_to_svg, mode)

    async def a_to_png(self, mode: Literal["tree", "graph"] = "tree") -> bytes:
        if not _GRAPHVIZ_AVAILABLE:
            raise ImportError("Graphviz is not installed. Please install it with `pip install 'kind[visual]'`.")
        dot = self._build_dot_source(mode)
        # Run in a thread pool to avoid blocking the event loop
        return await anyio.to_thread.run_sync(lambda: graphviz.Source(dot).pipe(format="png"))

    def to_png(self, mode: Literal["tree", "graph"] = "tree") -> bytes:
        return anyio.run(self.a_to_png, mode)

    def to_mmd(self, mode: Literal["tree", "graph"] = "tree") -> str:
        seen = set()
        lines = ["graph TD"] if mode == "tree" else ["graph LR"]

        def esc(kind):
            return kind.name.replace(" ", "_")

        def walk(kind):
            if kind in seen:
                return
            seen.add(kind)
            if mode == "tree":
                for child in sorted(kind.children, key=lambda s: s.name):
                    lines.append(f"{esc(kind)} --> {esc(child)}")
                    walk(child)
            elif mode == "graph":
                for neighbor in kind.children:
                    lines.append(f"{esc(kind)} --> {esc(neighbor)}")
                    walk(neighbor)

        walk(self.root)
        header = lines[0]
        sorted_lines = sorted(lines[1:])
        return header + "\n" + "\n".join(sorted_lines)

    @classmethod
    def from_mmd(cls, mmd_string: str) -> 'Kind':
        from kind.core.kind import Kind  # Import here to avoid circular dependency

        lines = mmd_string.strip().split('\n')
        if not lines:
            raise ValueError("Empty Mermaid string provided.")

        header = lines[0].strip()
        if header not in ["graph TD", "graph LR"]:
            raise ValueError(f"Unsupported Mermaid graph type: {header}. Only 'graph TD' and 'graph LR' are supported.")

        kinds = {} # Map Mermaid ID to Kind object
        
        def get_or_create_kind(mermaid_id: str) -> Kind:
            if mermaid_id in kinds:
                return kinds[mermaid_id]

            # Clean the Mermaid ID to get the actual Kind name
            clean_name = mermaid_id.replace('_', ' ')
            # Handle node declarations like 'node_id(Node Name)'
            if '(' in clean_name and clean_name.endswith(')'):
                last_paren_idx = clean_name.rfind('(')
                display_name = clean_name[last_paren_idx + 1 : -1]
                if display_name:
                    clean_name = display_name
                else:
                    clean_name = clean_name[:last_paren_idx].strip()

            # Create the Kind with the cleaned name
            new_kind = Kind(clean_name)
            kinds[mermaid_id] = new_kind # Store using Mermaid ID
            return new_kind

        # Process relationships
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue

            # Handle 'A --> B' and 'A -- text --> B'
            if '-->' in line:
                parts = line.split('-->')
                source_part = parts[0].strip()
                target_part = parts[1].strip()

                # Check for text in relationship: 'A -- text --> B'
                if '--' in source_part and source_part.count('--') == 1:
                    sub_parts = source_part.split('--')
                    source_name = sub_parts[0].strip()
                    relation_text = sub_parts[1].strip()
                    
                    source_kind = get_or_create_kind(source_name)
                    target_kind = get_or_create_kind(target_part)
                    source_kind.relate(target_kind, how=relation_text)
                else:
                    source_kind = get_or_create_kind(source_part)
                    target_kind = get_or_create_kind(target_part)
                    source_kind.append(target_kind)
            # Handle node declarations like 'node_id(Node Name)'
            elif '(' in line and line.endswith(')'):
                get_or_create_kind(line)
            else:
                # Just a node name, ensure it's created
                get_or_create_kind(line)

        # Determine root kinds (those with no parents among the parsed kinds)
        all_kinds = set(kinds.values())
        child_kinds = set()
        for kind in all_kinds:
            for child in kind.children:
                if child in all_kinds: # Only consider children that were part of this graph
                    child_kinds.add(child)
            # Also consider kinds related via 'relate' as children for root determination
            for how, related_kinds in kind.relations.items():
                if not how.startswith('_inverse_'):
                    for related_kind in related_kinds:
                        if related_kind in all_kinds:
                            child_kinds.add(related_kind)

        root_kinds = [kind for kind in all_kinds if kind not in child_kinds]

        if not root_kinds:
            # If no clear root (e.g., a circular graph or single node), return any kind
            if all_kinds:
                return next(iter(all_kinds))
            else:
                raise ValueError("No kinds found in the Mermaid string.")
        
        # For simplicity, return the first root. In a more complex scenario,
        # we might want to return a list of roots or a composite kind.
        return root_kinds[0]

    def to_ascii(self, mode: Literal["tree", "graph"] = "tree") -> str:
        # This will be handled by the Kind's own to_ascii method, or a dedicated GraphTraversal
        # For now, a placeholder or direct call to Kind's method
        if mode == "tree":
            return self.root.to_ascii()
        else:
            # For generic graph, we might need a more sophisticated ASCII renderer
            # For simplicity, let's just use the tree representation for now
            return self.root.to_ascii()
