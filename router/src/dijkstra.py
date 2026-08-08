import heapq
from dataclasses import dataclass

from network_graph import GraphLink


@dataclass(frozen=True)
class ShortestRoute:
    destination_router_id: str
    next_hop_router_id: str
    total_cost: int


def calculate_shortest_routes(
    network_graph: dict[str, list[GraphLink]],
    source_router_id: str,
) -> list[ShortestRoute]:
    router_ids = collect_router_ids(network_graph)
    minimum_cost_by_router = {
        router_id: float("inf")
        for router_id in router_ids
    }
    previous_router_by_router: dict[str, str] = {}
    minimum_cost_by_router[source_router_id] = 0
    pending_routers: list[tuple[int, str]] = [(0, source_router_id)]

    while pending_routers:
        current_cost, current_router_id = heapq.heappop(pending_routers)

        if current_cost > minimum_cost_by_router[current_router_id]:
            continue

        for graph_link in network_graph.get(current_router_id, []):
            candidate_cost = current_cost + graph_link.cost
            known_cost = minimum_cost_by_router[graph_link.neighbor_router_id]

            if candidate_cost >= known_cost:
                continue

            minimum_cost_by_router[graph_link.neighbor_router_id] = candidate_cost
            previous_router_by_router[graph_link.neighbor_router_id] = (
                current_router_id
            )
            heapq.heappush(
                pending_routers,
                (candidate_cost, graph_link.neighbor_router_id),
            )

    shortest_routes: list[ShortestRoute] = []

    for destination_router_id in sorted(router_ids):
        if destination_router_id == source_router_id:
            continue

        total_cost = minimum_cost_by_router[destination_router_id]

        if total_cost == float("inf"):
            continue

        next_hop_router_id = find_next_hop_router_id(
            source_router_id,
            destination_router_id,
            previous_router_by_router,
        )
        shortest_routes.append(
            ShortestRoute(
                destination_router_id=destination_router_id,
                next_hop_router_id=next_hop_router_id,
                total_cost=int(total_cost),
            )
        )

    return shortest_routes


def collect_router_ids(
    network_graph: dict[str, list[GraphLink]],
) -> set[str]:
    router_ids = set(network_graph)

    for graph_links in network_graph.values():
        for graph_link in graph_links:
            router_ids.add(graph_link.neighbor_router_id)

    return router_ids


def find_next_hop_router_id(
    source_router_id: str,
    destination_router_id: str,
    previous_router_by_router: dict[str, str],
) -> str:
    current_router_id = destination_router_id

    while previous_router_by_router[current_router_id] != source_router_id:
        current_router_id = previous_router_by_router[current_router_id]

    return current_router_id
