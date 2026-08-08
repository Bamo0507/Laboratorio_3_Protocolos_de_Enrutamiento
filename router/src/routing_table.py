import csv
from dataclasses import dataclass
from pathlib import Path


ROUTING_TABLE_HEADER = [
    "destination_router_id",
    "next_hop_router_id",
    "next_hop_ip",
    "next_hop_port",
    "total_cost",
]


@dataclass(frozen=True)
class RoutingTableRow:
    destination_router_id: str
    next_hop_router_id: str
    next_hop_ip: str
    next_hop_port: int
    total_cost: int


def write_routing_table(
    router_id: str,
    routing_table_rows: list[RoutingTableRow],
) -> Path:
    router_directory = Path(__file__).resolve().parent.parent
    routing_tables_directory = router_directory / "routing_tables"
    routing_tables_directory.mkdir(exist_ok=True)
    routing_table_path = (
        routing_tables_directory / f"{router_id}_tabla_enrutamiento.csv"
    )

    with routing_table_path.open("w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(ROUTING_TABLE_HEADER)

        for routing_table_row in routing_table_rows:
            csv_writer.writerow(
                [
                    routing_table_row.destination_router_id,
                    routing_table_row.next_hop_router_id,
                    routing_table_row.next_hop_ip,
                    routing_table_row.next_hop_port,
                    routing_table_row.total_cost,
                ]
            )

    return routing_table_path
