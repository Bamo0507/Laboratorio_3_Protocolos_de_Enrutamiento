import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_ATTACHED_HOST_ROLES = {"CLIENT", "SERVER"}


@dataclass(frozen=True)
class ListeningAddress:
    ip: str
    port: int


@dataclass(frozen=True)
class NeighborConfiguration:
    router_id: str
    ip: str
    port: int
    cost: int


@dataclass(frozen=True)
class AttachedHostConfiguration:
    role: str
    host_id: str
    ip: str
    port: int


@dataclass(frozen=True)
class RouterConfiguration:
    router_id: str
    listening_address: ListeningAddress
    neighbors: list[NeighborConfiguration]
    attached_host: AttachedHostConfiguration | None


def load_router_configuration(
    configuration_file_path: str,
) -> RouterConfiguration:
    configuration_path = Path(configuration_file_path)

    try:
        configuration_text = configuration_path.read_text(encoding="utf-8")
    except FileNotFoundError as exception:
        raise ValueError(
            "No existe el archivo de configuración del router: "
            f"{configuration_path}."
        ) from exception

    try:
        configuration_data = json.loads(configuration_text)
    except json.JSONDecodeError as exception:
        raise ValueError(
            "El archivo de configuración no contiene JSON válido: "
            f"{configuration_path}."
        ) from exception

    ensure_json_object(configuration_data, "configuración raíz")

    router_id = read_required_text(configuration_data, "router_id")
    listening_address = read_listening_address(configuration_data)
    neighbors = read_neighbors(configuration_data, router_id)
    attached_host = read_attached_host(configuration_data)

    return RouterConfiguration(
        router_id=router_id,
        listening_address=listening_address,
        neighbors=neighbors,
        attached_host=attached_host,
    )


def read_listening_address(
    configuration_data: dict[str, Any],
) -> ListeningAddress:
    listening_data = read_required_object(configuration_data, "listen")

    return ListeningAddress(
        ip=read_required_text(listening_data, "listen.ip"),
        port=read_required_port(listening_data, "listen.port"),
    )


def read_neighbors(
    configuration_data: dict[str, Any],
    router_id: str,
) -> list[NeighborConfiguration]:
    neighbors_data = configuration_data.get("neighbors")

    if not isinstance(neighbors_data, list):
        raise ValueError("El campo 'neighbors' debe ser una lista.")

    neighbors: list[NeighborConfiguration] = []
    registered_neighbor_ids: set[str] = set()

    for neighbor_index, neighbor_data in enumerate(neighbors_data):
        field_prefix = f"neighbors[{neighbor_index}]"
        ensure_json_object(neighbor_data, field_prefix)

        neighbor_router_id = read_required_text(
            neighbor_data,
            f"{field_prefix}.router_id",
        )

        if neighbor_router_id == router_id:
            raise ValueError(
                "Un router no puede declararse como su propio vecino."
            )

        if neighbor_router_id in registered_neighbor_ids:
            raise ValueError(
                "Un vecino solo puede aparecer una vez en la configuración: "
                f"{neighbor_router_id}."
            )

        registered_neighbor_ids.add(neighbor_router_id)

        neighbors.append(
            NeighborConfiguration(
                router_id=neighbor_router_id,
                ip=read_required_text(neighbor_data, f"{field_prefix}.ip"),
                port=read_required_port(neighbor_data, f"{field_prefix}.port"),
                cost=read_required_cost(neighbor_data, f"{field_prefix}.cost"),
            )
        )

    return neighbors


def read_attached_host(
    configuration_data: dict[str, Any],
) -> AttachedHostConfiguration | None:
    if "attached_host" not in configuration_data:
        raise ValueError("Falta el campo obligatorio 'attached_host'.")

    attached_host_data = configuration_data["attached_host"]

    if attached_host_data is None:
        return None

    ensure_json_object(attached_host_data, "attached_host")
    role = read_required_text(attached_host_data, "attached_host.role")

    if role not in VALID_ATTACHED_HOST_ROLES:
        valid_roles_text = ", ".join(sorted(VALID_ATTACHED_HOST_ROLES))
        raise ValueError(
            "El rol de 'attached_host' debe ser uno de los siguientes: "
            f"{valid_roles_text}."
        )

    return AttachedHostConfiguration(
        role=role,
        host_id=read_required_text(attached_host_data, "attached_host.host_id"),
        ip=read_required_text(attached_host_data, "attached_host.ip"),
        port=read_required_port(attached_host_data, "attached_host.port"),
    )


def read_required_object(
    json_object: dict[str, Any],
    field_name: str,
) -> dict[str, Any]:
    field_value = json_object.get(field_name)
    ensure_json_object(field_value, field_name)
    return field_value


def read_required_text(
    json_object: dict[str, Any],
    field_name: str,
) -> str:
    field_value = json_object.get(field_name)

    if not isinstance(field_value, str) or not field_value.strip():
        raise ValueError(
            f"El campo '{field_name}' debe ser texto no vacío."
        )

    return field_value


def read_required_port(
    json_object: dict[str, Any],
    field_name: str,
) -> int:
    field_value = json_object.get(field_name)

    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise ValueError(f"El campo '{field_name}' debe ser un puerto entero.")

    if field_value < 1 or field_value > 65535:
        raise ValueError(
            f"El campo '{field_name}' debe estar entre 1 y 65535."
        )

    return field_value


def read_required_cost(
    json_object: dict[str, Any],
    field_name: str,
) -> int:
    field_value = json_object.get(field_name)

    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise ValueError(f"El campo '{field_name}' debe ser un entero.")

    if field_value <= 0:
        raise ValueError(f"El campo '{field_name}' debe ser mayor que cero.")

    return field_value


def ensure_json_object(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"El campo '{field_name}' debe ser un objeto JSON.")
