import json
from dataclasses import dataclass
from typing import Any


DATA_MESSAGE_TYPE = "DATA"

SUPPORTED_BANK_COMMANDS = {
    "START_TRANSACTION",
    "TRANSACTION_READY",
    "CARD",
    "CARD_ACCEPTED",
    "CARD_INVALID",
    "PIN",
    "PIN_ACCEPTED",
    "PIN_INCORRECT",
    "OPTION",
    "BALANCE",
    "REQUEST_AMOUNT",
    "AMOUNT",
    "WITHDRAWAL_SUCCESSFUL",
    "INSUFFICIENT_FUNDS",
    "PROTOCOL_ERROR",
    "LOGOUT",
    "LOGOUT_ACK",
}


@dataclass(frozen=True)
class HostRoute:
    host_id: str
    gateway_id: str


@dataclass(frozen=True)
class NoiseConfiguration:
    bit_flip_probability: float


@dataclass(frozen=True)
class BankPayload:
    command: str
    payload: str


@dataclass(frozen=True)
class DataMessage:
    packet_id: str
    session_id: str
    origin: HostRoute
    destination: HostRoute
    noise: NoiseConfiguration
    payload: BankPayload


def serialize_data_message(data_message: DataMessage) -> str:
    validate_data_message(data_message)

    message_data = {
        "type": DATA_MESSAGE_TYPE,
        "packet_id": data_message.packet_id,
        "session_id": data_message.session_id,
        "origin": {
            "host_id": data_message.origin.host_id,
            "gateway_id": data_message.origin.gateway_id,
        },
        "destination": {
            "host_id": data_message.destination.host_id,
            "gateway_id": data_message.destination.gateway_id,
        },
        "noise": {
            "bit_flip_probability": data_message.noise.bit_flip_probability,
        },
        "payload": {
            "command": data_message.payload.command,
            "payload": data_message.payload.payload,
        },
    }
    return json.dumps(message_data, ensure_ascii=False, separators=(",", ":"))


def parse_data_message(serialized_message: str) -> DataMessage:
    try:
        message_data = json.loads(serialized_message)
    except json.JSONDecodeError as exception:
        raise ValueError("El mensaje DATA no contiene JSON válido.") from exception

    ensure_json_object(message_data, "DATA")

    if message_data.get("type") != DATA_MESSAGE_TYPE:
        raise ValueError("El campo 'type' debe ser 'DATA'.")

    origin_data = read_required_object(message_data, "origin")
    destination_data = read_required_object(message_data, "destination")
    noise_data = read_required_object(message_data, "noise")
    payload_data = read_required_object(message_data, "payload")

    data_message = DataMessage(
        packet_id=read_required_text(message_data, "packet_id"),
        session_id=read_required_text(message_data, "session_id"),
        origin=HostRoute(
            host_id=read_required_text(origin_data, "host_id"),
            gateway_id=read_required_text(origin_data, "gateway_id"),
        ),
        destination=HostRoute(
            host_id=read_required_text(
                destination_data,
                "host_id",
            ),
            gateway_id=read_required_text(
                destination_data,
                "gateway_id",
            ),
        ),
        noise=NoiseConfiguration(
            bit_flip_probability=read_bit_flip_probability(noise_data)
        ),
        payload=BankPayload(
            command=read_bank_command(payload_data),
            payload=read_text(payload_data, "payload"),
        ),
    )
    validate_data_message(data_message)
    return data_message


def validate_data_message(data_message: DataMessage) -> None:
    read_non_empty_text(data_message.packet_id, "packet_id")
    read_non_empty_text(data_message.session_id, "session_id")
    read_non_empty_text(data_message.origin.host_id, "origin.host_id")
    read_non_empty_text(data_message.origin.gateway_id, "origin.gateway_id")
    read_non_empty_text(data_message.destination.host_id, "destination.host_id")
    read_non_empty_text(data_message.destination.gateway_id, "destination.gateway_id")
    validate_bit_flip_probability(data_message.noise.bit_flip_probability)

    if data_message.payload.command not in SUPPORTED_BANK_COMMANDS:
        raise ValueError(
            "El comando bancario no es reconocido: "
            f"{data_message.payload.command}."
        )

    if not isinstance(data_message.payload.payload, str):
        raise ValueError("El campo 'payload.payload' debe ser texto.")


def read_required_object(
    message_data: dict[str, Any],
    field_name: str,
) -> dict[str, Any]:
    field_value = message_data.get(field_name)
    ensure_json_object(field_value, field_name)
    return field_value


def read_required_text(
    message_data: dict[str, Any],
    field_name: str,
) -> str:
    return read_non_empty_text(message_data.get(field_name), field_name)


def read_text(message_data: dict[str, Any], field_name: str) -> str:
    field_value = message_data.get(field_name)

    if not isinstance(field_value, str):
        raise ValueError(f"El campo '{field_name}' debe ser texto.")

    return field_value


def read_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El campo '{field_name}' debe ser texto no vacío.")

    return value


def read_bit_flip_probability(noise_data: dict[str, Any]) -> float:
    probability = noise_data.get("bit_flip_probability")
    validate_bit_flip_probability(probability)
    return float(probability)


def validate_bit_flip_probability(probability: Any) -> None:
    if isinstance(probability, bool) or not isinstance(probability, (int, float)):
        raise ValueError(
            "El campo 'noise.bit_flip_probability' debe ser un número."
        )

    if probability < 0 or probability > 1:
        raise ValueError(
            "El campo 'noise.bit_flip_probability' debe estar entre 0.0 y 1.0."
        )


def read_bank_command(payload_data: dict[str, Any]) -> str:
    command = read_required_text(payload_data, "command")

    if command not in SUPPORTED_BANK_COMMANDS:
        raise ValueError(f"El comando bancario no es reconocido: {command}.")

    return command


def ensure_json_object(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"El campo '{field_name}' debe ser un objeto JSON.")
