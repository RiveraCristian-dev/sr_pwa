"""Simulation helpers: interpolate positions between nodes to produce smooth movement.

Exports:
- simulate_route(graph, route, steps_per_segment=20)
- simulate_aba(graph, origin, dest, steps_per_segment=20)
"""
from typing import Dict, List
def interpolate(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def simulate_route(graph: Dict, route: List[str], steps_per_segment: int = 20) -> List[Dict]:
    if not route or len(route) < 2:
        return []
    positions = []
    for i in range(len(route)-1):
        n1 = route[i]
        n2 = route[i+1]
        coord1 = graph[n1].get('coord')
        coord2 = graph[n2].get('coord')
        if coord1 is None or coord2 is None:
            raise ValueError(f"Missing coords for nodes {n1} or {n2}")
        for s in range(steps_per_segment):
            t = s / steps_per_segment
            x = interpolate(coord1['x'], coord2['x'], t)
            y = interpolate(coord1['y'], coord2['y'], t)
            positions.append({
                'x': x,
                'y': y,
                'from': n1,
                'to': n2,
                'step': s,
                't': t
            })
    # append final node coord
    last = route[-1]
    positions.append({
        'x': graph[last]['coord']['x'],
        'y': graph[last]['coord']['y'],
        'from': route[-2],
        'to': last,
        'step': steps_per_segment,
        't': 1.0
    })
    return positions

def simulate_aba(graph: Dict, origin: str, dest: str, steps_per_segment: int = 20) -> Dict:
    from core.dijktra import dijkstra, path_distance
    ida = dijkstra(graph, origin, dest)
    regreso = dijkstra(graph, dest, origin)
    if not ida:
        raise ValueError("No path origin->dest")
    if not regreso:
        raise ValueError("No path dest->origin")
    pos_ida = simulate_route(graph, ida, steps_per_segment)
    pos_regreso = simulate_route(graph, regreso, steps_per_segment)
    # mark phases
    for p in pos_ida:
        p['phase'] = 'ida'
    for p in pos_regreso:
        p['phase'] = 'regreso'
    # combine: ida then regreso
    combined = pos_ida + pos_regreso
    total_distance = path_distance(graph, ida) + path_distance(graph, regreso)
    return {
        'ruta_ida': ida,
        'ruta_regreso': regreso,
        'posiciones': combined,
        'distancia_total': total_distance
    }
