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
    routing_table_path = get_routing_table_path(router_id)
    routing_table_path.parent.mkdir(exist_ok=True)

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


def read_routing_table(router_id: str) -> dict[str, RoutingTableRow]:
    routing_table_path = get_routing_table_path(router_id)

    if not routing_table_path.exists():
        raise ValueError(
            "No existe la tabla de enrutamiento para el router "
            f"{router_id}: {routing_table_path}."
        )

    with routing_table_path.open("r", encoding="utf-8", newline="") as file:
        csv_reader = csv.DictReader(file)

        if csv_reader.fieldnames != ROUTING_TABLE_HEADER:
            raise ValueError(
                "El encabezado de la tabla de enrutamiento no coincide con "
                "el formato acordado."
            )

        routing_table_by_destination: dict[str, RoutingTableRow] = {}

        for row_number, row_data in enumerate(csv_reader, start=2):
            routing_table_row = parse_routing_table_row(row_data, row_number)
            destination_router_id = routing_table_row.destination_router_id

            if destination_router_id in routing_table_by_destination:
                raise ValueError(
                    "La tabla de enrutamiento contiene dos filas para el "
                    f"destino {destination_router_id}."
                )

            routing_table_by_destination[destination_router_id] = (
                routing_table_row
            )

    return routing_table_by_destination


def get_routing_table_path(router_id: str) -> Path:
    if not isinstance(router_id, str) or not router_id.strip():
        raise ValueError("El identificador del router debe ser texto no vacío.")

    router_directory = Path(__file__).resolve().parent.parent
    routing_tables_directory = router_directory / "routing_tables"
    return routing_tables_directory / f"{router_id}_tabla_enrutamiento.csv"


def parse_routing_table_row(
    row_data: dict[str, str | None],
    row_number: int,
) -> RoutingTableRow:
    return RoutingTableRow(
        destination_router_id=read_required_text(
            row_data,
            "destination_router_id",
            row_number,
        ),
        next_hop_router_id=read_required_text(
            row_data,
            "next_hop_router_id",
            row_number,
        ),
        next_hop_ip=read_required_text(
            row_data,
            "next_hop_ip",
            row_number,
        ),
        next_hop_port=read_port(row_data, "next_hop_port", row_number),
        total_cost=read_positive_integer(row_data, "total_cost", row_number),
    )


def read_required_text(
    row_data: dict[str, str | None],
    field_name: str,
    row_number: int,
) -> str:
    field_value = row_data.get(field_name)

    if field_value is None or not field_value.strip():
        raise ValueError(
            f"La columna '{field_name}' en la fila {row_number} debe contener texto."
        )

    return field_value


def read_port(
    row_data: dict[str, str | None],
    field_name: str,
    row_number: int,
) -> int:
    port = read_positive_integer(row_data, field_name, row_number)

    if port > 65535:
        raise ValueError(
            f"La columna '{field_name}' en la fila {row_number} debe estar "
            "entre 1 y 65535."
        )

    return port


def read_positive_integer(
    row_data: dict[str, str | None],
    field_name: str,
    row_number: int,
) -> int:
    field_value = read_required_text(row_data, field_name, row_number)

    try:
        integer_value = int(field_value)
    except ValueError as exception:
        raise ValueError(
            f"La columna '{field_name}' en la fila {row_number} debe ser un entero."
        ) from exception

    if integer_value <= 0:
        raise ValueError(
            f"La columna '{field_name}' en la fila {row_number} debe ser mayor que cero."
        )

    return integer_value
