from __future__ import division
import random
import os
from collections import defaultdict
from collections import deque
from typing import Set, Dict, List, Optional

class Edge:
    __slots__ = ('ident', 'x', 'y', 'm', 'color', 'G')
    
    def __init__(self, ident: int, x: 'Vertex', y: 'Vertex', m: int, G: 'Multigraph'):
        self.ident = ident
        self.x = x
        self.y = y
        self.m = m
        self.color = 0
        self.G = G

    def color_with(self, c: int) -> None:
        if self.color:
            self.x.colors[self.color] -= 1
            self.y.colors[self.color] -= 1
            if self.x.colors[self.color] == 0:
                del self.x.colors[self.color]
            if self.y.colors[self.color] == 0:
                del self.y.colors[self.color]
        self.color = c
        self.x.colors[c] = self.x.colors.get(c, 0) + 1
        self.y.colors[c] = self.y.colors.get(c, 0) + 1

class Vertex:
    __slots__ = ('ident', 'edges', 'colors', 'G', 'missing_cache')
    
    def __init__(self, ident: int, G: 'Multigraph'):
        self.ident = ident
        self.edges = set() #connected edges
        self.colors = defaultdict(int)  # color -> count
        self.G = G
        self.missing_cache = set()
        # Cached missing colors for performance optimization


    def degree(self) -> int:
        #Returns the degree of the vertex (number of connected edges).
        return len(self.edges)

    def update_missing_colors(self):
        used_colors = set(self.colors.keys())
        self.missing_cache = self.G.colors - used_colors

    def missing_colors(self) -> Set[int]:
        self.update_missing_colors()
        return self.missing_cache

    def with_color(self, c: int) -> Optional[Edge]:
        #Returns an edge with the given color if one exists.
        return next((e for e in self.edges if e.color == c), None)

    def add_edge(self, edge: 'Edge'):
        #Adds an edge to this vertex and updates color tracking.
        self.edges.add(edge)
        if edge.color is not None:
            self.colors[edge.color] += 1
            self.update_missing_colors()

    def remove_edge(self, edge: 'Edge'):
        #Removes an edge from this vertex and updates color tracking.
        self.edges.discard(edge)
        if edge.color is not None:
            self.colors[edge.color] -= 1
            if self.colors[edge.color] == 0:
                del self.colors[edge.color]
            self.update_missing_colors()

    def log_state(self):
        print(f"Edge {self.ident}: ({self.x.ident}, {self.y.ident}), Color: {self.color}")


class Multigraph:
    def __init__(self):
        self.vertices: Dict[int, Vertex] = {}
        self.edges: List[Edge] = []
        self.colors: Set[int] = set()
        self._edge_lookup: Dict[tuple, int] = defaultdict(int)

    def add_vertex(self, ident: int) -> Vertex:
        if ident not in self.vertices:
            self.vertices[ident] = Vertex(ident, self)
        return self.vertices[ident]

    def add_edge(self, ident: int, x: int, y: int, m: int) -> None:
        vx, vy = self.add_vertex(x), self.add_vertex(y)
        edge = Edge(ident, vx, vy, m, self)
        self.edges.append(edge)
        vx.edges.add(edge)
        vy.edges.add(edge)
        self._edge_lookup[tuple(sorted((x, y)))] += 1

    def edge_coloring(self):
        delta = max(v.degree() for v in self.vertices.values())
        self.colors = set(range(1, delta + 2))  # Allow up to Δ + 1 colors

        for edge in self.edges:
            missing_x = edge.x.missing_colors()
            missing_y = edge.y.missing_colors()
            available = missing_x & missing_y

            if available:
                edge.color_with(min(available))
            else:
                # Use a new color if all are blocked
                new_color = max(self.colors) + 1
                self.colors.add(new_color)
                edge.color_with(new_color)


def debug_missing_edges(input_file: str, output_file: str) -> None:
    #Debugging function to check if there are missing edges between the input and output.
    # Parse the input file
    input_edges = []
    with open(input_file, "r") as f:
        num_edges = int(f.readline().strip())  # First line is the number of edges
        for line in f:
            parts = list(map(int, line.strip().split()))
            if len(parts) == 3:
                x, y, m = parts
                input_edges.append((x, y))  # Store as a tuple (x, y)

    # Parse the output file
    output_edges = []
    with open(output_file, "r") as f:
        for line in f:
            if line.startswith("Edge"):
                parts = line.split(":")[1].strip()  # Extract edge description
                edge_info = parts.split(",")[0]    # Extract (x, y)
                edge = tuple(map(int, edge_info.strip("()").split()))  # Convert to tuple (x, y)
                output_edges.append(edge)

    # Check for missing edges
    missing_edges = [edge for edge in input_edges if edge not in output_edges and tuple(reversed(edge)) not in output_edges]
    extra_edges = [edge for edge in output_edges if edge not in input_edges and tuple(reversed(edge)) not in input_edges]

    # Report results
    if missing_edges:
        print(f"Missing edges in the output: {missing_edges}")
    else:
        print("All edges from the input are present in the output.")

    if extra_edges:
        print(f"Unexpected extra edges in the output: {extra_edges}")
    else:
        print("No unexpected extra edges in the output.")

def recolor_edges(self, u: Vertex, v: Vertex, new_color: int):
    #Recolors edges to resolve conflicts by constructing Vizing's fan using BFS and applying recoloring rules.
    # Initialize queue for BFS
    queue = deque([(u, None)])  # (current_vertex, parent_edge_color)
    visited = set()
    parent_color_map = {}  # Maps a vertex to its parent edge color

    # BFS to find Vizing's fan or recoloring path
    while queue:
        current_vertex, parent_color = queue.popleft()

        if current_vertex in visited:
            continue
        visited.add(current_vertex)

        # Get missing colors for the current vertex
        missing_colors = current_vertex.missing_colors()

        if new_color in missing_colors:
            # Recolor the edge between the current vertex and its parent
            if parent_color is not None:
                edge_to_recolor = current_vertex.with_color(parent_color)
                edge_to_recolor.color = new_color
            return  # Recoloring successful, exit function

        # Add adjacent vertices to the queue
        for edge in current_vertex.edges:
            if edge.color != parent_color:
                next_vertex = edge.other(current_vertex)
                queue.append((next_vertex, edge.color))
                parent_color_map[next_vertex] = edge.color

    # If BFS fails to find a recoloring path, raise an exception
    raise ValueError("Recoloring failed: No valid path found.")

def main():
    
    inFile = "input3.txt"
    outFile = "output.txt"
    
    if not os.path.exists(inFile):
        print(f"Error: {inFile} not found!")
        return

    debug_missing_edges (inFile, outFile)
    G = Multigraph()
    
    with open(inFile, "r") as f:
        edge_id = 1
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                x, y, m = map(int, parts)
                G.add_edge(edge_id, x, y, m)
                edge_id += 1
    
    G.edge_coloring()
    
    with open(outFile, "w") as f:
        for edge in G.edges:
            f.write(f"Edge {edge.ident}: ({edge.x.ident}, {edge.y.ident}), Color: {edge.color}\n")
    
    print(f"Edge-colored graph written to {outFile}")

if __name__ == '__main__':
    main()