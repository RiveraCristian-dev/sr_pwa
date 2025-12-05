"""Dijkstra algorithm implementation.

Graph format expected (JSON):
{
  "A": {
    "B": {"dist": 5},
    "C": {"dist": 2},
    "coord": {"x": 10, "y": 10}
  },
  ...
}
"""
import heapq
from typing import Dict, List, Tuple

def dijkstra(graph: Dict, start: str, goal: str) -> List[str]:
    if start not in graph or goal not in graph:
        raise ValueError(f"Start or goal node not in graph: {start}, {goal}")

    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0.0

    pq = [(0.0, start)]
    visited = set()

    while pq:
        current_dist, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            break

        neighbors = graph.get(node, {})
        for neighbor, data in neighbors.items():
            if neighbor == "coord":
                continue
            weight = float(data.get("dist", 1.0))
            new_dist = current_dist + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruct path
    path = []
    cur = goal
    if prev[cur] is None and cur != start and dist[cur] == float('inf'):
        # no path
        return []
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path

def path_distance(graph: Dict, path: List[str]) -> float:
    total = 0.0
    for i in range(len(path)-1):
        a = path[i]
        b = path[i+1]
        edge = graph[a].get(b)
        if edge is None:
            # If edge missing, try symmetric
            edge = graph[b].get(a)
        if edge is None:
            raise ValueError(f"Edge not found between {a} and {b}")
        total += float(edge.get('dist', 0.0))
    return total
