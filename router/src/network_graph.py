from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GraphLink:
    neighbor_router_id: str
    cost: int


def build_network_graph(
    latest_lsa_by_origin: dict[str, dict[str, Any]],
) -> dict[str, list[GraphLink]]:
    network_graph: dict[str, list[GraphLink]] = {}

    for origin_router_id, lsa_message_data in latest_lsa_by_origin.items():
        links_data = lsa_message_data["links"]
        graph_links: list[GraphLink] = []

        for link_data in links_data:
            graph_links.append(
                GraphLink(
                    neighbor_router_id=link_data["neighbor_router_id"],
                    cost=link_data["cost"],
                )
            )

        network_graph[origin_router_id] = graph_links

    return network_graph
