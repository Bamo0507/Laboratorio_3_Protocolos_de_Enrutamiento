import json
from typing import Any

from router_config import RouterConfiguration


HELLO_MESSAGE_TYPE = "HELLO"
HELLO_REPLY_MESSAGE_TYPE = "HELLO_REPLY"
LSA_MESSAGE_TYPE = "LSA"


def build_hello_message(
    router_configuration: RouterConfiguration,
) -> str:
    message_data = {
        "type": HELLO_MESSAGE_TYPE,
        "origin_router_id": router_configuration.router_id,
        "listen_port": router_configuration.listening_address.port,
    }
    return serialize_control_message(message_data)


def build_hello_reply_message(
    router_configuration: RouterConfiguration,
    link_cost: int,
) -> str:
    message_data = {
        "type": HELLO_REPLY_MESSAGE_TYPE,
        "origin_router_id": router_configuration.router_id,
        "cost": link_cost,
    }
    return serialize_control_message(message_data)


def build_lsa_message(
    router_configuration: RouterConfiguration,
    sequence: int,
    from_router_id: str,
) -> str:
    if sequence <= 0:
        raise ValueError("La secuencia de una LSA debe ser mayor que cero.")

    links = []

    for neighbor_configuration in router_configuration.neighbors:
        links.append(
            {
                "neighbor_router_id": neighbor_configuration.router_id,
                "cost": neighbor_configuration.cost,
            }
        )

    message_data = {
        "type": LSA_MESSAGE_TYPE,
        "origin_router_id": router_configuration.router_id,
        "sequence": sequence,
        "links": links,
        "from_router_id": from_router_id,
    }
    return serialize_control_message(message_data)


def build_forwarded_lsa_message(
    lsa_message_data: dict[str, Any],
    forwarding_router_id: str,
) -> str:
    validate_lsa_message(lsa_message_data)

    forwarded_links = []

    for link_data in lsa_message_data["links"]:
        forwarded_links.append(dict(link_data))

    forwarded_message_data = {
        "type": LSA_MESSAGE_TYPE,
        "origin_router_id": lsa_message_data["origin_router_id"],
        "sequence": lsa_message_data["sequence"],
        "links": forwarded_links,
        "from_router_id": forwarding_router_id,
    }
    return serialize_control_message(forwarded_message_data)


def parse_control_message(serialized_message: str) -> dict[str, Any]:
    try:
        message_data = json.loads(serialized_message)
    except json.JSONDecodeError as exception:
        raise ValueError("El mensaje de control no contiene JSON válido.") from exception

    if not isinstance(message_data, dict):
        raise ValueError("El mensaje de control debe ser un objeto JSON.")

    message_type = message_data.get("type")

    if message_type == HELLO_MESSAGE_TYPE:
        validate_hello_message(message_data)
    elif message_type == HELLO_REPLY_MESSAGE_TYPE:
        validate_hello_reply_message(message_data)
    elif message_type == LSA_MESSAGE_TYPE:
        validate_lsa_message(message_data)
    else:
        raise ValueError(
            "El tipo de mensaje de control no es reconocido: "
            f"{message_type}."
        )

    return message_data


def serialize_control_message(message_data: dict[str, Any]) -> str:
    return json.dumps(message_data, ensure_ascii=False, separators=(",", ":"))


def validate_hello_message(message_data: dict[str, Any]) -> None:
    read_required_text(message_data, "origin_router_id")
    read_required_port(message_data, "listen_port")


def validate_hello_reply_message(message_data: dict[str, Any]) -> None:
    read_required_text(message_data, "origin_router_id")
    read_required_cost(message_data, "cost")


def validate_lsa_message(message_data: dict[str, Any]) -> None:
    read_required_text(message_data, "origin_router_id")
    read_required_positive_integer(message_data, "sequence")
    read_required_text(message_data, "from_router_id")

    links_data = message_data.get("links")

    if not isinstance(links_data, list):
        raise ValueError("El campo 'links' de una LSA debe ser una lista.")

    registered_neighbor_ids: set[str] = set()

    for link_index, link_data in enumerate(links_data):
        field_prefix = f"links[{link_index}]"

        if not isinstance(link_data, dict):
            raise ValueError(
                f"El campo '{field_prefix}' debe ser un objeto JSON."
            )

        neighbor_router_id = read_required_text(
            link_data,
            f"{field_prefix}.neighbor_router_id",
        )

        if neighbor_router_id in registered_neighbor_ids:
            raise ValueError(
                "Un vecino solo puede aparecer una vez en una LSA: "
                f"{neighbor_router_id}."
            )

        registered_neighbor_ids.add(neighbor_router_id)
        read_required_cost(link_data, f"{field_prefix}.cost")


def read_required_text(message_data: dict[str, Any], field_name: str) -> str:
    field_value = message_data.get(field_name)

    if not isinstance(field_value, str) or not field_value.strip():
        raise ValueError(f"El campo '{field_name}' debe ser texto no vacío.")

    return field_value


def read_required_port(message_data: dict[str, Any], field_name: str) -> int:
    field_value = message_data.get(field_name)

    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise ValueError(f"El campo '{field_name}' debe ser un puerto entero.")

    if field_value < 1 or field_value > 65535:
        raise ValueError(
            f"El campo '{field_name}' debe estar entre 1 y 65535."
        )

    return field_value


def read_required_cost(message_data: dict[str, Any], field_name: str) -> int:
    field_value = message_data.get(field_name)

    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise ValueError(f"El campo '{field_name}' debe ser un entero.")

    if field_value <= 0:
        raise ValueError(f"El campo '{field_name}' debe ser mayor que cero.")

    return field_value


def read_required_positive_integer(
    message_data: dict[str, Any],
    field_name: str,
) -> int:
    field_value = message_data.get(field_name)

    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise ValueError(f"El campo '{field_name}' debe ser un entero.")

    if field_value <= 0:
        raise ValueError(f"El campo '{field_name}' debe ser mayor que cero.")

    return field_value
